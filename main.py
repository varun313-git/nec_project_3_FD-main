"""
Real-Time Name and Gender Detection System using CNN and OpenCV
Main Entry Point for the Application

This system allows:
1. User registration with face capture
2. Training a CNN model on collected faces
3. Live detection and gender recognition from webcam
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from registration.register_user import UserRegistration
from training.train_model import ModelTrainer
from detection.detect_live import LiveFaceRecognizer
from utils import DatabaseManager


class FaceDetectionSystem:
    """Main system controller"""
    
    def __init__(self):
        """Initialize the system"""
        self.ensure_directories()
    
    @staticmethod
    def ensure_directories():
        """Ensure all required directories exist"""
        directories = [
            'dataset',
            'models',
            'database',
            'registration',
            'training',
            'detection'
        ]
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
    
    def display_menu(self):
        """Display main menu"""
        print("\n" + "="*70)
        print(" "*15 + "FACE DETECTION AND GENDER RECOGNITION")
        print(" "*20 + "System v1.0")
        print("="*70)
        print("\nAvailable Options:")
        print("-" * 70)
        print("1. Register New User")
        print("2. Train Model")
        print("3. Live Detection")
        print("4. View Registered Users")
        print("5. Exit")
        print("-" * 70)
    
    def view_registered_users(self):
        """Display all registered users"""
        print("\n" + "="*70)
        print("REGISTERED USERS")
        print("="*70)
        
        database = DatabaseManager.load_database()
        
        if not database:
            print("No registered users yet!")
        else:
            print(f"\nTotal Users: {len(database)}\n")
            for idx, (username, data) in enumerate(database.items(), 1):
                gender = data.get('gender', 'Unknown')
                
                # Count images
                user_folder = Path('dataset') / username
                if user_folder.exists():
                    image_count = len(list(user_folder.glob('*.jpg')))
                else:
                    image_count = 0
                
                print(f"{idx}. {username:<20} | Gender: {gender:<8} | Images: {image_count}")
        
        print("="*70 + "\n")
    
    def register_user(self):
        """Handle user registration"""
        try:
            registration = UserRegistration()
            success = registration.register_user()
            
            if success:
                print("\n✓ Registration completed successfully!")
            else:
                print("\n⚠ Registration was not completed.")
        
        except KeyboardInterrupt:
            print("\n\nRegistration cancelled by user.")
        except Exception as e:
            print(f"\n❌ Error during registration: {str(e)}")
    
    def train_model(self):
        """Handle model training"""
        try:
            # Check if dataset has images
            database = DatabaseManager.load_database()
            
            if not database:
                print("\n" + "="*70)
                print("⚠ NO REGISTERED USERS FOUND!")
                print("="*70)
                print("Please register users first before training.")
                print("="*70 + "\n")
                return
            
            print("\n" + "="*70)
            print("Checking dataset...")
            print("="*70)
            
            total_images = 0
            for username in database.keys():
                user_folder = Path('dataset') / username
                if user_folder.exists():
                    image_count = len(list(user_folder.glob('*.jpg')))
                    total_images += image_count
                    print(f"{username}: {image_count} images")
            
            print(f"\nTotal Images: {total_images}")
            
            if total_images < 30:
                print("\n" + "="*70)
                print("⚠ INSUFFICIENT DATA!")
                print("="*70)
                print("Need at least 30 images total for training.")
                print(f"Currently have: {total_images} images")
                print("="*70 + "\n")
                return
            
            print("="*70 + "\n")
            
            # Start training
            trainer = ModelTrainer()
            success = trainer.train()
            
            if success:
                print("\n✓ Model training completed successfully!")
            else:
                print("\n⚠ Model training failed.")
        
        except KeyboardInterrupt:
            print("\n\nTraining cancelled by user.")
        except Exception as e:
            print(f"\n❌ Error during training: {str(e)}")
    
    def live_detection(self):
        """Handle live face detection"""
        try:
            # Check if model exists
            if not Path('models/face_model.h5').exists():
                print("\n" + "="*70)
                print("⚠ MODEL NOT FOUND!")
                print("="*70)
                print("Please train the model first using option 2.")
                print("="*70 + "\n")
                return
            
            # Start live detection
            recognizer = LiveFaceRecognizer()
            success = recognizer.run()
            
            if success:
                print("\n✓ Live detection completed successfully!")
            else:
                print("\n⚠ Live detection failed.")
        
        except KeyboardInterrupt:
            print("\n\nLive detection cancelled by user.")
        except Exception as e:
            print(f"\n❌ Error during live detection: {str(e)}")
    
    def run(self):
        """Main application loop"""
        print("\n" + "="*70)
        print("Initializing System...")
        print("="*70)
        self.ensure_directories()
        print("✓ System initialized successfully!\n")
        
        while True:
            self.display_menu()
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == '1':
                self.register_user()
            
            elif choice == '2':
                self.train_model()
            
            elif choice == '3':
                self.live_detection()
            
            elif choice == '4':
                self.view_registered_users()
            
            elif choice == '5':
                print("\n" + "="*70)
                print("Thank you for using Face Detection and Gender Recognition System!")
                print("="*70 + "\n")
                sys.exit(0)
            
            else:
                print("\n❌ Invalid option! Please select 1-5.\n")


def main():
    """Main entry point"""
    try:
        system = FaceDetectionSystem()
        system.run()
    
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("Application interrupted by user.")
        print("="*70 + "\n")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
