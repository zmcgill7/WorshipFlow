"""
Worship Flow - Training Script
==============================

Trains the instrument classifier using pre-extracted NSynth dataset splits.

Usage:
    python train_worship_flow.py --splits_dir ./nsynth-splits \
                                   --output_dir ./models/worship_flow \
                                   --epochs 30 \
                                   --batch_size 32

Author: Worship Flow Team
"""

import os
import json
import argparse
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from pathlib import Path
from datetime import datetime
from dataset_loader import SplitDatasetLoader

# ============================================================================
# CONFIGURATION
# ============================================================================

class TrainingConfig:
    """Training configuration"""
    
    def __init__(self, args):
        # Paths
        self.splits_dir = args.splits_dir
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
        print(f"Splits directory: {self.splits_dir}")
        print(f"Output directory: {self.output_dir}")
        print(f"Batch size: {self.batch_size}")
        print(f"Epochs: {self.epochs}")
        print(f"Learning rate: {self.learning_rate}")
        print("=" * 80 + "\n")

# ============================================================================
# FEATURE EXTRACTION
# ============================================================================

def extract_yamnet_features(audio_batch, yamnet_model):
    """
    Extract YAMNet embeddings from audio batch
    
    Args:
        audio_batch: Batch of audio waveforms
        yamnet_model: YAMNet model
        
    Returns:
        Array of embeddings
    """
    embeddings_list = []
    
    for audio in audio_batch:
        # YAMNet expects 1D audio
        if isinstance(audio, np.ndarray):
            audio_tensor = tf.convert_to_tensor(audio, dtype=tf.float32)
        else:
            audio_tensor = audio
        
        # YAMNet returns (scores, embeddings, spectrogram)
        scores, embeddings, spectrogram = yamnet_model(audio_tensor)
        
        # Average over time dimension to get single embedding vector
        avg_embedding = tf.reduce_mean(embeddings, axis=0)
        embeddings_list.append(avg_embedding.numpy())
    
    return np.array(embeddings_list, dtype=np.float32)

