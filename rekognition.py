import boto3
import base64
import os
import cv2
import numpy as np
import uuid
from dotenv import load_dotenv
import logging
from typing import Dict, List, Optional, Tuple, Any

# Load environment variables
load_dotenv()

class RekognitionService:
    def __init__(self):
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("rekognition")
        
        # Initialize AWS clients
        self.rekognition_client = boto3.client(
            'rekognition',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Create a local directory for storing reference faces
        self.faces_dir = os.path.join(os.path.dirname(__file__), 'reference_faces')
        os.makedirs(self.faces_dir, exist_ok=True)
        
        # Collection name for storing face records
        self.collection_id = 'FaceLockUsers'
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self) -> None:
        """Ensure that the face collection exists in AWS Rekognition"""
        try:
            # Check if collection exists
            response = self.rekognition_client.list_collections()
            if self.collection_id not in response.get('CollectionIds', []):
                self.rekognition_client.create_collection(CollectionId=self.collection_id)
                self.logger.info(f"Created collection: {self.collection_id}")
            else:
                self.logger.info(f"Collection {self.collection_id} already exists")
        except Exception as e:
            self.logger.error(f"Error setting up collection: {str(e)}")
            raise
    
    def register_face(self, user_id: str, image_data: bytes) -> Dict[str, Any]:
        """Register a user's face in the Rekognition collection"""
        try:
            # Save reference image locally
            image_id = str(uuid.uuid4())
            image_path = os.path.join(self.faces_dir, f"{user_id}_{image_id}.jpg")
            
            # Convert bytes to numpy array and save as image
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            cv2.imwrite(image_path, img)
            
            # Index face in Rekognition
            response = self.rekognition_client.index_faces(
                CollectionId=self.collection_id,
                Image={'Bytes': image_data},
                ExternalImageId=user_id,
                DetectionAttributes=['ALL']
            )
            
            # Return face details
            face_records = response.get('FaceRecords', [])
            if not face_records:
                return {"success": False, "message": "No face detected in the image"}
            
            face_id = face_records[0]['Face']['FaceId']
            self.logger.info(f"Registered face for user {user_id} with face ID {face_id}")
            
            return {
                "success": True,
                "user_id": user_id,
                "face_id": face_id,
                "confidence": face_records[0]['Face']['Confidence']
            }
            
        except Exception as e:
            self.logger.error(f"Error registering face: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def verify_face(self, image_data: bytes, similarity_threshold: float = 90.0) -> Dict[str, Any]:
        """Verify a face against the registered faces in the collection"""
        try:
            # Search for matching faces
            response = self.rekognition_client.search_faces_by_image(
                CollectionId=self.collection_id,
                Image={'Bytes': image_data},
                MaxFaces=1,
                FaceMatchThreshold=similarity_threshold
            )
            
            # Check if we found any matches
            face_matches = response.get('FaceMatches', [])
            if not face_matches:
                return {"success": False, "message": "No matching face found"}
            
            # Get the best match
            best_match = face_matches[0]
            user_id = best_match['Face']['ExternalImageId']
            
            self.logger.info(f"Verified face for user {user_id} with similarity {best_match['Similarity']}")
            
            return {
                "success": True,
                "user_id": user_id,
                "similarity": best_match['Similarity'],
                "face_id": best_match['Face']['FaceId']
            }
            
        except Exception as e:
            self.logger.error(f"Error verifying face: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Delete a user's face data from the collection"""
        try:
            # List faces to find the face IDs associated with this user
            response = self.rekognition_client.list_faces(CollectionId=self.collection_id)
            
            # Filter faces by external image ID (user_id)
            face_ids = [face['FaceId'] for face in response['Faces'] 
                        if face['ExternalImageId'] == user_id]
            
            if not face_ids:
                return {"success": False, "message": f"No faces found for user {user_id}"}
            
            # Delete faces from collection
            delete_response = self.rekognition_client.delete_faces(
                CollectionId=self.collection_id,
                FaceIds=face_ids
            )
            
            # Delete local reference images
            for filename in os.listdir(self.faces_dir):
                if filename.startswith(f"{user_id}_"):
                    os.remove(os.path.join(self.faces_dir, filename))
            
            self.logger.info(f"Deleted {len(face_ids)} faces for user {user_id}")
            
            return {
                "success": True,
                "user_id": user_id,
                "deleted_face_count": len(face_ids)
            }
            
        except Exception as e:
            self.logger.error(f"Error deleting user: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def list_users(self) -> Dict[str, Any]:
        """List all registered users"""
        try:
            # List faces in the collection
            response = self.rekognition_client.list_faces(CollectionId=self.collection_id)
            
            # Extract unique user IDs
            user_ids = set(face['ExternalImageId'] for face in response['Faces'])
            
            return {
                "success": True,
                "users": list(user_ids),
                "total_count": len(user_ids)
            }
            
        except Exception as e:
            self.logger.error(f"Error listing users: {str(e)}")
            return {"success": False, "message": str(e)}
