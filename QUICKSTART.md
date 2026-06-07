# Face Detection and Gender Recognition System
# Quick Start Guide

## Installation (Windows PowerShell)

```powershell
# 1. Create virtual environment
python -m venv face_env

# 2. Activate environment
.\face_env\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Register Users
```powershell
python registration/register_user.py
```

Follow prompts:
- Enter name
- Select gender
- Keep your face in front of camera - automatically captures 50 images (no pressing needed!)
- Takes ~15 seconds (one image every 0.3 seconds)
- Press Q to quit early

### 2. Train Model
```powershell
python training/train_model.py
```

Trains CNN on collected images. Takes 2-5 minutes.

### 3. Live Detection
```powershell
python detection/detect_live.py
```

Detects and recognizes faces in real-time from webcam.

## Or Use Main Menu

```powershell
python main.py
```

Interactive menu for all operations.

## Key Files

| File | Purpose |
|------|---------|
| `utils.py` | Utility functions for all modules |
| `main.py` | Main application entry point |
| `registration/register_user.py` | User registration |
| `training/train_model.py` | CNN model training |
| `detection/detect_live.py` | Live face detection |
| `database/users.json` | User data storage |
| `dataset/` | Face image storage |
| `models/` | Trained model storage |

## Minimum Requirements

- Python 3.10+
- 4GB RAM
- Webcam
- ~2GB disk space

## Troubleshooting

**Webcam error:** Check if webcam is working and not in use by other apps.

**Model not found:** Run training first.

**Poor accuracy:** Register more images (60-100 per person) in different lighting.

**TensorFlow errors:** Reinstall: `pip install --upgrade tensorflow`

## Expected Output

### Registration
```
✓ Image 1/30 captured!
✓ Image 2/30 captured!
...
✓ Image 30/30 captured!
✓ REGISTRATION SUCCESSFUL!
```

### Training
```
Epoch 1/20: loss: 0.7234 - accuracy: 0.5000
...
Epoch 20/20: loss: 0.1234 - accuracy: 0.9688
Test Accuracy: 95.45%
✓ Model saved!
```

### Live Detection
```
Green box + "Meeravali | Male" = Recognized
Red box + "Unknown (45%)" = Not recognized
```

## Next Steps

1. See README.md for detailed documentation
2. Check code comments in .py files
3. Modify confidence threshold in detect_live.py
4. Extend with age detection or emotion recognition

---

**Good Luck with your project! 🚀**
