import os
import json
import numpy as np
import librosa
import tensorflow as tf
import tensorflow_hub as hub
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
from datetime import datetime

# ============================================================================
# FEATURE EXTRACTION
# ============================================================================

def load_audio(audio_path: str, sample_rate: int = 16000, duration: float = 4.0) -> np.ndarray:
    """
    Load and preprocess audio file

    Args:
        audio_path: Path to audio file
        sample_rate: Target sample rate
        duration: Duration in seconds

    Returns:
        Normalized audio waveform
    """
    try:
        waveform, sr = librosa.load(
            audio_path,
            sr=sample_rate,
            duration=duration,
            mono=True
        )

        # Ensure correct length
        target_length = int(duration * sample_rate)
        if len(waveform) < target_length:
            waveform = np.pad(waveform, (0, target_length - len(waveform)))
        else:
            waveform = waveform[:target_length]

        # Normalize
        waveform = waveform / (np.max(np.abs(waveform)) + 1e-8)

        return waveform

    except Exception as e:
        raise ValueError(f"Error loading audio from {audio_path}: {e}")


def extract_yamnet_embedding(audio: np.ndarray, yamnet_model) -> np.ndarray:
    """
    Extract YAMNet embedding from audio

    Args:
        audio: Audio waveform
        yamnet_model: Loaded YAMNet model

    Returns:
        1024-dimensional embedding vector
    """
    audio_tensor = tf.convert_to_tensor(audio, dtype=tf.float32)

    # YAMNet returns (scores, embeddings, spectrogram)
    scores, embeddings, spectrogram = yamnet_model(audio_tensor)

    # Average over time to get single embedding vector
    avg_embedding = tf.reduce_mean(embeddings, axis=0)

    return avg_embedding.numpy()


# ============================================================================
# INFERENCE ENGINE
# ============================================================================

class InstrumentClassifier:
    """Multi-label instrument classifier for inference"""

    def __init__(self, model_path: str, results_path: str, threshold: float = 0.5, yamnet_path: str | None = None):
        """
        Initialize classifier

        Args:
            model_path: Path to trained Keras model
            results_path: Path to training_results.json
            threshold: Classification threshold (default: 0.5)
        """
        print("Initializing Worship Flow Instrument Classifier...")
        print(f"Model: {model_path}")
        print(f"Results: {results_path}")

        # Load model
        if not os.path.exists(model_path):
            raise ValueError(f"Model not found: {model_path}")

        self.model = tf.keras.models.load_model(model_path)
        print("✓ Model loaded")

        # Load metadata
        if not os.path.exists(results_path):
            raise ValueError(f"Results file not found: {results_path}")

        with open(results_path, 'r') as f:
            self.results = json.load(f)

        self.instruments = self.results['instruments']
        self.num_classes = self.results['num_classes']
        self.sample_rate = self.results['sample_rate']
        self.optimal_threshold = self.results.get('optimal_threshold', 0.5)

        # Use provided threshold or optimal from training
        self.threshold = threshold if threshold is not None else self.optimal_threshold

        print(f"✓ Metadata loaded")
        print(f"  Instruments: {self.num_classes} classes")
        print(f"  Sample rate: {self.sample_rate} Hz")
        print(f"  Threshold: {self.threshold:.3f}")

        # Load YAMNet
        print("\nLoading YAMNet for feature extraction...")
        self.yamnet_path = yamnet_path or 'https://tfhub.dev/google/yamnet/1'
        self.yamnet_model = hub.load(self.yamnet_path)
        print("✓ YAMNet loaded")

        print("\nClassifier ready!\n")

    def predict_file(self, audio_path: str, return_probabilities: bool = False) -> Dict:
        """
        Predict instruments in a single audio file

        Args:
            audio_path: Path to audio file
            return_probabilities: Whether to return probabilities

        Returns:
            Dictionary with predictions
        """
        # Load audio
        audio = load_audio(audio_path, self.sample_rate)

        # Extract features
        embedding = extract_yamnet_embedding(audio, self.yamnet_model)
        embedding = np.expand_dims(embedding, axis=0)  # Add batch dimension

        # Predict
        probabilities = self.model.predict(embedding, verbose=0)[0]

        # Apply threshold
        predictions = (probabilities >= self.threshold).astype(int)

        # Get detected instruments
        detected_instruments = [
            self.instruments[i] for i in range(self.num_classes)
            if predictions[i] == 1
        ]

        result = {
            'file': os.path.basename(audio_path),
            'detected_instruments': detected_instruments,
            'num_instruments': len(detected_instruments),
            'threshold': self.threshold
        }

        if return_probabilities:
            result['probabilities'] = {
                instrument: float(prob)
                for instrument, prob in zip(self.instruments, probabilities)
            }
            result['predictions'] = {
                instrument: int(pred)
                for instrument, pred in zip(self.instruments, predictions)
            }

        return result

    def predict_batch(self, audio_paths: List[str],
                     return_probabilities: bool = False) -> List[Dict]:
        """
        Predict instruments for multiple audio files

        Args:
            audio_paths: List of audio file paths
            return_probabilities: Whether to return probabilities

        Returns:
            List of prediction dictionaries
        """
        results = []

        print(f"Processing {len(audio_paths)} files...")

        for i, audio_path in enumerate(audio_paths, 1):
            try:
                result = self.predict_file(audio_path, return_probabilities)
                results.append(result)

                print(f"[{i}/{len(audio_paths)}] {result['file']}: "
                      f"{result['num_instruments']} instruments detected")

            except Exception as e:
                print(f"[{i}/{len(audio_paths)}] Error processing {audio_path}: {e}")
                results.append({
                    'file': os.path.basename(audio_path),
                    'error': str(e)
                })

        return results

    def predict_directory(self, directory: str,
                         extensions: List[str] = None,
                         return_probabilities: bool = False) -> List[Dict]:
        """
        Predict instruments for all audio files in a directory

        Args:
            directory: Directory path
            extensions: Audio file extensions (default: ['.mp3', '.wav', '.flac', '.m4a'])
            return_probabilities: Whether to return probabilities

        Returns:
            List of prediction dictionaries
        """
        if extensions is None:
            extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg']

        # Find all audio files
        audio_files = []
        for ext in extensions:
            audio_files.extend(Path(directory).glob(f"*{ext}"))
            audio_files.extend(Path(directory).glob(f"*{ext.upper()}"))

        audio_files = sorted(set(str(f) for f in audio_files))

        if not audio_files:
            print(f"No audio files found in {directory}")
            return []

        print(f"Found {len(audio_files)} audio files")

        return self.predict_batch(audio_files, return_probabilities)