def extract_features_from_split(audio_data, yamnet_model, batch_size=32, split_name=''):
    """
    Extract features from entire split
    
    Args:
        audio_data: Array of audio waveforms
        yamnet_model: YAMNet model
        batch_size: Batch size for processing
        split_name: Name of split for logging
        
    Returns:
        Array of features
    """
    print(f"\nExtracting YAMNet features from {split_name}...")
    features_list = []
    
    num_batches = (len(audio_data) + batch_size - 1) // batch_size
    
    for i in range(0, len(audio_data), batch_size):
        batch = audio_data[i:i+batch_size]
        features_batch = extract_yamnet_features(batch, yamnet_model)
        features_list.append(features_batch)
        
        if (i // batch_size + 1) % 10 == 0:
            print(f"  Processed {i+batch_size}/{len(audio_data)} samples...")
    
    features = np.concatenate(features_list, axis=0)
    print(f"{split_name} features shape: {features.shape}")
    
    return features

# ============================================================================
# MODEL DEFINITION
# ============================================================================

def create_worship_flow_model(num_classes):
    """
    Create classification model for YAMNet embeddings
    
    Args:
        num_classes: Number of instrument classes
        
    Returns:
        Keras model
    """
    # Input is YAMNet embedding (1024 dimensions)
    inputs = tf.keras.Input(shape=(1024,), dtype=tf.float32, name='yamnet_embedding')
    
    # Classification head
    x = tf.keras.layers.Dense(256, activation='relu', name='dense1')(inputs)
    x = tf.keras.layers.Dropout(0.5, name='dropout1')(x)
    x = tf.keras.layers.Dense(128, activation='relu', name='dense2')(x)
    x = tf.keras.layers.Dropout(0.3, name='dropout2')(x)
    outputs = tf.keras.layers.Dense(num_classes, activation='softmax', name='output')(x)
    
    model = tf.keras.Model(inputs=inputs, outputs=outputs, name='worship_flow_model')
    
    return model

# ============================================================================
# TRAINING PIPELINE
# ============================================================================

def train_worship_flow(config):
    """
    Main training pipeline
    
    Args:
        config: TrainingConfig object
    """
    
    # Load dataset splits
    print("\n" + "=" * 80)
    print("LOADING DATASET")
    print("=" * 80)
    
    loader = SplitDatasetLoader(config.splits_dir, config.sample_rate)
    
    # Load audio data
    X_train, y_train = loader.load_split('train')
    X_val, y_val = loader.load_split('validation')
    X_test, y_test = loader.load_split('test')
    
    num_classes = len(loader.instruments)
    
    print(f"\nDataset loaded:")
    print(f"  Train: {X_train.shape}")
    print(f"  Val:   {X_val.shape}")
    print(f"  Test:  {X_test.shape}")
    print(f"  Classes: {num_classes} ({', '.join(loader.instruments)})")
    
    # Load YAMNet for feature extraction
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
    print("CREATING MODEL")
    print("=" * 80)
    
    model = create_worship_flow_model(num_classes)
    model.summary()
    
    # Compile model
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=config.learning_rate),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # Callbacks
    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            filepath=os.path.join(config.checkpoint_dir, 'best_model.keras'),
            save_best_only=True,
            monitor='val_accuracy',
            mode='max',
            verbose=1
        ),
        tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=8,
            restore_best_weights=True,
            verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=4,
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
    
    # Evaluate on validation set
    print("\n" + "=" * 80)
    print("VALIDATION SET EVALUATION")
    print("=" * 80)
    val_loss, val_acc = model.evaluate(val_ds)
    print(f"Validation accuracy: {val_acc:.4f}")
    print(f"Validation loss: {val_loss:.4f}")
    
    # Evaluate on test set
    print("\n" + "=" * 80)
    print("TEST SET EVALUATION")
    print("=" * 80)
    test_loss, test_acc = model.evaluate(test_ds)
    print(f"Test accuracy: {test_acc:.4f}")
    print(f"Test loss: {test_loss:.4f}")
    
    # Save final model
    model_path = os.path.join(config.output_dir, 'worship_flow_final.keras')
    model.save(model_path)
    print(f"\nModel saved to: {model_path}")
    
    # Save training configuration and results
    results = {
        'instruments': loader.instruments,
        'sample_rate': config.sample_rate,
        'num_classes': num_classes,
        'train_samples': len(X_train),
        'val_samples': len(X_val),
        'test_samples': len(X_test),
        'batch_size': config.batch_size,
        'epochs': config.epochs,
        'learning_rate': config.learning_rate,
        'val_accuracy': float(val_acc),
        'val_loss': float(val_loss),
        'test_accuracy': float(test_acc),
        'test_loss': float(test_loss),
        'training_date': datetime.now().isoformat(),
        'best_epoch': len(history.history['loss']) - config.epochs // 4,  # Approximate
    }
    
    results_path = os.path.join(config.output_dir, 'training_results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Training results saved to: {results_path}")
    
    # Save confusion matrix data
    print("\nGenerating predictions for confusion matrix...")
    y_pred = model.predict(test_ds)
    y_pred_classes = np.argmax(y_pred, axis=1)
    
    from sklearn.metrics import confusion_matrix, classification_report
    
    cm = confusion_matrix(y_test, y_pred_classes)
    report = classification_report(
        y_test, y_pred_classes,
        target_names=loader.instruments,
        output_dict=True
    )
    
    # Save confusion matrix and report
    eval_results = {
        'confusion_matrix': cm.tolist(),
        'classification_report': report,
        'instruments': loader.instruments
    }
    
    eval_path = os.path.join(config.output_dir, 'evaluation_results.json')
    with open(eval_path, 'w') as f:
        json.dump(eval_results, f, indent=2)
    
    print(f"Evaluation results saved to: {eval_path}")
    
    # Print classification report
    print("\n" + "=" * 80)
    print("CLASSIFICATION REPORT")
    print("=" * 80)
    print(classification_report(
        y_test, y_pred_classes,
        target_names=loader.instruments
    ))
    
    print("\n" + "=" * 80)
    print("TRAINING COMPLETE!")
    print("=" * 80)
    print(f"\nOutput directory: {config.output_dir}")
    print(f"  ├── worship_flow_final.keras (trained model)")
    print(f"  ├── training_results.json (metrics)")
    print(f"  ├── evaluation_results.json (confusion matrix)")
    print(f"  ├── training_log.csv (epoch logs)")
    print(f"  ├── checkpoints/ (best model)")
    print(f"  └── logs/ (TensorBoard logs)")
    
    print("\nTo use the model for inference:")
    print(f"""
from worship_flow_predictor import WorshipFlowPredictor

predictor = WorshipFlowPredictor(
    model_path='{model_path}',
    config_path='{results_path}'
)
results = predictor.predict('path/to/audio.wav')
print(results)
    """)
    
    print("\nTo view training logs with TensorBoard:")
    print(f"tensorboard --logdir {os.path.join(config.output_dir, 'logs')}")
    
    return model, history, results

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Train Worship Flow instrument classifier'
    )
    
    parser.add_argument(
        '--splits_dir',
        type=str,
        required=True,
        help='Path to pre-extracted dataset splits directory'
    )
    
    parser.add_argument(
        '--output_dir',
        type=str,
        default='./models/worship_flow',
        help='Path to output directory for model and results (default: ./models/worship_flow)'
    )
    
    parser.add_argument(
        '--batch_size',
        type=int,
        default=32,
        help='Batch size for training (default: 32)'
    )
    
    parser.add_argument(
        '--epochs',
        type=int,
        default=30,
        help='Number of training epochs (default: 30)'
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
    
    # Train model
    model, history, results = train_worship_flow(config)

if __name__ == '__main__':
    main()