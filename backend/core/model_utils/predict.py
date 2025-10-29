"""
Worship Flow - Inference/Prediction Module
==========================================

Loads trained model and performs instrument detection on audio files.

Usage:
    from worship_flow_predictor import WorshipFlowPredictor
    
    predictor = WorshipFlowPredictor(
        model_path='./models/worship_flow/worship_flow_final.keras',
        config_path='./models/worship_flow/training_results.json'
    )
    
    results = predictor.predict('audio.wav', top_k=3)
    print(results)

Command Line:
    python worship_flow_predictor.py --model ./models/worship_flow/worship_flow_final.keras \
                                      --config ./models/worship_flow/training_results.json \
                                      --audio audio.wav \
                                      --top_k 3
"""

import json
import argparse
import numpy as np
import librosa
import tensorflow as tf
import tensorflow_hub as hub
from pathlib import Path
from typing import List, Dict

# ============================================================================
# PREDICTOR CLASS
# ============================================================================

class WorshipFlowPredictor:
    """Inference class for instrument detection"""
    
    def __init__(self, model_path: str, config_path: str):
        """
        Initialize predictor
        
        Args:
            model_path: Path to trained model (.keras or .h5)
            config_path: Path to training results config JSON
        """
        print("Loading model...")
        self.model = tf.keras.models.load_model(model_path)
        
        print("Loading configuration...")
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.instruments = config['instruments']
        self.sample_rate = config['sample_rate']
        self.num_classes = config['num_classes']
        
        # Load YAMNet for feature extraction
        print("Loading YAMNet for inference...")
        self.yamnet = hub.load('https://tfhub.dev/google/yamnet/1')
        
        print("✓ Model loaded successfully!\n")
        print(f"Instruments: {', '.join(self.instruments)}")
        print(f"Sample rate: {self.sample_rate} Hz")
    
    def _load_audio(self, audio_path: str) -> np.ndarray:
        """
        Load and preprocess audio file
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Preprocessed waveform
        """
        # Load audio
        waveform, sr = librosa.load(audio_path, sr=self.sample_rate, duration=4.0)
        
        # Ensure correct length (pad or truncate)
        target_length = 4 * self.sample_rate
        if len(waveform) < target_length:
            waveform = np.pad(waveform, (0, target_length - len(waveform)))
        else:
            waveform = waveform[:target_length]
        
        # Normalize
        waveform = waveform / (np.max(np.abs(waveform)) + 1e-8)
        
        return waveform
    
    def _extract_features(self, waveform: np.ndarray) -> np.ndarray:
        """
        Extract YAMNet features from waveform
        
        Args:
            waveform: Audio waveform
            
        Returns:
            YAMNet embedding
        """
        # Extract YAMNet features
        scores, embeddings, spectrogram = self.yamnet(waveform)
        
        # Average over time dimension
        avg_embedding = tf.reduce_mean(embeddings, axis=0).numpy()
        
        return avg_embedding
    
    def predict(self, audio_path: str, top_k: int = 1) -> List[Dict]:
        """
        Predict instruments in audio file
        
        Args:
            audio_path: Path to audio file
            top_k: Number of top predictions to return
            
        Returns:
            List of predictions with instrument names and confidence scores
        """
        # Load audio
        waveform = self._load_audio(audio_path)
        
        # Extract features
        features = self._extract_features(waveform)
        
        # Predict
        features_input = np.expand_dims(features, 0)
        predictions = self.model.predict(features_input, verbose=0)[0]
        
        # Get top-k predictions
        top_indices = np.argsort(predictions)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                'instrument': self.instruments[idx],
                'confidence': float(predictions[idx])
            })
        
        return results
    
    def predict_batch(self, audio_paths: List[str], top_k: int = 1) -> List[List[Dict]]:
        """
        Predict instruments for multiple audio files
        
        Args:
            audio_paths: List of paths to audio files
            top_k: Number of top predictions per file
            
        Returns:
            List of prediction results for each file
        """
        results = []
        
        for audio_path in audio_paths:
            try:
                result = self.predict(audio_path, top_k)
                results.append(result)
            except Exception as e:
                print(f"Error processing {audio_path}: {e}")
                results.append([])
        
        return results
    
    def evaluate_on_split(self, split_dir: str, split_name: str = 'test') -> Dict:
        """
        Run inference on all files in a dataset split
        
        Args:
            split_dir: Path to splits directory
            split_name: Name of split ('test', 'validation', etc.)
            
        Returns:
            Dictionary with evaluation results
        """
        from pathlib import Path
        
        split_path = Path(split_dir) / split_name
        metadata_path = split_path / 'metadata.json'
        
        if not metadata_path.exists():
            raise ValueError(f"Metadata not found at {metadata_path}")
        
        # Load metadata
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        print(f"\nRunning inference on {split_name} set...")
        print(f"Total samples: {metadata['num_samples']}")
        
        results = []
        correct = 0
        
        for file_info in metadata['files']:
            file_path = Path(split_dir) / file_info['path']
            true_label = file_info['instrument']
            
            # Predict
            predictions = self.predict(str(file_path), top_k=len(self.instruments))
            predicted_label = predictions[0]['instrument']
            
            # Check if correct
            is_correct = (predicted_label == true_label)
            if is_correct:
                correct += 1
            
            results.append({
                'file': str(file_path),
                'true_label': true_label,
                'predicted_label': predicted_label,
                'confidence': predictions[0]['confidence'],
                'correct': is_correct,
                'all_predictions': predictions
            })
        
        accuracy = correct / len(results)
        
        print(f"\n{split_name.upper()} SET RESULTS:")
        print(f"  Total samples: {len(results)}")
        print(f"  Correct: {correct}")
        print(f"  Incorrect: {len(results) - correct}")
        print(f"  Accuracy: {accuracy:.2%}")
        
        return {
            'split_name': split_name,
            'total_samples': len(results),
            'correct_predictions': correct,
            'accuracy': accuracy,
            'predictions': results
        }

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Predict instruments in audio files using Worship Flow'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        required=True,
        help='Path to trained model (.keras or .h5)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='Path to training results config JSON'
    )
    
    parser.add_argument(
        '--audio',
        type=str,
        help='Path to audio file for prediction'
    )
    
    parser.add_argument(
        '--audio_list',
        type=str,
        help='Path to text file with list of audio files (one per line)'
    )
    
    parser.add_argument(
        '--evaluate_split',
        type=str,
        help='Path to splits directory for evaluation'
    )
    
    parser.add_argument(
        '--split_name',
        type=str,
        default='test',
        help='Name of split to evaluate (default: test)'
    )
    
    parser.add_argument(
        '--top_k',
        type=int,
        default=3,
        help='Number of top predictions to show (default: 3)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Path to save prediction results JSON'
    )
    
    args = parser.parse_args()
    
    # Initialize predictor
    predictor = WorshipFlowPredictor(args.model, args.config)
    
    # Single audio file prediction
    if args.audio:
        print("\n" + "=" * 80)
        print("SINGLE FILE PREDICTION")
        print("=" * 80)
        print(f"File: {args.audio}\n")
        
        results = predictor.predict(args.audio, top_k=args.top_k)
        
        print("Predictions:")
        for i, pred in enumerate(results, 1):
            confidence_bar = '█' * int(pred['confidence'] * 40)
            print(f"  {i}. {pred['instrument']:<12} {pred['confidence']:>6.2%} {confidence_bar}")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to: {args.output}")
    
    # Batch prediction from file list
    elif args.audio_list:
        print("\n" + "=" * 80)
        print("BATCH PREDICTION")
        print("=" * 80)
        
        with open(args.audio_list, 'r') as f:
            audio_paths = [line.strip() for line in f if line.strip()]
        
        print(f"Processing {len(audio_paths)} files...\n")
        
        batch_results = predictor.predict_batch(audio_paths, top_k=args.top_k)
        
        for audio_path, results in zip(audio_paths, batch_results):
            print(f"\n{Path(audio_path).name}:")
            for i, pred in enumerate(results[:3], 1):
                print(f"  {i}. {pred['instrument']:<12} {pred['confidence']:>6.2%}")
        
        if args.output:
            output_data = {
                'files': audio_paths,
                'predictions': batch_results
            }
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"\nResults saved to: {args.output}")
    
    # Evaluate on dataset split
    elif args.evaluate_split:
        print("\n" + "=" * 80)
        print("DATASET EVALUATION")
        print("=" * 80)
        
        eval_results = predictor.evaluate_on_split(
            args.evaluate_split,
            args.split_name
        )
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(eval_results, f, indent=2)
            print(f"\nResults saved to: {args.output}")
    
    else:
        parser.print_help()
        print("\nError: Must provide --audio, --audio_list, or --evaluate_split")

if __name__ == '__main__':
    main()