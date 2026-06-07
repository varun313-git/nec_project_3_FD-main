"""
Live Detection Module for Face Detection and Gender Recognition System
Performs real-time face detection and person recognition with gender display
"""

import cv2
import sys
import numpy as np
import tensorflow as tf
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import DatabaseManager, FaceDetector, ImageProcessor


class LiveFaceRecognizer:
    """Performs live face recognition"""
    
    # Confidence threshold for recognition (0-100%)
    CONFIDENCE_THRESHOLD = 70
    # Minimum gap between the best and second-best prediction to trust the label
    MARGIN_THRESHOLD = 0.15
    # Minimum cosine similarity for centroid-based verification
    CENTROID_SIM_THRESHOLD = 0.65
    
    def __init__(self):
        """Initialize live recognizer"""
        self.model = None
        self.feature_model = None
        self.label_map = None
        self.centroids = None
        self.database = None
        self.face_detector = FaceDetector()
        self.cap = None
    
    def load_model_and_data(self):
        """Load trained model and data"""
        print("\n" + "="*70)
        print("LOADING MODEL AND DATA")
        print("="*70)
        
        # Check if model exists
        model_path = 'models/face_model.h5'
        label_map_path = 'models/label_map.npy'
        
        if not Path(model_path).exists():
            print(f"❌ Model not found at {model_path}")
            print("Please run training/train_model.py first!")
            return False
        
        if not Path(label_map_path).exists():
            print(f"❌ Label map not found at {label_map_path}")
            return False
        
        try:
            # Load model
            self.model = tf.keras.models.load_model(model_path)
            print(f"✓ Model loaded from: {model_path}")

            # Build feature extractor from the penultimate dense layer
            self.feature_model = tf.keras.Model(
                inputs=self.model.input,
                outputs=self.model.layers[-3].output
            )
            
            # Load label map
            self.label_map = np.load(label_map_path, allow_pickle=True).item()
            print(f"✓ Label map loaded: {len(self.label_map)} classes")

            centroid_path = 'models/class_centroids.npy'
            if Path(centroid_path).exists():
                self.centroids = np.load(centroid_path, allow_pickle=True).item()
                print(f"✓ Class centroids loaded: {len(self.centroids)} classes")
            else:
                self.centroids = None
                print("⚠ Class centroids not found. Using softmax only.")
            
            # Load database
            self.database = DatabaseManager.load_database()
            print(f"✓ Database loaded: {len(self.database)} registered users")
            
            print("="*70 + "\n")
            return True
        
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            return False
    
    def open_webcam(self):
        """Open webcam"""
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            print("❌ Error: Cannot open webcam!")
            return False
        
        # Set webcam properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        return True
    
    def preprocess_face(self, face_roi):
        """Preprocess face for model prediction"""
        try:
            face = ImageProcessor.preprocess_face_image(face_roi)
            if face is None:
                return None

            return np.expand_dims(face, axis=0)
        except:
            return None
    
    def predict_person(self, face_roi):
        """
        Predict person from face
        
        Returns:
            (person_name, confidence_score)
        """
        # Preprocess face
        face = self.preprocess_face(face_roi)
        
        if face is None:
            return 'Unknown', 0
        
        try:
            # Make prediction
            predictions = self.model.predict(face, verbose=0)
            
            # Get the class with highest probability
            predicted_class = np.argmax(predictions[0])
            confidence = np.max(predictions[0]) * 100
            sorted_scores = np.sort(predictions[0])
            second_best = sorted_scores[-2] if len(sorted_scores) > 1 else 0
            
            # Get person name from label map
            person_name = self.label_map.get(predicted_class, 'Unknown')

            # Use centroid verification when available
            if self.centroids is not None and self.feature_model is not None:
                embedding = self.feature_model.predict(face, verbose=0)[0]
                embedding = embedding / (np.linalg.norm(embedding) + 1e-8)

                best_class = None
                best_similarity = -1.0
                second_similarity = -1.0

                for class_id, centroid in self.centroids.items():
                    centroid_vector = np.asarray(centroid)
                    centroid_vector = centroid_vector / (np.linalg.norm(centroid_vector) + 1e-8)
                    similarity = float(np.dot(embedding, centroid_vector))

                    if similarity > best_similarity:
                        second_similarity = best_similarity
                        best_similarity = similarity
                        best_class = int(class_id)
                    elif similarity > second_similarity:
                        second_similarity = similarity

                centroid_name = self.label_map.get(best_class, 'Unknown')
                if best_similarity >= self.CENTROID_SIM_THRESHOLD:
                    if best_class == predicted_class:
                        return centroid_name, confidence

                    # If the embedding strongly agrees with a different person, prefer it
                    if best_similarity - max(second_similarity, -1.0) >= 0.05:
                        centroid_confidence = ((best_similarity + 1.0) / 2.0) * 100
                        return centroid_name, max(confidence, centroid_confidence)
            
            # Reject uncertain predictions even if they are the top class
            if (confidence / 100.0) - second_best < self.MARGIN_THRESHOLD:
                return 'Unknown', confidence
            
            return person_name, confidence
        
        except Exception as e:
            print(f"Error during prediction: {str(e)}")
            return 'Unknown', 0
    
    def get_person_info(self, person_name, confidence):
        """Get person information based on confidence threshold"""
        if confidence < self.CONFIDENCE_THRESHOLD:
            return 'Unknown', 'Unknown'
        
        if person_name in self.database:
            gender = self.database[person_name].get('gender', 'Unknown')
            return person_name, gender
        
        return 'Unknown', 'Unknown'
    
    def run_live_detection(self):
        """Run live face detection and recognition"""
        try:
            print("="*70)
            print("LIVE FACE DETECTION AND RECOGNITION")
            print("="*70)
            print(f"Confidence Threshold: {self.CONFIDENCE_THRESHOLD}%")
            print("Press 'Q' to quit")
            print("="*70 + "\n")
            
            if not self.open_webcam():
                return False
            
            while True:
                ret, frame = self.cap.read()
                
                if not ret:
                    print("Error reading frame!")
                    break
                
                # Flip frame for selfie view
                frame = cv2.flip(frame, 1)
                
                # Detect faces
                faces = self.face_detector.detect_faces(frame)
                
                # Process each detected face
                for (x, y, w, h) in faces:
                    # Extract face region
                    face_roi = frame[y:y+h, x:x+w]
                    if face_roi.size == 0:
                        continue
                    
                    # Predict person
                    predicted_name, confidence = self.predict_person(face_roi)
                    
                    # Get person info
                    display_name, display_gender = self.get_person_info(
                        predicted_name, confidence
                    )
                    
                    # Prepare label
                    if display_name == 'Unknown':
                        label = f"{display_name} ({confidence:.1f}%)"
                        color = (0, 0, 255)  # Red for unknown
                    else:
                        label = f"{display_name} | {display_gender}"
                        color = (0, 255, 0)  # Green for known
                    
                    # Draw on frame
                    frame = self.face_detector.draw_face_box_with_label(
                        frame, x, y, w, h, label, color
                    )
                
                # Display frame
                cv2.imshow("Live Face Recognition", frame)
                
                # Check for quit
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == ord('Q'):
                    print("\nLive detection stopped!")
                    break
            
            cv2.destroyAllWindows()
            return True
        
        except Exception as e:
            print(f"Error during live detection: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            if self.cap:
                self.cap.release()
            cv2.destroyAllWindows()
    
    def run(self):
        """Main method to run live detection"""
        if not self.load_model_and_data():
            return False
        
        return self.run_live_detection()


def main():
    """Main function for detection module"""
    recognizer = LiveFaceRecognizer()
    success = recognizer.run()
    
    if success:
        print("\n" + "="*70)
        print("Live detection completed successfully!")
        print("="*70 + "\n")


if __name__ == "__main__":
    main()
