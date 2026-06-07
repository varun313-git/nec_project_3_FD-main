"""
Training Module for Face Detection and Gender Recognition System
Trains a CNN model on the captured face images
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import ImageProcessor, DatabaseManager


class FaceRecognitionCNN:
    """CNN model for face recognition"""
    
    @staticmethod
    def build_model(num_classes):
        """
        Build CNN architecture for face recognition
        
        Architecture:
        - Input: 64x64x3
        - Conv2D(32) + MaxPool
        - Conv2D(64) + MaxPool
        - Conv2D(128) + MaxPool
        - Flatten
        - Dense(128)
        - Output: num_classes
        """
        
        model = keras.Sequential([
            # Input layer
            keras.Input(shape=(64, 64, 3)),

            # Built-in augmentation layers avoid the SciPy dependency used by ImageDataGenerator
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.05),
            layers.RandomZoom(0.1),
            layers.RandomTranslation(0.05, 0.05),
            layers.RandomContrast(0.1),
            
            # Block 1
            layers.Conv2D(32, (3, 3), activation='relu', kernel_regularizer=keras.regularizers.l2(1e-4)),
            layers.MaxPooling2D((2, 2)),
            layers.BatchNormalization(),
            
            # Block 2
            layers.Conv2D(64, (3, 3), activation='relu', kernel_regularizer=keras.regularizers.l2(1e-4)),
            layers.MaxPooling2D((2, 2)),
            layers.BatchNormalization(),
            
            # Block 3
            layers.Conv2D(128, (3, 3), activation='relu', kernel_regularizer=keras.regularizers.l2(1e-4)),
            layers.MaxPooling2D((2, 2)),
            layers.BatchNormalization(),
            
            # Flatten and Dense layers
            layers.Flatten(),
            layers.Dense(128, activation='relu', kernel_regularizer=keras.regularizers.l2(1e-4)),
            layers.Dropout(0.5),
            
            # Output layer
            layers.Dense(num_classes, activation='softmax')
        ])
        
        return model
    
    @staticmethod
    def compile_model(model):
        """Compile the model"""
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        return model
    
    @staticmethod
    def print_model_summary(model):
        """Print model architecture summary"""
        print("\n" + "="*70)
        print("CNN MODEL ARCHITECTURE")
        print("="*70)
        model.summary()
        print("="*70 + "\n")


class DataPreprocessor:
    """Preprocesses data for training"""
    
    @staticmethod
    def prepare_data(images, labels, test_split=0.2):
        """
        Prepare training and testing data
        
        Args:
            images: Array of images
            labels: Array of labels
            test_split: Test set percentage
        
        Returns:
            X_train, X_test, y_train, y_test
        """
        # Split each class separately so validation always contains every person
        X_train_parts = []
        X_test_parts = []
        y_train_parts = []
        y_test_parts = []

        for class_id in np.unique(labels):
            class_indices = np.where(labels == class_id)[0]
            class_indices = np.random.permutation(class_indices)

            split_point = max(1, int(len(class_indices) * (1 - test_split)))
            if split_point >= len(class_indices):
                split_point = len(class_indices) - 1

            train_indices = class_indices[:split_point]
            test_indices = class_indices[split_point:]

            X_train_parts.append(images[train_indices])
            X_test_parts.append(images[test_indices])
            y_train_parts.append(labels[train_indices])
            y_test_parts.append(labels[test_indices])

        X_train = np.concatenate(X_train_parts, axis=0)
        X_test = np.concatenate(X_test_parts, axis=0)
        y_train = np.concatenate(y_train_parts, axis=0)
        y_test = np.concatenate(y_test_parts, axis=0)

        # Shuffle the final splits
        train_order = np.random.permutation(len(X_train))
        test_order = np.random.permutation(len(X_test))
        X_train = X_train[train_order]
        y_train = y_train[train_order]
        X_test = X_test[test_order]
        y_test = y_test[test_order]
        
        print(f"\nTraining samples: {len(X_train)}")
        print(f"Testing samples: {len(X_test)}")
        
        # Convert labels to one-hot encoding
        num_classes = len(np.unique(labels))
        y_train = keras.utils.to_categorical(y_train, num_classes)
        y_test = keras.utils.to_categorical(y_test, num_classes)
        
        return X_train, X_test, y_train, y_test, num_classes


class ModelTrainer:
    """Trains the CNN model"""
    
    def __init__(self):
        """Initialize trainer"""
        self.model = None
        self.history = None
        self.label_map = None
    
    def load_and_prepare_data(self):
        """Load dataset and prepare for training"""
        print("\n" + "="*70)
        print("LOADING DATASET")
        print("="*70)
        
        images, labels, label_map = ImageProcessor.load_dataset()
        
        if images is None or labels is None:
            print("Failed to load dataset!")
            return False
        
        self.label_map = label_map
        
        # Prepare data
        X_train, X_test, y_train, y_test, num_classes = DataPreprocessor.prepare_data(
            images, labels
        )
        
        return images, labels, X_train, X_test, y_train, y_test, num_classes

    def save_class_centroids(self, images, labels):
        """Save centroid embeddings for each registered person."""
        try:
            feature_model = keras.Model(
                inputs=self.model.input,
                outputs=self.model.layers[-3].output
            )

            embeddings = feature_model.predict(images, verbose=0)
            embeddings = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)

            centroids = {}
            for class_id in sorted(np.unique(labels)):
                class_embeddings = embeddings[labels == class_id]
                if len(class_embeddings) == 0:
                    continue
                centroid = np.mean(class_embeddings, axis=0)
                centroid = centroid / (np.linalg.norm(centroid) + 1e-8)
                centroids[int(class_id)] = centroid

            np.save('models/class_centroids.npy', centroids)
            print("✓ Class centroids saved to: models/class_centroids.npy")
        except Exception as e:
            print(f"Error saving class centroids: {str(e)}")
    
    def train(self):
        """Main training workflow"""
        try:
            # Load and prepare data
            data = self.load_and_prepare_data()
            
            if not data:
                return False
            
            images, labels, X_train, X_test, y_train, y_test, num_classes = data
            
            # Build model
            print("\n" + "="*70)
            print("BUILDING MODEL")
            print("="*70)
            
            self.model = FaceRecognitionCNN.build_model(num_classes)
            self.model = FaceRecognitionCNN.compile_model(self.model)
            
            # Print model summary
            FaceRecognitionCNN.print_model_summary(self.model)
            
            # Train model
            print("="*70)
            print("TRAINING MODEL")
            print("="*70)
            print(f"Epochs: 20 | Batch Size: 8 | Classes: {num_classes}\n")

            class_counts = np.bincount(np.argmax(y_train, axis=1))
            class_weights = {
                class_id: float(len(y_train)) / (num_classes * count)
                for class_id, count in enumerate(class_counts)
                if count > 0
            }

            callbacks = [
                keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=5,
                    restore_best_weights=True
                ),
                keras.callbacks.ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=2,
                    min_lr=1e-6
                ),
                keras.callbacks.ModelCheckpoint(
                    'models/best_face_model.h5',
                    monitor='val_loss',
                    save_best_only=True,
                    verbose=1
                )
            ]
            
            self.history = self.model.fit(
                X_train, y_train,
                batch_size=8,
                epochs=20,
                validation_data=(X_test, y_test),
                class_weight=class_weights,
                callbacks=callbacks,
                verbose=1
            )
            
            # Evaluate model
            print("\n" + "="*70)
            print("MODEL EVALUATION")
            print("="*70)
            
            loss, accuracy = self.model.evaluate(X_test, y_test)
            print(f"Test Accuracy: {accuracy * 100:.2f}%")
            print(f"Test Loss: {loss:.4f}")
            print("="*70 + "\n")
            
            # Save model and label map
            self.save_model()

            # Save centroid embeddings for better live recognition stability
            self.save_class_centroids(images, labels)
            
            # Plot training history
            self.plot_training_history()
            
            return True
        
        except Exception as e:
            print(f"Error during training: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_model(self):
        """Save trained model and label map"""
        try:
            print("="*70)
            print("SAVING MODEL")
            print("="*70)
            
            # Create models directory
            Path('models').mkdir(exist_ok=True)
            
            # Save model
            model_path = 'models/face_model.h5'
            self.model.save(model_path)
            print(f"✓ Model saved to: {model_path}")
            
            # Save label map
            label_map_path = 'models/label_map.npy'
            np.save(label_map_path, self.label_map)
            print(f"✓ Label map saved to: {label_map_path}")
            
            print("="*70 + "\n")
        
        except Exception as e:
            print(f"Error saving model: {str(e)}")
    
    def plot_training_history(self):
        """Plot and save training history graphs"""
        try:
            if self.history is None:
                return
            
            print("="*70)
            print("GENERATING TRAINING PLOTS")
            print("="*70)
            
            fig, axes = plt.subplots(1, 2, figsize=(14, 5))
            
            # Accuracy plot
            axes[0].plot(self.history.history['accuracy'], label='Training Accuracy')
            axes[0].plot(self.history.history['val_accuracy'], label='Validation Accuracy')
            axes[0].set_title('Model Accuracy', fontsize=14, fontweight='bold')
            axes[0].set_xlabel('Epoch')
            axes[0].set_ylabel('Accuracy')
            axes[0].legend()
            axes[0].grid(True)
            
            # Loss plot
            axes[1].plot(self.history.history['loss'], label='Training Loss')
            axes[1].plot(self.history.history['val_loss'], label='Validation Loss')
            axes[1].set_title('Model Loss', fontsize=14, fontweight='bold')
            axes[1].set_xlabel('Epoch')
            axes[1].set_ylabel('Loss')
            axes[1].legend()
            axes[1].grid(True)
            
            plt.tight_layout()
            
            # Save plot
            plot_path = 'models/training_history.png'
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            print(f"✓ Training history plot saved to: {plot_path}")
            
            # Display plot
            plt.show()
            
            print("="*70 + "\n")
        
        except Exception as e:
            print(f"Error plotting training history: {str(e)}")


def main():
    """Main function for training module"""
    trainer = ModelTrainer()
    success = trainer.train()
    
    if success:
        print("\n" + "🎉 "*20)
        print("TRAINING COMPLETED SUCCESSFULLY!")
        print("🎉 "*20 + "\n")
        print("Next step: Run detection/detect_live.py to test the model")
    else:
        print("\n❌ Training failed. Please check the dataset and try again.")


if __name__ == "__main__":
    main()
