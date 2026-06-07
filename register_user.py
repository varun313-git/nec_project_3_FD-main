"""
Registration Module for Face Detection and Gender Recognition System
Allows users to register their name, gender, and capture face images
"""

import cv2
import os
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import FileManager, DatabaseManager, FaceDetector, ImageProcessor


class UserRegistration:
    """Handles user registration process"""
    
    # Number of images to capture per user
    IMAGES_TO_CAPTURE = 50
    
    # Auto-capture interval in seconds (captures one image every 0.3 seconds)
    CAPTURE_INTERVAL = 0.3
    
    def __init__(self):
        """Initialize registration system"""
        FileManager.create_directories()
        self.cap = None
        self.face_detector = FaceDetector()
    
    def get_user_input(self):
        """Get name and gender from user"""
        print("\n" + "="*50)
        print("USER REGISTRATION")
        print("="*50)
        
        while True:
            name = input("\nEnter your name: ").strip()
            if name and len(name) > 0:
                # Remove spaces and special characters for folder name
                folder_name = name.replace(" ", "_")
                if DatabaseManager.user_exists(folder_name):
                    print(f"User '{name}' is already registered!")
                    continue
                break
            else:
                print("Please enter a valid name!")
        
        while True:
            gender = input("Enter your gender (Male/Female/Other): ").strip()
            if gender.lower() in ['male', 'female', 'other']:
                gender = gender.capitalize()
                break
            else:
                print("Please enter valid gender (Male/Female/Other)!")
        
        return name, folder_name, gender
    
    def open_webcam(self):
        """Open webcam for face capture"""
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            print("Error: Cannot open webcam!")
            return False
        
        # Set webcam properties for better quality
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        return True
    
    def capture_images(self, username, folder_name):
        """Capture face images from webcam with automatic time-based capture"""
        print(f"\n{'='*50}")
        print(f"CAPTURING IMAGES FOR: {username}")
        print(f"{'='*50}")
        print(f"\nWill automatically capture {self.IMAGES_TO_CAPTURE} images...")
        print("Just keep your face in front of the camera!")
        print("Press 'Q' to quit registration")
        print("-" * 50)
        
        # Create user folder
        user_path = FileManager.ensure_user_folder(folder_name)
        
        image_count = 0
        last_capture_time = time.time()
        
        while image_count < self.IMAGES_TO_CAPTURE:
            ret, frame = self.cap.read()
            
            if not ret:
                print("Error: Failed to read from webcam!")
                break
            
            # Flip frame for selfie view
            frame = cv2.flip(frame, 1)
            
            # Detect faces
            faces = self.face_detector.detect_faces(frame)
            
            # Draw information on frame
            info_text = f"Images Captured: {image_count}/{self.IMAGES_TO_CAPTURE}"
            cv2.putText(
                frame,
                info_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )
            
            # Auto-capture every CAPTURE_INTERVAL seconds when face is detected
            current_time = time.time()
            time_elapsed = current_time - last_capture_time
            
            if len(faces) > 0:
                # Draw green box if face detected
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Check if it's time to capture
                if time_elapsed >= self.CAPTURE_INTERVAL:
                    # Save largest face
                    (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
                    face_roi = frame[y:y+h, x:x+w]
                    face_roi = ImageProcessor.preprocess_face_image(face_roi)
                    if face_roi is None:
                        print("⚠ Unable to preprocess face image. Try again.")
                        continue
                    face_roi = (face_roi * 255).astype('uint8')
                    
                    # Save image
                    image_path = os.path.join(user_path, f"{image_count + 1}.jpg")
                    cv2.imwrite(image_path, face_roi)
                    
                    image_count += 1
                    last_capture_time = current_time
                    print(f"✓ Image {image_count}/{self.IMAGES_TO_CAPTURE} captured automatically!")
                
                # Show countdown to next capture
                countdown = int((self.CAPTURE_INTERVAL - time_elapsed) * 10) / 10
                status_text = f"Capturing... ({countdown:.1f}s) until next image"
                cv2.putText(
                    frame,
                    status_text,
                    (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2
                )
            else:
                status_text = "No Face Detected - Position Your Face in Camera"
                cv2.putText(
                    frame,
                    status_text,
                    (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )
            
            cv2.imshow("Face Registration - Auto Capture", frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            # Quit on 'Q' key
            if key == ord('q') or key == ord('Q'):
                print(f"\nRegistration cancelled! Only {image_count} images captured.")
                cv2.destroyAllWindows()
                return False
        
        cv2.destroyAllWindows()
        print(f"\n{'='*50}")
        print(f"✓ Successfully captured {image_count} images!")
        print(f"{'='*50}")
        
        return True
    
    def register_user(self):
        """Main registration workflow"""
        try:
            # Get user information
            name, folder_name, gender = self.get_user_input()
            
            # Open webcam
            if not self.open_webcam():
                return False
            
            # Capture images
            if not self.capture_images(name, folder_name):
                return False
            
            # Save to database
            success, message = DatabaseManager.add_user(folder_name, gender)
            
            if success:
                print(f"\n{'='*50}")
                print("✓ REGISTRATION SUCCESSFUL!")
                print(f"{'='*50}")
                print(f"Name: {name}")
                print(f"Gender: {gender}")
                print(f"Images Captured: {self.IMAGES_TO_CAPTURE}")
                print(f"{'='*50}\n")
                return True
            else:
                print(f"\n⚠ {message}\n")
                return False
        
        except Exception as e:
            print(f"Error during registration: {str(e)}")
            return False
        
        finally:
            if self.cap:
                self.cap.release()
            cv2.destroyAllWindows()


def main():
    """Main function for registration module"""
    registration = UserRegistration()
    registration.register_user()


if __name__ == "__main__":
    main()
