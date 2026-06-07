"""
Installation and Dependency Verification Script
Checks if all required packages are installed and working correctly
"""

import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f" {text}")
    print("="*70)


def print_success(text):
    """Print success message"""
    print(f"✓ {text}")


def print_error(text):
    """Print error message"""
    print(f"✗ {text}")


def print_warning(text):
    """Print warning message"""
    print(f"⚠ {text}")


def check_python_version():
    """Check Python version"""
    print_header("PYTHON VERSION")
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 10:
        print_success(f"Python {version.major}.{version.minor}+ detected")
        return True
    else:
        print_error(f"Python 3.10+ required. Found {version.major}.{version.minor}")
        return False


def check_package(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name.lower().replace("-", "_")
    
    try:
        __import__(import_name)
        
        # Get version
        try:
            module = __import__(import_name)
            version = getattr(module, '__version__', 'Unknown')
            print_success(f"{package_name}: {version}")
            return True
        except:
            print_success(f"{package_name}: Installed")
            return True
    
    except ImportError:
        print_error(f"{package_name}: NOT INSTALLED")
        return False


def check_dependencies():
    """Check all required dependencies"""
    print_header("DEPENDENCY VERIFICATION")
    
    packages = [
        ("opencv-python", "cv2"),
        ("numpy", "numpy"),
        ("tensorflow", "tensorflow"),
        ("keras", "keras"),
        ("matplotlib", "matplotlib"),
        ("pillow", "PIL"),
    ]
    
    results = {}
    for package, import_name in packages:
        results[package] = check_package(package, import_name)
    
    return all(results.values())


def check_directories():
    """Check if project directories exist"""
    print_header("DIRECTORY STRUCTURE")
    
    required_dirs = [
        "dataset",
        "models",
        "database",
        "registration",
        "training",
        "detection"
    ]
    
    all_exist = True
    for directory in required_dirs:
        if Path(directory).exists():
            print_success(f"Directory: {directory}/")
        else:
            print_warning(f"Directory: {directory}/ (will be created)")
            Path(directory).mkdir(exist_ok=True)
    
    return True


def check_files():
    """Check if main files exist"""
    print_header("PROJECT FILES")
    
    required_files = [
        "main.py",
        "utils.py",
        "requirements.txt",
        "README.md",
        "registration/register_user.py",
        "training/train_model.py",
        "detection/detect_live.py",
    ]
    
    all_exist = True
    for file in required_files:
        if Path(file).exists():
            print_success(f"File: {file}")
        else:
            print_error(f"File: {file} (MISSING)")
            all_exist = False
    
    return all_exist


def check_webcam():
    """Check if webcam is available"""
    print_header("HARDWARE VERIFICATION")
    
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print_success("Webcam: Detected and working")
            cap.release()
            return True
        else:
            print_warning("Webcam: Not accessible (may need permissions)")
            return False
    except:
        print_warning("Webcam: Could not verify")
        return False


def check_tensorflow_gpu():
    """Check if TensorFlow can use GPU"""
    print_header("GPU ACCELERATION")
    
    try:
        import tensorflow as tf
        gpus = tf.config.list_physical_devices('GPU')
        
        if gpus:
            print_success(f"GPU: {len(gpus)} device(s) detected")
            for gpu in gpus:
                print(f"  - {gpu}")
            print_success("GPU acceleration available")
            return True
        else:
            print_warning("GPU: No GPU detected (will use CPU)")
            return False
    except:
        print_warning("GPU: Could not verify (will use CPU)")
        return False


def print_next_steps():
    """Print next steps"""
    print_header("NEXT STEPS")
    
    print("\n1. Register a user:")
    print("   python registration/register_user.py")
    
    print("\n2. Train the model:")
    print("   python training/train_model.py")
    
    print("\n3. Run live detection:")
    print("   python detection/detect_live.py")
    
    print("\n4. Or use the main menu:")
    print("   python main.py")
    
    print("\nFor detailed instructions, see:")
    print("   - README.md (Complete documentation)")
    print("   - QUICKSTART.md (Quick start guide)")
    print("   - ARCHITECTURE.md (System architecture)")
    print()


def main():
    """Run all checks"""
    print("\n" + "🔍 "*35)
    print("FACE DETECTION AND GENDER RECOGNITION SYSTEM")
    print("Installation and Verification Script")
    print("🔍 "*35)
    
    checks = {
        "Python Version": check_python_version(),
        "Dependencies": check_dependencies(),
        "Directories": check_directories(),
        "Project Files": check_files(),
        "Webcam": check_webcam(),
        "GPU Support": check_tensorflow_gpu(),
    }
    
    print_header("VERIFICATION SUMMARY")
    
    for check_name, result in checks.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{check_name}: {status}")
    
    if all(checks.values()):
        print("\n" + "🎉 "*20)
        print("ALL CHECKS PASSED - System is ready!")
        print("🎉 "*20)
        print_next_steps()
        return 0
    else:
        print("\n" + "⚠️  "*20)
        print("Some checks failed. Please fix the issues above.")
        print("⚠️  "*20)
        print("\nFor help:")
        print("  - Check README.md Troubleshooting section")
        print("  - Run: pip install -r requirements.txt")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
