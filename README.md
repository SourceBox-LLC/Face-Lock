# Face Lock Server

## Overview

Face Lock Server is a comprehensive facial recognition authentication system built with FastAPI and AWS Rekognition. It enables developers to create applications with facial recognition-based security, running locally on a user's machine while leveraging the powerful cloud-based recognition capabilities of AWS Rekognition.

This server acts as a local security provider that authenticates users via their face and then issues JWT tokens that can be used to secure other applications and services. Think of it as "Face ID for your custom applications".

## Key Features

### Core Functionality
- **Facial Registration**: Securely register user faces in AWS Rekognition collections
- **Facial Verification**: Authenticate users by comparing captured faces against registered templates
- **JWT Token Authentication**: Issue secure tokens upon successful facial verification
- **Comprehensive User Management**: Register, verify, list, and delete users

### Technical Highlights
- **Secure Authentication Flow**: Complete end-to-end authentication system
- **AWS Rekognition Integration**: Leverages AWS's advanced facial recognition capabilities
- **Local Reference Storage**: Maintains local copies of registered faces
- **Dependency Injection**: Well-structured code with clear separation of concerns
- **Comprehensive Error Handling**: Robust error management across all endpoints
- **CORS Support**: Ready for cross-origin requests from web applications
- **Interactive Documentation**: Fully documented API with Swagger UI and ReDoc

## Architecture

The Face Lock Server implements a modern, modular architecture:

```
┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐
│   Client Apps     │━━━▶│   Face Lock API   │━━━▶│  AWS Rekognition  │
│                   │◀━━━│    (FastAPI)      │◀━━━│    Collection     │
└───────────────────┘    └───────────────────┘    └───────────────────┘
                               │       ▲
                               ▼       │
                          ┌───────────────────┐
                          │  Local Reference  │
                          │    Storage        │
                          └───────────────────┘
```

- **FastAPI Application**: Core server handling all requests and responses
- **Rekognition Service**: Communication layer with AWS Rekognition
- **JWT Authentication**: Token generation and validation layer
- **Local Storage**: Maintains copies of registered faces

## Prerequisites

- **Python 3.8+**: Required for running the server
- **AWS Account**: With Rekognition service access enabled
- **AWS Credentials**: Access key and secret key with Rekognition permissions
- **Camera/Image Source**: For capturing facial images (client-side)

## Detailed Setup Guide

### 1. Environment Preparation

#### Clone or Download the Repository

```bash
# If cloning from a repository
git clone https://your-repository-url.git
cd face-lock-server

# If downloaded as a zip file, extract it to a folder of your choice
```

#### Virtual Environment Setup

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 2. Dependency Installation

```bash
# Install required packages
pip install -r requirements.txt

# This will install:
# - FastAPI and Uvicorn for the web server
# - boto3 for AWS integration
# - python-jose and passlib for authentication
# - python-multipart for handling file uploads
# - opencv-python for image processing
# - python-dotenv for environment management
```

### 3. AWS Configuration

#### Create and Configure .env File

Create a `.env` file in the project root based on the provided `.env.example`:

```bash
cp .env.example .env   # On Windows, use 'copy .env.example .env'
```

Edit the `.env` file with your specific details:

```
# AWS Credentials
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1  # Or your preferred AWS region

# Security Settings
SECRET_KEY=your_long_random_string_for_jwt_encryption
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Settings
DEBUG=True  # Set to False in production
```

#### AWS Rekognition Setup

1. Create an AWS account if you don't have one
2. Create an IAM user with programmatic access and attach the `AmazonRekognitionFullAccess` policy
3. Copy the access key ID and secret access key to your `.env` file