# ============================================================================
# RESULT FORMATTING
# ============================================================================

def format_results_table(results: List[Dict]) -> None:
    """Print results in table format"""
    print("\n" + "=" * 80)
    print("PREDICTION RESULTS")
    print("=" * 80)

    for i, result in enumerate(results, 1):
        if 'error' in result:
            print(f"\n{i}. {result['file']}")
            print(f"   ERROR: {result['error']}")
            continue

        print(f"\n{i}. {result['file']}")
        print(f"   Detected: {result['num_instruments']} instruments")

        if result['detected_instruments']:
            print(f"   Instruments: {', '.join(result['detected_instruments'])}")
        else:
            print(f"   Instruments: None detected")

        if 'probabilities' in result:
            print(f"\n   All Probabilities:")
            sorted_probs = sorted(
                result['probabilities'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            for instrument, prob in sorted_probs:
                marker = "✓" if result['predictions'][instrument] == 1 else " "
                print(f"     [{marker}] {instrument:<20} {prob:.3f}")


def save_results_csv(results: List[Dict], output_path: str) -> None:
    """Save results to CSV file"""

    # Prepare data
    rows = []
    for result in results:
        if 'error' in result:
            rows.append({
                'file': result['file'],
                'num_instruments': None,
                'instruments': None,
                'error': result['error']
            })
        else:
            rows.append({
                'file': result['file'],
                'num_instruments': result['num_instruments'],
                'instruments': ', '.join(result['detected_instruments']),
                'error': None
            })

            # Add probabilities if available
            if 'probabilities' in result:
                for instrument, prob in result['probabilities'].items():
                    rows[-1][f'prob_{instrument}'] = prob

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"\n✓ Results saved to: {output_path}")


def save_results_json(results: List[Dict], output_path: str) -> None:
    """Save results to JSON file"""

    output_data = {
        'timestamp': datetime.now().isoformat(),
        'num_files': len(results),
        'results': results
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✓ Results saved to: {output_path}")


if __name__ == "__main__":
    # Default Configuration
    model_path = 'training/models/worship_flow_multilabel/checkpoints/best_model.keras'
    results_path = 'training/models/worship_flow_multilabel/training_results.json'
    audio_path = './music.mp3'  # Set to an empty string if processing a directory
    audio_dir = ''  # Set to a directory path if processing multiple files
    threshold = 0.5  # Classification threshold
    return_probabilities = True  # Whether to include probability scores in output
    output_csv = './inference_results.csv'  
    output_json = './inference_results.json'
    extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg']


    # Initialize classifier
    classifier = InstrumentClassifier(
        model_path=model_path,
        results_path=results_path,
        threshold=threshold
    )

    # Run inference
    if audio_path:
        # Single file
        result = classifier.predict_file(
            audio_path,
            return_probabilities=return_probabilities
        )
        results = [result]
    elif audio_dir:
        # Directory
        results = classifier.predict_directory(
            audio_dir,
            extensions=extensions,
            return_probabilities=return_probabilities
        )
    else:
        print("Error: Either 'audio_path' or 'audio_dir' must be provided.")
        results = []

    # Display results
    if results:
        format_results_table(results)

    # Save results
    if output_csv:
        save_results_csv(results, output_csv)

    if output_json:
        save_results_json(results, output_json)

    # Summary
    if results and any('error' not in r for r in results):
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        successful = sum(1 for r in results if 'error' not in r)
        failed = len(results) - successful

        print(f"Total files processed: {len(results)}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")

        if successful > 0:
            avg_instruments = np.mean([
                r['num_instruments'] for r in results if 'error' not in r
            ])
            print(f"\nAverage instruments detected: {avg_instruments:.2f}")

            # Instrument frequency
            instrument_counts = {}
            for result in results:
                if 'error' not in result:
                    for instrument in result['detected_instruments']:
                        instrument_counts[instrument] = instrument_counts.get(instrument, 0) + 1

            if instrument_counts:
                print(f"\nInstrument frequency:")
                for instrument, count in sorted(
                    instrument_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                ):
                    percentage = (count / successful) * 100
                    print(f"  {instrument:<20} {count:3d} ({percentage:5.1f}%)")
