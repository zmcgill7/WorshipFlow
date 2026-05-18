# Worship Flow

An intelligent deep learning system for classifying musical instruments commonly used in worship music. Built on YAMNet embeddings and trained with TensorFlow, this project includes both the model training workflow and a hosted full-stack web app for analyzing uploaded audio.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Instrument Categories](#instrument-categories)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Detailed Workflow](#detailed-workflow)
- [Project Structure](#project-structure)
- [Usage Examples](#usage-examples)
- [Model Performance](#model-performance)
- [Contributing](#contributing)
- [License](#license)

## Overview

https://github.com/user-attachments/assets/88d520e6-3b4a-4ca9-a549-0036becd44d8

Live app: https://worshipflow.site

Worship Flow is designed to automatically identify and classify musical instruments in worship music recordings. Whether you're organizing a music library, analyzing recordings, or building music information retrieval systems, this tool provides fast instrument classification from uploaded audio.

The system uses transfer learning with Google's YAMNet (a pre-trained audio classification model) as a feature extractor, combined with a custom classification head trained specifically on worship music instruments.

The production app uses React, Firebase Authentication, Django, Firestore, and Cloud Run. I keep it hosted cheaply by using Cloud Run scale-to-zero and storing only lightweight analysis history in Firestore.

## Features

- **7 Instrument Categories**: Classifies guitar, bass, keyboard, drums, strings, brass, and vocals
- **Transfer Learning**: Leverages YAMNet's powerful audio embeddings
- **Web Upload Flow**: Analyze `.mp3`, `.mp4`, and `.wav` files from the browser
- **User History**: Firebase Authentication and Firestore store previous analysis results per user
- **Easy Dataset Management**: One-time extraction, reusable splits
- **Comprehensive Evaluation**: Confusion matrices, classification reports, and accuracy metrics
- **TensorBoard Integration**: Visualize training progress
- **Production Deployment**: Dockerized Django/React app deployed to Cloud Run

## Instrument Categories

The model classifies instruments into 7 categories:

| Category | Includes | Examples |
|----------|----------|----------|
| **Guitar** | Acoustic & Electric Guitars | Rhythm guitar, lead guitar |
| **Bass** | Bass Guitars | Electric bass, acoustic bass |
| **Keyboard** | Piano, Organ, Synth, Mallet | Grand piano, Hammond organ, synthesizers |
| **Drums** | Drum Kit & Percussion | Kick, snare, cymbals |
| **Strings** | Orchestral Strings | Violin, cello, viola |
| **Brass** | Brass Instruments | Trumpet, trombone, French horn |
| **Vocals** | Voice | Lead vocals, backing vocals, choir |

## Requirements

### System Requirements
- Python 3.8 or higher
- 16GB RAM minimum (32GB recommended for large datasets)
- 80GB free disk space (for NSynth dataset)
- GPU recommended (but not required)

### Python Dependencies

```txt
tensorflow>=2.10.0
tensorflow-hub>=0.12.0
librosa>=0.10.0
numpy>=1.21.0
scikit-learn>=1.0.0
tqdm>=4.64.0
```

## Installation

### 1. Clone or Download the Repository

```bash
git clone https://github.com/zmcgill7/WorshipFlow.git
cd WorshipFlow
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install tensorflow tensorflow-hub librosa numpy scikit-learn tqdm
```

### 4. Verify Installation

```bash
python -c "import tensorflow as tf; print(f'TensorFlow {tf.__version__} installed successfully')"
```

## ⚡ Quick Start

### One-Time Setup (15-30 minutes)

```bash
# 1. Download NSynth dataset (73GB - this takes a while)
wget http://download.magenta.tensorflow.org/datasets/nsynth/nsynth-train.jsonwav.tar.gz

# 2. Extract the dataset
tar -xzf nsynth-train.jsonwav.tar.gz

# 3. Organize dataset into train/val/test splits
python training/utils/nsynth_extractor.py \
    --nsynth_dir ./nsynth-train \
    --output_dir ./nsynth-splits \
    --train_samples 10000 \
    --val_samples 1000 \
    --test_samples 1000
```

### Train the Model (30-60 minutes)

```bash
python training/train.py \
    --splits_dir ./nsynth-splits \
    --output_dir ./training/models/worship_flow \
    --epochs 30 \
    --batch_size 32
```

### Run Inference

```bash
python training/inference/predict_v2.py
```

The deployed Django API uses the same inference approach from `backend/core/model_utils/predict_v2.py`.

## Detailed Workflow

### Step 1: Dataset Extraction

The NSynth dataset is large (73GB) and takes time to process. We extract and organize it **once**, then reuse the organized splits for training.

```bash
python training/utils/nsynth_extractor.py \
    --nsynth_dir ./nsynth-train \
    --output_dir ./nsynth-splits \
    --train_samples 10000 \
    --val_samples 1000 \
    --test_samples 1000
```

**Parameters:**
- `--nsynth_dir`: Path to downloaded and extracted NSynth dataset
- `--output_dir`: Where to save organized splits
- `--train_samples`: Number of training samples
- `--val_samples`: Number of validation samples
- `--test_samples`: Number of test samples

**Output Structure:**
```
nsynth-splits/
├── train/
│   ├── guitar/
│   │   ├── guitar_acoustic_001.wav
│   │   ├── guitar_electric_002.wav
│   │   └── ...
│   ├── bass/
│   ├── keyboard/
│   ├── string/
│   ├── brass/
│   ├── reed/
│   ├── vocal/
│   └── metadata.json
├── validation/
│   └── (same structure)
├── test/
│   └── (same structure)
└── config.json
```

### Step 2: Model Training

Train the classifier using the organized dataset:

```bash
python training/train.py \
    --splits_dir ./nsynth-splits \
    --output_dir ./training/models/worship_flow \
    --epochs 30 \
    --batch_size 32 \
    --learning_rate 0.001
```

**Parameters:**
- `--splits_dir`: Path to organized dataset splits
- `--output_dir`: Where to save trained model and results
- `--epochs`: Number of training epochs (default: 30)
- `--batch_size`: Batch size for training (default: 32)
- `--learning_rate`: Learning rate (default: 0.001)

**Training Process:**
1. Loads pre-organized dataset splits
2. Downloads YAMNet model for feature extraction
3. Extracts YAMNet embeddings from all audio
4. Trains classification head
5. Evaluates on validation and test sets
6. Saves model, metrics, and logs

**Output:**
```
training/models/worship_flow/
├── worship_flow_final.keras       # Trained model
├── training_results.json          # Training metrics
├── evaluation_results.json        # Confusion matrix & report
├── training_log.csv               # Epoch-by-epoch logs
├── checkpoints/
│   └── best_model.keras           # Best model during training
└── logs/                          # TensorBoard logs
```

**Monitor Training:**
```bash
tensorboard --logdir ./training/models/worship_flow/logs
```
Then open http://localhost:6006 in your browser.

### Step 3: Inference / Prediction

Use the trained model to classify instruments in new audio files. The web app calls the Django endpoint at `/api/analyze/`, which uses `backend/core/model_utils/predict_v2.py`.

#### Production API Flow

```bash
curl -X POST https://worshipflow.site/api/analyze/ \
    -H "Authorization: Bearer <firebase-id-token>" \
    -F "file=@song.wav"
```

**Output:**
```json
{
  "results": [
    {
      "filename": "song.wav",
      "predictions": [
        { "instrument": "keyboard", "confidence": 0.75 },
        { "instrument": "guitar", "confidence": 0.68 }
      ]
    }
  ]
}
```

## Project Structure

```
WorshipFlow/
│
├── README.md                      # This file
├── Dockerfile                     # Production image for frontend + backend
├── cloudbuild.yaml                # Cloud Build / Cloud Run deployment
│
├── frontend/                      # React + TypeScript app
│   └── src/
│
├── backend/                       # Django API and production model
│   ├── core/
│   │   ├── views.py               # Analyze and history endpoints
│   │   ├── middleware.py          # Firebase token auth
│   │   └── model_utils/           # Keras model + inference utilities
│   └── requirements.txt
│
└── training/                      # Training scripts, notebooks, and experiments
    ├── train.py
    ├── train_medleydb.py
    ├── inference/
    ├── models/
    └── utils/
```

## Usage Examples

### Example 1: Training with Custom Parameters

```bash
python training/train.py \
    --splits_dir ./nsynth-splits \
    --output_dir ./training/models/my_custom_model \
    --epochs 50 \
    --batch_size 64 \
    --learning_rate 0.0005
```

### Example 2: Using Smaller Dataset for Testing

```bash
# Extract smaller dataset for quick testing
python training/utils/nsynth_extractor.py \
    --nsynth_dir ./nsynth-train \
    --output_dir ./nsynth-splits-small \
    --train_samples 1000 \
    --val_samples 100 \
    --test_samples 100

# Train quickly
python training/train.py \
    --splits_dir ./nsynth-splits-small \
    --output_dir ./training/models/test_model \
    --epochs 10 \
    --batch_size 32
```

### Example 3: Deploy to Cloud Run

```bash
gcloud builds submit --config cloudbuild.yaml --project worship-flow-479220 .
```

## Model Performance

### Current Checked-In Production Model

| Metric | Value |
|--------|-------|
| Sample F1 | 0.920 |
| Jaccard Score | 0.882 |
| Hamming Loss | 0.070 |
| Epochs | 50 |
| Training Samples | 919 |
| Validation Samples | 114 |
| Test Samples | 116 |

### Performance Tips

**For Better Accuracy:**
- Increase training samples
- Train for more epochs
- Use data augmentation
- Fine-tune learning rate

**For Faster Training:**
- Use GPU (NVIDIA with CUDA support)
- Decrease batch size if out of memory
- Use smaller dataset for testing

**For Faster Inference:**
- Keep the Cloud Run instance warm for demos
- Batch multiple predictions together
- Pre-bundle YAMNet in the image so it is not downloaded at request time

## Troubleshooting

### Common Issues

**Issue: Out of memory during training**
- **Solution**: Reduce batch size: `--batch_size 16` or `--batch_size 8`

**Issue: Training is very slow**
- **Solution**: Use GPU or reduce training samples for testing

**Issue: Low accuracy**
- **Solution**: Increase training samples and epochs, check data quality

**Issue: "Config not found" error**
- **Solution**: Ensure you ran `training/utils/nsynth_extractor.py` first to create organized splits

**Issue: History fails in production**
- **Solution**: Ensure `FIRESTORE_DATABASE_ID` points to the named Firestore database and production is deployed with `DJANGO_DEBUG=False`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
git clone https://github.com/zmcgill7/WorshipFlow.git
cd WorshipFlow
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Running Tests

```bash
# Quick test with small dataset
python training/utils/nsynth_extractor.py --nsynth_dir ./nsynth-train --output_dir ./test-splits --train_samples 100 --val_samples 10 --test_samples 10
python training/train.py --splits_dir ./test-splits --output_dir ./test-models --epochs 5
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [NSynth Dataset](https://magenta.tensorflow.org/datasets/nsynth) by Google Magenta
- [YAMNet](https://tfhub.dev/google/yamnet/1) by Google Research
- TensorFlow and TensorFlow Hub teams

## Future Enhancements

- [ ] Real-time audio classification
- [ ] Mobile app integration
- [ ] Extended instrument categories
- [ ] Audio segmentation and timestamping
- [ ] Confidence calibration
