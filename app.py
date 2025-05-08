# ---------------------------------------------------------------------------- #
#                        Face Lock Server - Main Application                    #
# ---------------------------------------------------------------------------- #

# Standard library imports
import os
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import uuid4
import logging

# Third-party imports
import cv2
import numpy as np
from fastapi import FastAPI, Depends, HTTPException, status, Request, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from dotenv import load_dotenv

# Local imports
from rekognition import RekognitionService

# ---------------------------------------------------------------------------- #
#                        Configuration and Initialization                       #
# ---------------------------------------------------------------------------- #

# Load environment variables from .env file
load_dotenv()

# Configure logging with appropriate level
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("facial-auth")

# Initialize the AWS Rekognition service that handles facial recognition
rekognition_service = RekognitionService()

# Security configuration for JWT token generation and validation
# These values should be set in the .env file for security
SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")  # Used to sign JWT tokens
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # JWT encryption algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))  # Token validity period

# Password hashing context - used for potential future username/password authentication
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 password bearer scheme - defines how tokens are extracted from requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ---------------------------------------------------------------------------- #
#                          Pydantic Data Models                                #
# ---------------------------------------------------------------------------- #

# JWT Token response model - returned after successful authentication
class Token(BaseModel):
    access_token: str      # The JWT token string
    token_type: str        # Token type (usually "bearer")

# Token payload model - contains data encoded in the JWT token
class TokenData(BaseModel):
    user_id: Optional[str] = None  # Unique identifier for the authenticated user

# Basic user information model
class User(BaseModel):
    user_id: str                   # Unique identifier for the user
    email: Optional[str] = None    # User's email (optional)
    full_name: Optional[str] = None  # User's full name (optional)

# Extended user model that includes face ID from AWS Rekognition
class UserInDB(User):
    face_id: Optional[str] = None  # AWS Rekognition face ID

# Model for user creation requests
class UserCreate(BaseModel):
    user_id: str                   # Required unique identifier
    email: Optional[str] = None    # Optional email address 
    full_name: Optional[str] = None  # Optional full name

# Response model for face verification endpoints
class FaceVerificationResponse(BaseModel):
    success: bool                    # Whether verification was successful
    message: Optional[str] = None    # Additional information or error message
    user_id: Optional[str] = None    # ID of the verified user (if successful)
    similarity: Optional[float] = None  # Similarity score between 0-100
    token: Optional[str] = None      # JWT token (if successful)

# Response model for face registration endpoints 
class FaceRegistrationResponse(BaseModel):
    success: bool                    # Whether registration was successful
    message: Optional[str] = None    # Additional information or error message
    user_id: Optional[str] = None    # ID of the registered user
    face_id: Optional[str] = None    # AWS Rekognition face ID (if successful)

# ---------------------------------------------------------------------------- #
#                FastAPI Application Initialization and Configuration            #
# ---------------------------------------------------------------------------- #

# Initialize the FastAPI application with metadata
app = FastAPI(
    title="Face Lock Server",
    description="A facial recognition security server using AWS Rekognition",
    version="1.0.0"
)

