# Worship Flow

An intelligent deep learning system for classifying musical instruments commonly used in worship music. Built on YAMNet embeddings and trained on the NSynth dataset, this classifier can identify 7 different instrument categories from audio recordings.

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

Worship Flow is designed to automatically identify and classify musical instruments in worship music recordings. Whether you're organizing a music library, analyzing recordings, or building music information retrieval systems, this tool provides accurate, fast instrument classification.

The system uses transfer learning with Google's YAMNet (a pre-trained audio classification model) as a feature extractor, combined with a custom classification head trained specifically on worship music instruments.

## Features

- **7 Instrument Categories**: Classifies guitar, bass, keyboard, strings, brass, reeds, and vocals
- **Transfer Learning**: Leverages YAMNet's powerful audio embeddings
- **Fast Inference**: Processes audio files in seconds
- **Batch Processing**: Handle multiple files at once
- **Easy Dataset Management**: One-time extraction, reusable splits
- **Comprehensive Evaluation**: Confusion matrices, classification reports, and accuracy metrics
- **TensorBoard Integration**: Visualize training progress
- **Standalone Scripts**: No complex dependencies or external modules

## Instrument Categories

The model classifies instruments into 7 categories:

| Category | Includes | Examples |
|----------|----------|----------|
| **Guitar** | Acoustic & Electric Guitars | Rhythm guitar, lead guitar |
| **Bass** | Bass Guitars | Electric bass, acoustic bass |
| **Keyboard** | Piano, Organ, Synth, Mallet | Grand piano, Hammond organ, synthesizers |
| **String** | Orchestral Strings | Violin, cello, viola |
| **Brass** | Brass Instruments | Trumpet, trombone, French horn |
| **Reed** | Woodwind Instruments | Saxophone, flute, clarinet |
| **Vocal** | Voice | Lead vocals, backing vocals, choir |

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
git clone https://github.com/yourusername/worship-flow.git
cd worship-flow
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
python nsynth_extractor.py \
    --nsynth_dir ./nsynth-train \
    --output_dir ./nsynth-splits \
    --train_samples 10000 \
    --val_samples 1000 \
    --test_samples 1000
```

### Train the Model (30-60 minutes)

```bash
python train_standalone.py \
    --splits_dir ./nsynth-splits \
    --output_dir ./models/worship_flow \
    --epochs 30 \
    --batch_size 32
```

### Run Inference

```bash
python worship_flow_predictor.py \
    --model ./models/worship_flow/worship_flow_final.keras \
    --config ./models/worship_flow/training_results.json \
    --audio your_audio_file.wav \
    --top_k 3
```

## Detailed Workflow

### Step 1: Dataset Extraction

The NSynth dataset is large (73GB) and takes time to process. We extract and organize it **once**, then reuse the organized splits for training.

```bash
python nsynth_extractor.py \
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
python train_standalone.py \
    --splits_dir ./nsynth-splits \
    --output_dir ./models/worship_flow \
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
models/worship_flow/
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
tensorboard --logdir ./models/worship_flow/logs
```
Then open http://localhost:6006 in your browser.

### Step 3: Inference / Prediction

Use the trained model to classify instruments in new audio files:

#### Single File Prediction

```bash
python worship_flow_predictor.py \
    --model ./models/worship_flow/worship_flow_final.keras \
    --config ./models/worship_flow/training_results.json \
    --audio song.wav \
    --top_k 3
```

**Output:**
```
SINGLE FILE PREDICTION
================================================================================
File: song.wav

Predictions:
  1. guitar        87.32% ████████████████████████████████████
  2. keyboard      8.15%  ███
  3. bass          3.21%  █
```

#### Batch Prediction

Create a text file with audio paths (one per line):

```txt
# audio_list.txt
songs/song1.wav
songs/song2.wav
songs/song3.wav
```

Run batch prediction:

```bash
python worship_flow_predictor.py \
    --model ./models/worship_flow/worship_flow_final.keras \
    --config ./models/worship_flow/training_results.json \
    --audio_list audio_list.txt \
    --top_k 3 \
    --output predictions.json
```

#### Evaluate on Test Set

```bash
python worship_flow_predictor.py \
    --model ./models/worship_flow/worship_flow_final.keras \
    --config ./models/worship_flow/training_results.json \
    --evaluate_split ./nsynth-splits \
    --split_name test \
    --output test_results.json
```

## Project Structure

```
worship-flow/
│
├── README.md                      # This file
├── requirements.txt               # Python dependencies
│
├── nsynth_extractor.py           # Dataset extraction script
├── train_standalone.py           # Training script (standalone)
├── worship_flow_predictor.py     # Inference script
│
├── dataset_loader.py             # (Optional) Modular dataset loader
├── train_worship_flow.py         # (Optional) Modular training script
│
├── nsynth-train/                 # Downloaded NSynth dataset
│   ├── audio/
│   └── examples.json
│
├── nsynth-splits/                # Organized dataset splits
│   ├── train/
│   ├── validation/
│   ├── test/
│   └── config.json
│
└── models/                       # Trained models
    └── worship_flow/
        ├── worship_flow_final.keras
        ├── training_results.json
        └── ...