### 4. Starting the Server

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`. The `--reload` flag enables automatic reloading during development.

For production environments, remove the `--reload` flag:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

## API Documentation

### Comprehensive API Reference

#### Authentication Endpoints

| Endpoint | Method | Description | Authentication Required |
|----------|--------|-------------|-------------------------|
| `/register/` | POST | Register a new user with facial data | No |
| `/verify/` | POST | Verify a face and get an authentication token | No |
| `/token` | POST | Standard OAuth2 endpoint (returns error) | No |

#### User Management Endpoints

| Endpoint | Method | Description | Authentication Required |
|----------|--------|-------------|-------------------------|
| `/users/me/` | GET | Get current user information | Yes |
| `/users/` | GET | List all registered users | Yes |
| `/users/{user_id}/` | DELETE | Delete a user's facial data | Yes |

#### System Endpoints

| Endpoint | Method | Description | Authentication Required |
|----------|--------|-------------|-------------------------|
| `/` | GET | Welcome message | No |
| `/health` | GET | System health check | No |
| `/api-docs` | GET | API documentation information | No |

### Detailed Endpoint Specifications

#### 1. Register User

**Endpoint**: `POST /register/`

**Request Format**:
- Content-Type: `multipart/form-data`

**Parameters**:
- `user_id` (required): A unique identifier for the user (string)
- `full_name` (optional): User's full name (string)
- `email` (optional): User's email address (string)
- `face_image` (required): Image file containing the user's face (file upload)

**Response**:
```json
{
  "success": true,
  "user_id": "user123",
  "face_id": "abcd1234-efgh-5678-ijkl-9012mnop3456",
  "message": "User registered successfully"
}
```

**Error Responses**:
- 400 Bad Request: If no face is detected in the image
- 500 Internal Server Error: If there's an issue with AWS Rekognition

**Notes**:
- The image should clearly show the user's face
- Optimal lighting and positioning improve registration quality

#### 2. Verify Face

**Endpoint**: `POST /verify/`

**Request Format**:
- Content-Type: `multipart/form-data`

**Parameters**:
- `face_image` (required): Image file containing the user's face (file upload)
- `similarity_threshold` (optional): Minimum similarity score (float, default: 90.0)

**Response**:
```json
{
  "success": true,
  "user_id": "user123",
  "similarity": 99.85,
  "message": "Face verified successfully",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses**:
- 400 Bad Request: If no matching face is found
- 500 Internal Server Error: If there's an issue with AWS Rekognition

**Notes**:
- The token should be stored securely and used for subsequent authenticated requests
- Adjusting the similarity threshold can help with verification accuracy

## System Architecture

### File Structure

```
face-lock-server/
├── app.py                 # Main FastAPI application
├── rekognition.py         # AWS Rekognition service integration
├── requirements.txt       # Project dependencies
├── .env                   # Environment variables (create from .env.example)
├── .env.example           # Template for environment variables
├── README.md              # Project documentation
└── reference_faces/       # Directory for storing reference face images
```

### Component Descriptions

#### 1. FastAPI Application (`app.py`)

The core application contains:
- API endpoint definitions
- Request/response models
- Authentication logic
- Error handling
- CORS configuration

#### 2. Rekognition Service (`rekognition.py`)

This component handles:
- Connection to AWS Rekognition
- Face collection management
- Face registration operations
- Face verification operations
- User management

## Integration Guide

### Integrating Face Lock with Your Applications

#### Client-Side Implementation

1. **Capture User's Face**:
   - Use a camera or file upload to capture the user's face
   - Ensure good image quality and proper lighting

2. **Registration Process**:
   - Call the `/register/` endpoint with user details and face image
   - Store the returned user_id for future reference

3. **Authentication Flow**:
   - When requiring authentication, capture the user's face
   - Call the `/verify/` endpoint with the face image
   - Store the JWT token from a successful response
   - Include the token in subsequent requests to your backend

#### Backend Integration

1. **Token Validation**:
   - Implement JWT validation in your backend services
   - Verify tokens issued by Face Lock Server

2. **Protected Resources**:
   - Require valid JWT tokens for accessing protected resources
   - Extract user information from the token payload

### Example Implementation (Python Client)

```python
import requests

def register_user(server_url, user_id, full_name, email, image_path):
    """Register a new user with Face Lock Server"""
    with open(image_path, 'rb') as image_file:
        files = {'face_image': image_file}
        data = {
            'user_id': user_id,
            'full_name': full_name,
            'email': email
        }
        response = requests.post(f"{server_url}/register/", files=files, data=data)
    
    return response.json()

def verify_user(server_url, image_path, similarity_threshold=90.0):
    """Verify a user and get an authentication token"""
    with open(image_path, 'rb') as image_file:
        files = {'face_image': image_file}
        data = {'similarity_threshold': similarity_threshold}
        response = requests.post(f"{server_url}/verify/", files=files, data=data)
    
    return response.json()

def get_user_info(server_url, token):
    """Get authenticated user information"""
    headers = {'Authorization': f"Bearer {token}"}
    response = requests.get(f"{server_url}/users/me/", headers=headers)
    
    return response.json()
```

### Example Implementation (JavaScript Client)

```javascript
async function registerUser(serverUrl, userId, fullName, email, imageFile) {
    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('full_name', fullName);
    formData.append('email', email);
    formData.append('face_image', imageFile);
    
    const response = await fetch(`${serverUrl}/register/`, {
        method: 'POST',
        body: formData
    });
    
    return await response.json();
}

async function verifyUser(serverUrl, imageFile, similarityThreshold = 90.0) {
    const formData = new FormData();
    formData.append('face_image', imageFile);
    formData.append('similarity_threshold', similarityThreshold);
    
    const response = await fetch(`${serverUrl}/verify/`, {
        method: 'POST',
        body: formData
    });
    
    return await response.json();
}

async function getUserInfo(serverUrl, token) {
    const response = await fetch(`${serverUrl}/users/me/`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    return await response.json();
}
```

## Advanced Configuration

### Security Hardening

#### JWT Token Configuration

You can adjust JWT token settings in your `.env` file:

```
SECRET_KEY=your_very_long_and_secure_random_string
ALGORITHM=HS256  # Or other supported algorithms
ACCESS_TOKEN_EXPIRE_MINUTES=30  # Adjust token lifetime
```

#### CORS Configuration

For production, restrict CORS to specific origins by modifying `app.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Specify allowed origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],  # Restrict to needed methods
    allow_headers=["Authorization", "Content-Type"],
)
```

### AWS Rekognition Customization

#### Collection Management

By default, the system uses a collection named 'FaceLockUsers'. To change this:

1. Modify the `collection_id` in `rekognition.py`
2. Ensure you delete any existing collections with the old name through AWS Console

#### Face Match Parameters

Adjust face matching parameters in the `verify_face` method in `rekognition.py`:

```python
default_similarity_threshold = 90.0  # Adjust default threshold
max_faces = 5  # Adjust maximum number of matches returned
```

## Troubleshooting Guide

### Common Issues

#### Failed Face Registration

**Symptoms**: User registration returns "No face detected in the image"

**Solutions**:
- Ensure the image clearly shows the user's face
- Check lighting conditions - avoid backlighting
- Ensure face is not partially covered or obscured
- Try a different image with better quality

#### Failed Face Verification

**Symptoms**: Verification returns "No matching face found"

**Solutions**:
- Try lowering the similarity threshold (e.g., 85.0 instead of 90.0)
- Ensure consistent lighting and positioning between registration and verification
- Check if the user is registered by listing all users
- Re-register the user with a clearer image

#### AWS Connectivity Issues

**Symptoms**: Operations fail with AWS-related errors

**Solutions**:
- Verify AWS credentials in the `.env` file
- Check AWS region setting
- Ensure the IAM user has proper Rekognition permissions
- Check AWS service status for Rekognition

### Logging

The application uses Python's logging system. To view more detailed logs:

1. Check console output when running the server
2. Adjust logging level in `app.py` and `rekognition.py` for more detailed logs:

```python
logging.basicConfig(level=logging.DEBUG)  # Change from INFO to DEBUG
```

## Performance Considerations

### Optimization Tips

1. **Image Size and Quality**:
   - Use optimized images (1-2 MB maximum)
   - 1024×768 pixels is typically sufficient for recognition
   - Higher resolution doesn't necessarily improve accuracy

2. **AWS Costs and Limits**:
   - Be aware of AWS Rekognition pricing
   - Consider implementing rate limiting for public-facing applications
   - Monitor AWS usage to avoid unexpected charges

3. **Server Resources**:
   - For high-traffic deployments, consider deploying behind a load balancer
   - Optimize the number of worker processes in Uvicorn for your hardware

## Security Best Practices

### Data Protection

1. **AWS Credentials**:
   - Never expose AWS credentials in code or repositories
   - Rotate AWS credentials periodically
   - Use IAM roles with minimal required permissions

2. **Facial Data**:
   - Inform users about facial data collection and storage
   - Consider implementing data deletion policies
   - Only store the minimum required data

3. **Token Security**:
   - Store tokens securely (e.g., in HttpOnly cookies)
   - Implement token refresh mechanisms for long sessions
   - Consider adding token revocation capabilities

## Contributing to the Project

We welcome contributions to Face Lock Server! If you're interested in improving this project:

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add or update tests as necessary
5. Submit a pull request

Please ensure your code follows the existing style and includes appropriate documentation.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - The modern web framework used
- [AWS Rekognition](https://aws.amazon.com/rekognition/) - Powering the facial recognition capabilities
- [Python-Jose](https://python-jose.readthedocs.io/) - JWT token implementation