# Configure Cross-Origin Resource Sharing (CORS) middleware
# This allows the API to be called from web browsers on other domains
app.add_middleware(
    CORSMiddleware,
    # WARNING: In production, replace "*" with specific allowed origins for security
    allow_origins=["*"],  
    # Allow cookies and authentication headers to be included in cross-origin requests
    allow_credentials=True,
    # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_methods=["*"],
    # Allow all request headers
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------- #
#                    Authentication Helper Functions                           #
# ---------------------------------------------------------------------------- #

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Creates a JWT access token for user authentication.
    
    Args:
        data (dict): Payload data to encode in the token, typically contains user ID
        expires_delta (Optional[timedelta]): Custom expiration time, defaults to ACCESS_TOKEN_EXPIRE_MINUTES
    
    Returns:
        str: The encoded JWT token string
    """
    # Create a copy of the data to avoid modifying the original
    to_encode = data.copy()
    
    # Set the expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    # Add expiration time to the payload
    to_encode.update({"exp": expire})
    
    # Encode and return the JWT token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    FastAPI dependency that extracts and validates the user from a JWT token.
    This function is used to protect endpoints that require authentication.
    
    Args:
        token (str): JWT token extracted from the Authorization header
        
    Returns:
        User: The authenticated user object
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    # Define the exception to raise if authentication fails
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extract the user ID from the token subject claim
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        # Create token data object
        token_data = TokenData(user_id=user_id)
    except JWTError:
        # If token decoding fails, raise exception
        raise credentials_exception
    
    # In a production app, you'd fetch complete user data from a database here
    # For this implementation, we simply return a User object with the ID
    return User(user_id=token_data.user_id)

# ---------------------------------------------------------------------------- #
#                       API Endpoints Implementation                           #
# ---------------------------------------------------------------------------- #

# Root endpoint - serves as a simple health check and welcome message
@app.get("/")
async def root():
    """Root endpoint that returns a welcome message and confirms the server is running."""
    return {"message": "Welcome to Face Lock Server"}

# User registration endpoint - registers a new user's face with the system
@app.post("/register/", response_model=FaceRegistrationResponse)
async def register_user(user_id: str = Form(...), 
                       full_name: Optional[str] = Form(None),
                       email: Optional[str] = Form(None),
                       face_image: UploadFile = File(...)):
    """
    Register a new user with facial recognition.
    
    This endpoint takes a user's basic information and a facial image,
    then registers the face with AWS Rekognition for future verification.
    
    Args:
        user_id (str): Unique identifier for the user
        full_name (Optional[str]): User's full name (optional)
        email (Optional[str]): User's email address (optional)
        face_image (UploadFile): Image file containing the user's face
        
    Returns:
        FaceRegistrationResponse: Result of the registration operation
    """
    logger.info(f"Registering user: {user_id}")
    
    # Read and process the uploaded image
    image_content = await face_image.read()
    
    # Register face in AWS Rekognition through our service
    result = rekognition_service.register_face(user_id, image_content)
    
    # Handle registration failure
    if not result["success"]:
        logger.warning(f"Registration failed for user {user_id}: {result['message']}")
        return FaceRegistrationResponse(
            success=False,
            message=result["message"]
        )
    
    # In a production application, you would store additional user details in a database
    # This implementation only stores the face in AWS Rekognition
    logger.info(f"Successfully registered user {user_id} with face ID {result['face_id']}")
    
    # Return successful response with face ID
    return FaceRegistrationResponse(
        success=True,
        user_id=user_id,
        face_id=result["face_id"],
        message="User registered successfully"
    )

# Face verification endpoint - authenticates a user based on their face
@app.post("/verify/", response_model=FaceVerificationResponse)
async def verify_face(face_image: UploadFile = File(...), similarity_threshold: float = Form(90.0)):
    """
    Verify a user's identity using facial recognition.
    
    This endpoint takes a facial image and attempts to match it against
    registered faces. If successful, it returns a JWT token for authentication.
    
    Args:
        face_image (UploadFile): Image file containing the user's face
        similarity_threshold (float): Minimum similarity score (0-100) to consider a match
        
    Returns:
        FaceVerificationResponse: Result of the verification with token if successful
    """
    logger.info(f"Verifying face with similarity threshold: {similarity_threshold}")
    
    # Read and process the uploaded image
    image_content = await face_image.read()
    
    # Verify face against registered faces in AWS Rekognition
    result = rekognition_service.verify_face(image_content, similarity_threshold)
    
    # Handle verification failure
    if not result["success"]:
        logger.warning(f"Face verification failed: {result['message']}")
        return FaceVerificationResponse(
            success=False,
            message=result["message"]
        )
    
    # Generate JWT token for the verified user with appropriate expiration
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": result["user_id"]},  # 'sub' is the standard JWT claim for subject (user ID)
        expires_delta=access_token_expires
    )
    
    logger.info(f"Successfully verified user {result['user_id']} with similarity {result['similarity']}")
    
    # Return successful response with token
    return FaceVerificationResponse(
        success=True,
        user_id=result["user_id"],
        similarity=result["similarity"],
        message="Face verified successfully",
        token=access_token
    )

# Standard OAuth2 token endpoint - included for compatibility but not used
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token endpoint.
    
    This endpoint is provided for compatibility with standard OAuth2 clients,
    but returns an error directing users to use facial verification instead.
    
    Args:
        form_data: Standard OAuth2 username/password form
        
    Raises:
        HTTPException: Always raised to direct users to the facial verification endpoint
    """
    # This endpoint is provided for compatibility with OAuth2 clients
    # For this facial recognition system, we redirect to the facial verification endpoint
    logger.info("Attempt to use username/password authentication redirected to facial verification")
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="This server uses facial recognition for authentication. Please use /verify/ endpoint."
    )