```

## Usage Examples

### Example 1: Training with Custom Parameters

```bash
python train_standalone.py \
    --splits_dir ./nsynth-splits \
    --output_dir ./models/my_custom_model \
    --epochs 50 \
    --batch_size 64 \
    --learning_rate 0.0005
```

### Example 2: Using Smaller Dataset for Testing

```bash
# Extract smaller dataset for quick testing
python nsynth_extractor.py \
    --nsynth_dir ./nsynth-train \
    --output_dir ./nsynth-splits-small \
    --train_samples 1000 \
    --val_samples 100 \
    --test_samples 100

# Train quickly
python train_standalone.py \
    --splits_dir ./nsynth-splits-small \
    --output_dir ./models/test_model \
    --epochs 10 \
    --batch_size 32
```

### Example 3: Python API Usage

```python
from worship_flow_predictor import WorshipFlowPredictor

# Initialize predictor
predictor = WorshipFlowPredictor(
    model_path='./models/worship_flow/worship_flow_final.keras',
    config_path='./models/worship_flow/training_results.json'
)

# Predict single file
results = predictor.predict('audio.wav', top_k=3)

for i, pred in enumerate(results, 1):
    print(f"{i}. {pred['instrument']}: {pred['confidence']:.2%}")

# Predict multiple files
audio_files = ['song1.wav', 'song2.wav', 'song3.wav']
batch_results = predictor.predict_batch(audio_files, top_k=3)

for audio, results in zip(audio_files, batch_results):
    print(f"\n{audio}:")
    for pred in results[:3]:
        print(f"  - {pred['instrument']}: {pred['confidence']:.2%}")
```

### Example 4: Evaluate Custom Dataset

```python
from worship_flow_predictor import WorshipFlowPredictor

predictor = WorshipFlowPredictor(
    model_path='./models/worship_flow/worship_flow_final.keras',
    config_path='./models/worship_flow/training_results.json'
)

# Evaluate on test split
results = predictor.evaluate_on_split(
    split_dir='./nsynth-splits',
    split_name='test'
)

print(f"Test Accuracy: {results['accuracy']:.2%}")
```

## Model Performance

### Expected Performance (10K training samples)

| Metric | Value |
|--------|-------|
| Training Accuracy | ~85-90% |
| Validation Accuracy | ~60-70% |
| Test Accuracy | ~60-70% |
| Training Time | 30-60 minutes (GPU) |
| Inference Time | <1 second per file |

### Performance Tips

**For Better Accuracy:**
- Increase training samples (20K-50K)
- Train for more epochs (50-100)
- Use data augmentation
- Fine-tune learning rate

**For Faster Training:**
- Use GPU (NVIDIA with CUDA support)
- Decrease batch size if out of memory
- Use smaller dataset for testing

**For Faster Inference:**
- Batch multiple predictions together
- Use GPU if available
- Pre-extract features for repeated predictions

## Troubleshooting

### Common Issues

**Issue: "No module named 'dataset_loader'"**
- **Solution**: Use `train_standalone.py` instead, which has everything built-in

**Issue: Out of memory during training**
- **Solution**: Reduce batch size: `--batch_size 16` or `--batch_size 8`

**Issue: Training is very slow**
- **Solution**: Use GPU or reduce training samples for testing

**Issue: Low accuracy**
- **Solution**: Increase training samples and epochs, check data quality

**Issue: "Config not found" error**
- **Solution**: Ensure you ran `nsynth_extractor.py` first to create organized splits

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
git clone https://github.com/yourusername/worship-flow.git
cd worship-flow
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Running Tests

```bash
# Quick test with small dataset
python nsynth_extractor.py --nsynth_dir ./nsynth-train --output_dir ./test-splits --train_samples 100 --val_samples 10 --test_samples 10
python train_standalone.py --splits_dir ./test-splits --output_dir ./test-models --epochs 5
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [NSynth Dataset](https://magenta.tensorflow.org/datasets/nsynth) by Google Magenta
- [YAMNet](https://tfhub.dev/google/yamnet/1) by Google Research
- TensorFlow and TensorFlow Hub teams

## Future Enhancements

- [ ] Real-time audio classification
- [ ] Multi-instrument detection (detect multiple instruments in one audio)
- [ ] Web interface for easy predictions
- [ ] Mobile app integration
- [ ] Extended instrument categories
- [ ] Audio segmentation and timestamping
- [ ] Confidence calibration
