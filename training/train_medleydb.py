"""
Worship Flow - Multi-Label Training Script for MedleyDB
========================================================
Author: Ashwin Raikar

Trains a multi-label instrument classifier on MedleyDB dataset.

Usage:
    python train_medleydb.py \
        --data_dir ./medleydb-multilabel \
        --output_dir ./models/worship_flow_multilabel \
        --epochs 50 \
        --batch_size 32 \
        --learning_rate 0.001

Requirements:
    pip install tensorflow tensorflow-hub librosa numpy scikit-learn
"""

import os
import json
import argparse
import numpy as np
import librosa
import tensorflow as tf
import tensorflow_hub as hub
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# ============================================================================
# DATASET LOADER
# ============================================================================

class MultiLabelDatasetLoader:
    """Load MedleyDB multi-label dataset"""
    
    def __init__(self, data_dir, sample_rate=16000):
        self.data_dir = Path(data_dir)
        self.sample_rate = sample_rate
        
        # Load config
        config_path = self.data_dir / 'config.json'
        if not config_path.exists():
            raise ValueError(f"Config not found: {config_path}")
        
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.instruments = self.config['instruments']
        self.num_classes = len(self.instruments)
        
        print(f"Loaded dataset config from {data_dir}")
        print(f"Instruments ({self.num_classes}): {', '.join(self.instruments)}")
        print(f"Multi-label: {self.config.get('multilabel', False)}")
    
    def load_split(self, split_name):
        """Load a split (train/validation/test)"""
        split_dir = self.data_dir / split_name
        metadata_path = split_dir / 'metadata.json'
        
        if not metadata_path.exists():
            raise ValueError(f"Split metadata not found: {metadata_path}")
        
        # Load metadata
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        print(f"\nLoading {split_name} split...")
        print(f"  Samples: {metadata['num_samples']:,}")
        
        file_list = metadata['files']
        
        # Load audio and labels
        audio_data = []
        labels = []
        
        for file_info in tqdm(file_list, desc=f"Loading {split_name}"):
            file_path = self.data_dir / file_info['path']
            
            try:
                # Load audio
                waveform, sr = librosa.load(
                    str(file_path),
                    sr=self.sample_rate,
                    duration=4.0,
                    mono=True
                )
                
                # Ensure correct length
                target_length = 4 * self.sample_rate
                if len(waveform) < target_length:
                    waveform = np.pad(waveform, (0, target_length - len(waveform)))
                else:
                    waveform = waveform[:target_length]
                
                # Normalize
                waveform = waveform / (np.max(np.abs(waveform)) + 1e-8)
                
                audio_data.append(waveform)
                
                # Get label (already in multi-hot format)
                label = np.array(file_info['label'], dtype=np.float32)
                labels.append(label)
                
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        audio_data = np.array(audio_data, dtype=np.float32)
        labels = np.array(labels, dtype=np.float32)
        
        # Print label statistics
        print(f"\n{split_name.capitalize()} set statistics:")
        print(f"  Shape: {audio_data.shape}")
        print(f"  Labels shape: {labels.shape}")
        print(f"  Avg instruments per sample: {np.mean(np.sum(labels, axis=1)):.2f}")
        
        return audio_data, labels

# ============================================================================
# FEATURE EXTRACTION
# ============================================================================

def extract_yamnet_features(audio_batch, yamnet_model):
    """Extract YAMNet embeddings from audio batch"""
    embeddings_list = []
    
    for audio in audio_batch:
        # YAMNet expects 1D audio
        audio_tensor = tf.convert_to_tensor(audio, dtype=tf.float32)
        
        # YAMNet returns (scores, embeddings, spectrogram)
        scores, embeddings, spectrogram = yamnet_model(audio_tensor)
        
        # Average over time to get single embedding vector
        avg_embedding = tf.reduce_mean(embeddings, axis=0)
        embeddings_list.append(avg_embedding.numpy())
    
    return np.array(embeddings_list, dtype=np.float32)

