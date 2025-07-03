# src/face_processor.py
"""
Face extraction and verification module for passport/ID verification
Using InsightFace for better accuracy and performance
"""

import cv2
import numpy as np
from insightface.app import FaceAnalysis
from insightface.data import get_image as ins_get_image
import face_recognition
from typing import Dict, Tuple, Optional, List, Union
import logging
from dataclasses import dataclass
import json
import base64
from io import BytesIO
from PIL import Image
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FaceVerificationResult:
    """Data class for face verification results"""
    verified: bool
    confidence: float
    face_locations: Dict[str, List[int]]
    face_embeddings: Dict[str, Optional[List[float]]]  # Changed from np.ndarray to List[float] for JSON serialization
    verification_method: str
    error: Optional[str] = None
    liveness_score: Optional[float] = None
    
    def __post_init__(self):
        """Ensure all values are native Python types for JSON serialization"""
        self.verified = bool(self.verified)
        self.confidence = float(self.confidence)
        if self.liveness_score is not None:
            self.liveness_score = float(self.liveness_score)
    
class FaceProcessor:
    """Advanced face processing for passport/ID verification using InsightFace"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize face processor with configuration
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or self._default_config()
        
        # Initialize InsightFace
        self.face_app = FaceAnalysis(
            name='buffalo_l',  # Using buffalo_l model for best accuracy
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
        )
        self.face_app.prepare(ctx_id=0, det_size=(640, 640))
        
        # Fallback face cascade for document face extraction
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        logger.info("FaceProcessor initialized with InsightFace")
        
    def _default_config(self) -> Dict:
        """Default configuration for face processing"""
        return {
            "verification": {
                "threshold": 0.4,  # InsightFace uses cosine similarity, lower is better
                "model": "buffalo_l",  # InsightFace model
                "distance_metric": "cosine",
                "enforce_detection": True,
                "min_face_size": 30
            },
            "extraction": {
                "min_face_size": (30, 30),
                "scale_factor": 1.1,
                "min_neighbors": 5,
                "padding": 20,  # Padding around detected face
                "target_size": (112, 112)  # InsightFace input size
            },
            "liveness": {
                "enabled": True,
                "min_score": 0.7
            },
            "quality": {
                "min_face_quality": 0.5,
                "min_detection_confidence": 0.8
            }
        }
    
    def extract_face_from_document(self, document_image: np.ndarray, 
                                  document_type: str = "passport") -> Tuple[Optional[np.ndarray], Optional[Dict]]:
        """
        Extract face from passport or ID card with metadata
        
        Args:
            document_image: Document image as numpy array
            document_type: Type of document (passport/id_card)
            
        Returns:
            Tuple of (extracted face image, face metadata)
        """
        try:
            # Define face region based on document type
            h, w = document_image.shape[:2]
            
            if document_type == "passport":
                # Face is typically on the left side of passport
                roi_coords = (int(w*0.05), int(h*0.3), int(w*0.35), int(h*0.8))
            else:  # ID card
                # Face position varies more in ID cards
                roi_coords = (int(w*0.05), int(h*0.2), int(w*0.45), int(h*0.8))
            
            x1, y1, x2, y2 = roi_coords
            roi = document_image[y1:y2, x1:x2]
            
            # Try InsightFace first
            faces = self.face_app.get(roi)
            
            if faces:
                # Get the face with highest detection score
                best_face = max(faces, key=lambda f: f.det_score)
                
                # Extract face region
                bbox = best_face.bbox.astype(int)
                x, y, x2, y2 = bbox
                
                # Add padding
                padding = self.config["extraction"]["padding"]
                x = max(0, x - padding)
                y = max(0, y - padding)
                x2 = min(roi.shape[1], x2 + padding)
                y2 = min(roi.shape[0], y2 + padding)
                
                face_img = roi[y:y2, x:x2]
                
                # Get face metadata
                metadata = {
                    "bbox": bbox.tolist(),
                    "det_score": float(best_face.det_score),
                    "embedding": best_face.embedding.tolist() if best_face.embedding is not None else None,
                    "landmark": best_face.kps.tolist() if best_face.kps is not None else None,
                    "age": int(best_face.age) if hasattr(best_face, 'age') and best_face.age is not None else None,
                    "gender": int(best_face.gender) if hasattr(best_face, 'gender') and best_face.gender is not None else None
                }
                
                return self._enhance_face(face_img), metadata
            
            # Fallback to cascade classifier if InsightFace fails
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=self.config["extraction"]["scale_factor"],
                minNeighbors=self.config["extraction"]["min_neighbors"],
                minSize=self.config["extraction"]["min_face_size"]
            )
            
            if len(faces) > 0:
                # Get the largest face
                largest_face = max(faces, key=lambda f: f[2] * f[3])
                x, y, w, h = largest_face
                
                # Add padding
                padding = self.config["extraction"]["padding"]
                x = max(0, x - padding)
                y = max(0, y - padding)
                w = min(roi.shape[1] - x, w + 2 * padding)
                h = min(roi.shape[0] - y, h + 2 * padding)
                
                face_img = roi[y:y+h, x:x+w]
                
                metadata = {
                    "bbox": [x, y, x+w, y+h],
                    "det_score": 0.8,  # Default score for cascade
                    "embedding": None,
                    "method": "cascade"
                }
                
                return self._enhance_face(face_img), metadata
            
            logger.warning("No face detected in document")
            return None, None
            
        except Exception as e:
            logger.error(f"Error extracting face from document: {str(e)}")
            return None, None
    
    def _enhance_face(self, face_image: np.ndarray) -> np.ndarray:
        """
        Enhance face image for better verification
        
        Args:
            face_image: Face image to enhance
            
        Returns:
            Enhanced face image
        """
        try:
            # Apply CLAHE for contrast enhancement
            lab = cv2.cvtColor(face_image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            
            # Denoise
            enhanced = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)
            
            # Resize to target size for InsightFace
            target_size = self.config["extraction"]["target_size"]
            enhanced = cv2.resize(enhanced, target_size, interpolation=cv2.INTER_CUBIC)
            
            return enhanced
        except Exception as e:
            logger.error(f"Error enhancing face: {str(e)}")
            return face_image
    
    def extract_embedding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract face embedding using InsightFace
        
        Args:
            face_image: Face image
            
        Returns:
            Face embedding vector or None
        """
        try:
            faces = self.face_app.get(face_image)
            if faces:
                # Return embedding of the first (best) face
                return faces[0].embedding
            return None
        except Exception as e:
            logger.error(f"Error extracting embedding: {str(e)}")
            return None
    
    def verify_faces(self, id_face: np.ndarray, selfie_face: np.ndarray, 
                    id_metadata: Optional[Dict] = None) -> FaceVerificationResult:
        """
        Verify if two face images belong to the same person using InsightFace
        
        Args:
            id_face: Face from ID document
            selfie_face: Selfie face image
            id_metadata: Metadata from ID face extraction
            
        Returns:
            FaceVerificationResult object
        """
        try:
            # Get embeddings
            if id_metadata and id_metadata.get('embedding') is not None:
                id_embedding = id_metadata['embedding']
            else:
                id_embedding = self.extract_embedding(id_face)
            
            selfie_faces = self.face_app.get(selfie_face)
            
            if id_embedding is None or not selfie_faces:
                raise ValueError("Could not extract face embeddings")
            
            # Get selfie embedding (use the first/best face)
            selfie_embedding = selfie_faces[0].embedding
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(id_embedding, selfie_embedding)
            
            # Determine if verified (for cosine similarity, higher is better)
            verified = similarity >= (1 - self.config["verification"]["threshold"])
            
            # Get face locations
            face_locations = {
                "id_face": id_metadata.get('bbox', []) if id_metadata else [],
                "selfie_face": selfie_faces[0].bbox.astype(int).tolist() if selfie_faces else []
            }
            
            # Store embeddings for potential future use (convert to lists for JSON serialization)
            face_embeddings = {
                "id_face": id_embedding.tolist() if id_embedding is not None else None,
                "selfie_face": selfie_embedding.tolist() if selfie_embedding is not None else None
            }
            
            return FaceVerificationResult(
                verified=verified,
                confidence=float(similarity),
                face_locations=face_locations,
                face_embeddings=face_embeddings,
                verification_method="insightface"
            )
            
        except Exception as e:
            logger.error(f"InsightFace verification failed: {str(e)}")
            
            # Fallback to face_recognition library
            try:
                return self._verify_with_face_recognition(id_face, selfie_face)
            except Exception as e2:
                logger.error(f"Fallback verification failed: {str(e2)}")
                return FaceVerificationResult(
                    verified=False,
                    confidence=0.0,
                    face_locations={},
                    face_embeddings={},
                    verification_method="failed",
                    error=str(e2)
                )
    
    def _cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings"""
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        return dot_product / (norm1 * norm2)
    
    def _verify_with_face_recognition(self, id_face: np.ndarray, 
                                     selfie_face: np.ndarray) -> FaceVerificationResult:
        """
        Fallback verification using face_recognition library
        
        Args:
            id_face: Face from ID document
            selfie_face: Selfie face image
            
        Returns:
            FaceVerificationResult object
        """
        # Get face encodings
        id_encodings = face_recognition.face_encodings(id_face)
        selfie_encodings = face_recognition.face_encodings(selfie_face)
        
        if not id_encodings or not selfie_encodings:
            raise ValueError("Could not find face in one or both images")
        
        # Compare faces
        distances = face_recognition.face_distance(id_encodings, selfie_encodings[0])
        min_distance = min(distances)
        
        # Convert distance to confidence
        confidence = 1 - min_distance
        verified = confidence >= self.config["verification"]["threshold"]
        
        # Get face locations
        id_locations = face_recognition.face_locations(id_face)
        selfie_locations = face_recognition.face_locations(selfie_face)
        
        return FaceVerificationResult(
            verified=verified,
            confidence=confidence,
            face_locations={
                "id_face": id_locations[0] if id_locations else [],
                "selfie_face": selfie_locations[0] if selfie_locations else []
            },
            face_embeddings={
                "id_face": id_encodings[0].tolist() if id_encodings else None,
                "selfie_face": selfie_encodings[0].tolist() if selfie_encodings else None
            },
            verification_method="face_recognition"
        )
    
    def check_liveness(self, face_image: np.ndarray) -> float:
        """
        Check if the face is from a live person (anti-spoofing)
        
        Args:
            face_image: Face image to check
            
        Returns:
            Liveness score (0-1)
        """
        # Enhanced liveness check with multiple indicators
        scores = []
        
        # 1. Image quality check (blurriness)
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_score = min(laplacian_var / 1000, 1.0)
        scores.append(blur_score)
        
        # 2. Color distribution analysis
        hsv = cv2.cvtColor(face_image, cv2.COLOR_BGR2HSV)
        saturation_mean = np.mean(hsv[:, :, 1])
        saturation_std = np.std(hsv[:, :, 1])
        color_score = min((saturation_mean * saturation_std) / 5000, 1.0)
        scores.append(color_score)
        
        # 3. Texture analysis (detect print patterns)
        # Calculate Local Binary Patterns for texture
        texture_score = self._analyze_texture(gray)
        scores.append(texture_score)
        
        # 4. Face quality from InsightFace
        faces = self.face_app.get(face_image)
        if faces and faces[0].det_score:
            quality_score = float(faces[0].det_score)
            scores.append(quality_score)
        
        # Weighted average
        weights = [0.25, 0.25, 0.3, 0.2]
        liveness_score = sum(s * w for s, w in zip(scores, weights[:len(scores)]))
        
        return liveness_score
    
    def _analyze_texture(self, gray_image: np.ndarray) -> float:
        """Analyze texture patterns for liveness detection"""
        # Simple texture analysis using variance of Laplacian
        # Real faces have more complex textures than printed ones
        edges = cv2.Canny(gray_image, 50, 150)
        texture_complexity = np.mean(edges) / 255.0
        return min(texture_complexity * 10, 1.0)
    
    def process_verification_request(self, document_image: Union[str, np.ndarray], 
                                   selfie_image: Union[str, np.ndarray],
                                   document_type: str = "passport") -> Dict:
        """
        Complete verification pipeline
        
        Args:
            document_image: Path to document image or numpy array
            selfie_image: Path to selfie image or numpy array
            document_type: Type of document
            
        Returns:
            Complete verification results
        """
        results = {
            "success": False,
            "verification": None,
            "document_face": None,
            "errors": []
        }
        
        try:
            # Load images if paths provided
            if isinstance(document_image, str):
                document_img = cv2.imread(document_image)
            else:
                document_img = document_image
                
            if isinstance(selfie_image, str):
                selfie_img = cv2.imread(selfie_image)
            else:
                selfie_img = selfie_image
            
            if document_img is None or selfie_img is None:
                results["errors"].append("Failed to load one or more images")
                return results
            
            # Extract face from document
            id_face, id_metadata = self.extract_face_from_document(document_img, document_type)
            if id_face is None:
                results["errors"].append("Could not extract face from document")
                return results
            
            # Store extracted face for response
            results["document_face"] = encode_image_to_base64(id_face)
            
            # Verify faces
            verification = self.verify_faces(id_face, selfie_img, id_metadata)
            
            # Check liveness if enabled
            if self.config["liveness"]["enabled"]:
                liveness_score = self.check_liveness(selfie_img)
                verification.liveness_score = liveness_score
                
                if liveness_score < self.config["liveness"]["min_score"]:
                    verification.verified = False
                    results["errors"].append(f"Liveness check failed (score: {liveness_score:.2f})")
            
            results["success"] = True
            results["verification"] = {
                "verified": verification.verified,
                "confidence": float(verification.confidence),
                "method": verification.verification_method,
                "liveness_score": float(verification.liveness_score) if verification.liveness_score else None,
                "face_locations": verification.face_locations,
                "thresholds": {
                    "verification": self.config["verification"]["threshold"],
                    "liveness": self.config["liveness"]["min_score"]
                }
            }
            
            # Add face quality metrics
            if id_metadata:
                results["verification"]["document_face_quality"] = {
                    "detection_score": id_metadata.get("det_score", 0),
                    "age": id_metadata.get("age"),
                    "gender": id_metadata.get("gender")
                }
            
        except Exception as e:
            results["errors"].append(str(e))
            logger.error(f"Verification request failed: {str(e)}")
        
        return results

# Utility functions for integration

def create_face_processor(config_path: Optional[str] = None) -> FaceProcessor:
    """
    Factory function to create FaceProcessor instance
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        FaceProcessor instance
    """
    config = None
    if config_path:
        with open(config_path, 'r') as f:
            config = json.load(f).get('face_processing', {})
    
    return FaceProcessor(config)

def encode_image_to_base64(image: np.ndarray) -> str:
    """Convert numpy image to base64 string"""
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')

def decode_base64_to_image(base64_string: str) -> np.ndarray:
    """Convert base64 string to numpy image"""
    if base64_string.startswith('data:image'):
        base64_string = base64_string.split(',')[1]
    img_data = base64.b64decode(base64_string)
    nparr = np.frombuffer(img_data, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)