# Get current user endpoint - returns information about the authenticated user
@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get information about the currently authenticated user.
    
    This endpoint requires authentication via JWT token and returns
    the user's information based on the token.
    
    Args:
        current_user (User): Automatically injected from the JWT token via dependency
        
    Returns:
        User: The authenticated user's information
    """
    logger.info(f"Retrieved user information for {current_user.user_id}")
    return current_user

# Delete user endpoint - removes a user's facial data from the system
@app.delete("/users/{user_id}/")
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    """
    Delete a user's facial data from the system.
    
    This endpoint requires authentication and only allows users to delete
    their own data (security measure).
    
    Args:
        user_id (str): ID of the user to delete
        current_user (User): Automatically injected from the JWT token via dependency
        
    Returns:
        dict: Confirmation message
        
    Raises:
        HTTPException: If unauthorized or if deletion fails
    """
    # Security check: Only allow users to delete their own data
    # In a production app, you might implement admin permissions
    if current_user.user_id != user_id:
        logger.warning(f"User {current_user.user_id} attempted to delete data for user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own user data"
        )
    
    logger.info(f"Deleting user {user_id}")
    result = rekognition_service.delete_user(user_id)
    
    if not result["success"]:
        logger.error(f"Failed to delete user {user_id}: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["message"]
        )
    
    logger.info(f"Successfully deleted user {user_id}")
    return {"message": f"User {user_id} deleted successfully"}

# List users endpoint - returns all registered users
@app.get("/users/")
async def list_users(current_user: User = Depends(get_current_user)):
    """
    List all registered users in the system.
    
    This endpoint requires authentication and returns a list of all users
    registered in the facial recognition system.
    
    Args:
        current_user (User): Automatically injected from the JWT token via dependency
        
    Returns:
        dict: List of registered user IDs
        
    Raises:
        HTTPException: If there's an error retrieving the user list
    """
    # Note: In a production app, this might be restricted to admin users only
    logger.info(f"User {current_user.user_id} requested list of all users")
    result = rekognition_service.list_users()
    
    if not result["success"]:
        logger.error(f"Failed to list users: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )
    
    return result

# ---------------------------------------------------------------------------- #
#                       Utility Endpoints and Error Handling                    #
# ---------------------------------------------------------------------------- #

# API documentation information endpoint
@app.get("/api-docs")
async def get_api_docs():
    """
    Provides links to the API documentation interfaces.
    
    This endpoint returns the URLs for Swagger UI, ReDoc, and OpenAPI schema.
    Useful for developers integrating with the API.
    
    Returns:
        dict: Dictionary containing documentation URLs
    """
    logger.info("API documentation endpoints requested")
    return {
        "docs_url": "/docs",       # Swagger UI documentation URL
        "redoc_url": "/redoc",     # ReDoc documentation URL
        "openapi_url": "/openapi.json"  # OpenAPI schema URL
    }

# Health check endpoint for monitoring and load balancers
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring system status.
    
    This endpoint can be used by monitoring tools, load balancers,
    and container orchestration systems to verify the service is running.
    
    Returns:
        dict: Service health status and version information
    """
    logger.debug("Health check request received")
    return {
        "status": "healthy",  # Service status indicator
        "version": "1.0.0",   # API version for compatibility checking
        "timestamp": datetime.utcnow().isoformat()  # Current timestamp for monitoring
    }

# Global exception handler to catch and standardize error responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions.
    
    This catches any unhandled exceptions in the application and returns
    a standardized error response instead of revealing implementation details.
    All exceptions are logged for debugging and monitoring.
    
    Args:
        request (Request): The request that caused the exception
        exc (Exception): The unhandled exception
        
    Returns:
        JSONResponse: Standardized error response with 500 status code
    """
    # Log the full exception details for debugging
    logger.error(f"Unhandled exception in {request.url.path}: {str(exc)}", exc_info=True)
    
    # Return a generic error message to avoid exposing internal details
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "An unexpected error occurred",
            "request_id": str(uuid4())  # Unique ID for tracking this error in logs
        }
    )