def extract_features_from_split(audio_data, yamnet_model, batch_size=32, split_name=''):
    """Extract features from entire split"""
    print(f"\nExtracting YAMNet features from {split_name}...")
    features_list = []
    
    for i in range(0, len(audio_data), batch_size):
        batch = audio_data[i:i+batch_size]
        features_batch = extract_yamnet_features(batch, yamnet_model)
        features_list.append(features_batch)
        
        if (i // batch_size + 1) % 10 == 0:
            print(f"  Processed {min(i+batch_size, len(audio_data))}/{len(audio_data)} samples...")
    
    features = np.concatenate(features_list, axis=0)
    print(f"{split_name} features shape: {features.shape}")
    
    return features

# ============================================================================
# MODEL DEFINITION
# ============================================================================

def create_multilabel_model(num_classes, input_dim=1024):
    """
    Create multi-label classification model
    
    Args:
        num_classes: Number of instrument classes
        input_dim: Dimension of input features (YAMNet = 1024)
    
    Returns:
        Keras model
    """
    inputs = tf.keras.Input(shape=(input_dim,), dtype=tf.float32, name='yamnet_embedding')
    
    # Feature processing
    x = tf.keras.layers.Dense(512, activation='relu', name='dense1')(inputs)
    x = tf.keras.layers.BatchNormalization(name='bn1')(x)
    x = tf.keras.layers.Dropout(0.5, name='dropout1')(x)
    
    x = tf.keras.layers.Dense(256, activation='relu', name='dense2')(x)
    x = tf.keras.layers.BatchNormalization(name='bn2')(x)
    x = tf.keras.layers.Dropout(0.4, name='dropout2')(x)
    
    x = tf.keras.layers.Dense(128, activation='relu', name='dense3')(x)
    x = tf.keras.layers.Dropout(0.3, name='dropout3')(x)
    
    # Multi-label output: sigmoid activation for independent predictions
    outputs = tf.keras.layers.Dense(num_classes, activation='sigmoid', name='output')(x)
    
    model = tf.keras.Model(inputs=inputs, outputs=outputs, name='worship_flow_multilabel')
    
    return model

# ============================================================================
# TRAINING CONFIGURATION
# ============================================================================

class TrainingConfig:
    """Training configuration"""
    
    def __init__(self, args):
        self.data_dir = args.data_dir
        self.output_dir = args.output_dir
        self.checkpoint_dir = os.path.join(args.output_dir, 'checkpoints')
        
        # YAMNet
        self.yamnet_model_handle = 'https://tfhub.dev/google/yamnet/1'
        self.sample_rate = 16000
        
        # Training parameters
        self.batch_size = args.batch_size
        self.epochs = args.epochs
        self.learning_rate = args.learning_rate
        
        # Create directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        
        print("\n" + "=" * 80)
        print("TRAINING CONFIGURATION")
        print("=" * 80)
        print(f"Data directory: {self.data_dir}")
        print(f"Output directory: {self.output_dir}")
        print(f"Batch size: {self.batch_size}")
        print(f"Epochs: {self.epochs}")
        print(f"Learning rate: {self.learning_rate}")
        print("=" * 80 + "\n")

# ============================================================================
# TRAINING PIPELINE
# ============================================================================

def train_multilabel_model(config):
    """Main training pipeline for multi-label classification"""
    
    # Load dataset
    print("\n" + "=" * 80)
    print("LOADING DATASET")
    print("=" * 80)
    
    loader = MultiLabelDatasetLoader(config.data_dir, config.sample_rate)
    
    X_train, y_train = loader.load_split('train')
    X_val, y_val = loader.load_split('validation')
    X_test, y_test = loader.load_split('test')
    
    num_classes = loader.num_classes
    
    print(f"\nDataset loaded:")
    print(f"  Train: {X_train.shape}, Labels: {y_train.shape}")
    print(f"  Val:   {X_val.shape}, Labels: {y_val.shape}")
    print(f"  Test:  {X_test.shape}, Labels: {y_test.shape}")
    print(f"  Classes: {num_classes} ({', '.join(loader.instruments)})")
    
    # Load YAMNet
    print("\n" + "=" * 80)
    print("LOADING YAMNET FOR FEATURE EXTRACTION")
    print("=" * 80)
    yamnet_model = hub.load(config.yamnet_model_handle)
    print("YAMNet loaded successfully!")
    
    # Extract features
    print("\n" + "=" * 80)
    print("EXTRACTING FEATURES")
    print("=" * 80)
    
    X_train_features = extract_features_from_split(
        X_train, yamnet_model, config.batch_size, 'training set'
    )
    X_val_features = extract_features_from_split(
        X_val, yamnet_model, config.batch_size, 'validation set'
    )
    X_test_features = extract_features_from_split(
        X_test, yamnet_model, config.batch_size, 'test set'
    )
    
    # Create TensorFlow datasets
    train_ds = tf.data.Dataset.from_tensor_slices((X_train_features, y_train))
    train_ds = train_ds.shuffle(1000).batch(config.batch_size).prefetch(tf.data.AUTOTUNE)
    
    val_ds = tf.data.Dataset.from_tensor_slices((X_val_features, y_val))
    val_ds = val_ds.batch(config.batch_size).prefetch(tf.data.AUTOTUNE)
    
    test_ds = tf.data.Dataset.from_tensor_slices((X_test_features, y_test))
    test_ds = test_ds.batch(config.batch_size).prefetch(tf.data.AUTOTUNE)
    
    # Create model
    print("\n" + "=" * 80)
    print("CREATING MULTI-LABEL MODEL")
    print("=" * 80)
    
    model = create_multilabel_model(num_classes)
    model.summary()
    
    # Compile with multi-label loss
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=config.learning_rate),
        loss='binary_crossentropy',  # Multi-label loss
        metrics=[
            'binary_accuracy',
            tf.keras.metrics.AUC(name='auc', multi_label=True),
            tf.keras.metrics.Precision(name='precision'),
            tf.keras.metrics.Recall(name='recall')
        ]
    )
    
    # Callbacks
    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            filepath=os.path.join(config.checkpoint_dir, 'best_model.keras'),
            save_best_only=True,
            monitor='val_auc',
            mode='max',
            verbose=1
        ),
        tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True,
            verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-6,
            verbose=1
        ),
        tf.keras.callbacks.CSVLogger(
            os.path.join(config.output_dir, 'training_log.csv')
        ),
        tf.keras.callbacks.TensorBoard(
            log_dir=os.path.join(config.output_dir, 'logs'),
            histogram_freq=1
        )
    ]
    
    # Train
    print("\n" + "=" * 80)
    print("TRAINING")
    print("=" * 80)
    
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=config.epochs,
        callbacks=callbacks,
        verbose=1
    )
    
    # Evaluate
    print("\n" + "=" * 80)
    print("EVALUATION")
    print("=" * 80)
    
    val_results = model.evaluate(val_ds, verbose=0)
    test_results = model.evaluate(test_ds, verbose=0)
    
    print(f"\nValidation Results:")
    for name, value in zip(model.metrics_names, val_results):
        print(f"  {name}: {value:.4f}")
    
    print(f"\nTest Results:")
    for name, value in zip(model.metrics_names, test_results):
        print(f"  {name}: {value:.4f}")
    
    # Detailed evaluation
    print("\n" + "=" * 80)
    print("DETAILED MULTI-LABEL EVALUATION")
    print("=" * 80)
    
    y_pred_probs = model.predict(test_ds)
    
    # Find optimal threshold
    thresholds = np.arange(0.1, 0.9, 0.05)
    best_threshold = 0.5
    best_f1 = 0
    
    from sklearn.metrics import f1_score
    
    for threshold in thresholds:
        y_pred_binary = (y_pred_probs >= threshold).astype(int)
        f1 = f1_score(y_test, y_pred_binary, average='samples', zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold
    
    print(f"\nOptimal threshold: {best_threshold:.2f} (F1={best_f1:.4f})")
    
    # Use optimal threshold
    y_pred_binary = (y_pred_probs >= best_threshold).astype(int)
    
    # Multi-label metrics
    from sklearn.metrics import (
        hamming_loss, jaccard_score, precision_score, 
        recall_score, f1_score, multilabel_confusion_matrix
    )
    
    h_loss = hamming_loss(y_test, y_pred_binary)
    jaccard = jaccard_score(y_test, y_pred_binary, average='samples', zero_division=0)
    
    print(f"\nOverall Metrics:")
    print(f"  Hamming Loss: {h_loss:.4f}")
    print(f"  Jaccard Score (IoU): {jaccard:.4f}")
    print(f"  Sample-wise F1: {best_f1:.4f}")
    
    # Per-class metrics
    print(f"\n{'Instrument':<15} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support'}")
    print("-" * 65)
    
    per_class_metrics = {}
    
    for i, instrument in enumerate(loader.instruments):
        y_true_class = y_test[:, i]
        y_pred_class = y_pred_binary[:, i]
        
        precision = precision_score(y_true_class, y_pred_class, zero_division=0)
        recall = recall_score(y_true_class, y_pred_class, zero_division=0)
        f1 = f1_score(y_true_class, y_pred_class, zero_division=0)
        support = int(np.sum(y_true_class))
        
        print(f"{instrument:<15} {precision:<12.3f} {recall:<12.3f} {f1:<12.3f} {support}")
        
        per_class_metrics[instrument] = {
            'precision': float(precision),
            'recall': float(recall),
            'f1': float(f1),
            'support': support
        }
    
    # Save model
    model_path = os.path.join(config.output_dir, 'worship_flow_multilabel.keras')
    model.save(model_path)
    print(f"\n✓ Model saved to: {model_path}")
    
    # Save results
    results = {
        'instruments': loader.instruments,
        'num_classes': num_classes,
        'sample_rate': config.sample_rate,
        'train_samples': len(X_train),
        'val_samples': len(X_val),
        'test_samples': len(X_test),
        'batch_size': config.batch_size,
        'epochs': config.epochs,
        'learning_rate': config.learning_rate,
        'optimal_threshold': float(best_threshold),
        'hamming_loss': float(h_loss),
        'jaccard_score': float(jaccard),
        'sample_f1': float(best_f1),
        'per_class_metrics': per_class_metrics,
        'training_date': datetime.now().isoformat()
    }
    
    results_path = os.path.join(config.output_dir, 'training_results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✓ Results saved to: {results_path}")
    
    # Save evaluation results
    eval_results = {
        'confusion_matrices': multilabel_confusion_matrix(y_test, y_pred_binary).tolist(),
        'instruments': loader.instruments,
        'threshold': float(best_threshold),
        'metrics': per_class_metrics
    }
    
    eval_path = os.path.join(config.output_dir, 'evaluation_results.json')
    with open(eval_path, 'w') as f:
        json.dump(eval_results, f, indent=2)
    
    print(f"✓ Evaluation results saved to: {eval_path}")
    
    print("\n" + "=" * 80)
    print("TRAINING COMPLETE!")
    print("=" * 80)
    print(f"\nOutput directory: {config.output_dir}")
    print(f"  ├── worship_flow_multilabel.keras")
    print(f"  ├── training_results.json")
    print(f"  ├── evaluation_results.json")
    print(f"  ├── training_log.csv")
    print(f"  ├── checkpoints/")
    print(f"  └── logs/")
    
    print("\nTo view training logs:")
    print(f"tensorboard --logdir {os.path.join(config.output_dir, 'logs')}")
    
    return model, history, results

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Train multi-label instrument classifier on MedleyDB'
    )
    
    parser.add_argument(
        '--data_dir',
        type=str,
        required=True,
        help='Path to extracted MedleyDB dataset directory'
    )
    
    parser.add_argument(
        '--output_dir',
        type=str,
        default='./models/worship_flow_multilabel',
        help='Output directory for model and results'
    )
    
    parser.add_argument(
        '--batch_size',
        type=int,
        default=32,
        help='Batch size (default: 32)'
    )
    
    parser.add_argument(
        '--epochs',
        type=int,
        default=50,
        help='Number of epochs (default: 50)'
    )
    
    parser.add_argument(
        '--learning_rate',
        type=float,
        default=0.001,
        help='Learning rate (default: 0.001)'
    )
    
    args = parser.parse_args()
    
    # Create config
    config = TrainingConfig(args)
    
    # Train
    model, history, results = train_multilabel_model(config)

if __name__ == '__main__':
    main()