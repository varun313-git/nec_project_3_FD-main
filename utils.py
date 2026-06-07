"""
Utility functions for the Face Detection and Gender Recognition System
Handles common operations like file management, image processing, and database operations
"""

import os
import json
import cv2
import numpy as np
from pathlib import Path


class FileManager:
    """Manages directory and file operations"""
    
    @staticmethod
    def create_directories():
        """Create necessary directories if they don't exist"""
        directories = [
            'dataset',
            'models',
            'database'
        ]
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
    
    @staticmethod
    def ensure_user_folder(username):
        """Create a folder for the user in dataset directory"""
        user_path = Path('dataset') / username
        user_path.mkdir(parents=True, exist_ok=True)
        return str(user_path)


class DatabaseManager:
    """Manages JSON database operations"""
    
    DATABASE_PATH = 'database/users.json'
    
    @staticmethod
    def load_database():
        """Load users from JSON database"""
        if not os.path.exists(DatabaseManager.DATABASE_PATH):
            return {}
        
        try:
            with open(DatabaseManager.DATABASE_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Warning: Database file is corrupted. Creating new database.")
            return {}
    
    @staticmethod
    def save_database(data):
        """Save users to JSON database"""
        Path('database').mkdir(exist_ok=True)
        with open(DatabaseManager.DATABASE_PATH, 'w') as f:
            json.dump(data, f, indent=4)
    
    @staticmethod
    def add_user(username, gender):
        """Add a new user to the database"""
        database = DatabaseManager.load_database()
        if username in database:
            return False, f"User '{username}' already exists!"
        
        database[username] = {'gender': gender}
        DatabaseManager.save_database(database)
        return True, f"User '{username}' registered successfully!"
    
    @staticmethod
    def user_exists(username):
        """Check if user exists in database"""
        database = DatabaseManager.load_database()
        return username in database
    
    @staticmethod
    def get_user_gender(username):
        """Get user gender from database"""
        database = DatabaseManager.load_database()
        if username in database:
            return database[username].get('gender', 'Unknown')
        return 'Unknown'
    
    @staticmethod
    def get_all_users():
        """Get all registered users"""
        database = DatabaseManager.load_database()
        return list(database.keys())


class ImageProcessor:
    """Handles image processing operations"""
    
    TARGET_SIZE = (64, 64)
    
    @staticmethod
    def preprocess_face_image(image):
        """Normalize a face crop for both training and detection."""
        if image is None or image.size == 0:
            return None
        
        resized = cv2.resize(image, ImageProcessor.TARGET_SIZE)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        equalized = cv2.equalizeHist(gray)
        normalized = cv2.cvtColor(equalized, cv2.COLOR_GRAY2BGR)
        normalized = normalized.astype('float32') / 255.0
        return normalized
    
    @staticmethod
    def load_and_preprocess_image(image_path):
        """Load and preprocess an image for model input"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return None

            return ImageProcessor.preprocess_face_image(image)
        except Exception as e:
            print(f"Error processing image {image_path}: {str(e)}")
            return None
    
    @staticmethod
    def load_dataset():
        """Load all images from dataset folder"""
        dataset_path = Path('dataset')
        
        if not dataset_path.exists():
            print("Dataset folder not found!")
            return None, None
        
        images = []
        labels = []
        label_map = {}
        label_counter = 0
        
        # Iterate through each person folder
        for person_folder in sorted(dataset_path.iterdir()):
            if not person_folder.is_dir():
                continue
            
            person_name = person_folder.name
            label_map[label_counter] = person_name
            
            # Load images from person folder
            image_count = 0
            for image_file in person_folder.glob('*.jpg'):
                image = ImageProcessor.load_and_preprocess_image(str(image_file))
                if image is not None:
                    images.append(image)
                    labels.append(label_counter)
                    image_count += 1
            
            if image_count > 0:
                print(f"Loaded {image_count} images for {person_name}")
            
            label_counter += 1
        
        if len(images) == 0:
            print("No images found in dataset!")
            return None, None
        
        # Convert to numpy arrays
        images = np.array(images)
        labels = np.array(labels)
        
        print(f"\nTotal images loaded: {len(images)}")
        print(f"Total persons: {len(label_map)}")
        
        return images, labels, label_map
    
    @staticmethod
    def get_dataset_count():
        """Get count of images in each person folder"""
        dataset_path = Path('dataset')
        counts = {}
        
        if not dataset_path.exists():
            return counts
        
        for person_folder in dataset_path.iterdir():
            if person_folder.is_dir():
                image_count = len(list(person_folder.glob('*.jpg')))
                if image_count > 0:
                    counts[person_folder.name] = image_count
        
        return counts


class FaceDetector:
    """Handles face detection using Haar Cascade"""
    
    # Load Haar Cascade classifier
    CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    
    @staticmethod
    def detect_faces(frame):
        """
        Detect faces in a frame
        Returns list of (x, y, w, h) tuples
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = FaceDetector.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            maxSize=(300, 300)
        )
        return faces
    
    @staticmethod
    def draw_face_box_with_label(frame, x, y, w, h, label, color=(0, 255, 0)):
        """Draw bounding box and label on frame"""
        # Draw bounding box
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)
        
        # Draw label background
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
        cv2.rectangle(
            frame,
            (x, y - 35),
            (x + label_size[0], y),
            color,
            -1
        )
        
        # Put text
        cv2.putText(
            frame,
            label,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )
        
        return frame


# Initialize file manager
FileManager.create_directories()
