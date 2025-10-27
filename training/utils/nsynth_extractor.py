"""
NSynth Dataset Extractor and Organizer
======================================

Extracts and organizes NSynth dataset into train/validation/test splits
with configurable sample counts per instrument class.

Usage:
    python nsynth_extractor.py --nsynth_dir ./datasets/nsynth-train \
                                --output_dir ./nsynth-splits \
                                --train_samples 10000 \
                                --val_samples 1000 \
                                --test_samples 1000

Author: Worship Flow Team
"""

import os
import json
import shutil
import argparse
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from tqdm import tqdm

# ============================================================================
# CONFIGURATION
# ============================================================================

# Target instrument families (common in worship music)
TARGET_INSTRUMENTS = [
    'guitar',      # acoustic & electric
    'bass',        # bass guitar
    'keyboard',    # piano, organ, synth
    'string',      # violin, cello
    'brass',       # trumpet, trombone
    'reed',        # saxophone, flute
    'vocal'        # voice
]

# Instrument family mapping from NSynth to our categories
FAMILY_MAPPING = {
    'guitar': ['guitar'],
    'bass': ['bass'],
    'keyboard': ['keyboard', 'mallet'],
    'string': ['string'],
    'brass': ['brass'],
    'reed': ['reed'],
    'vocal': ['vocal']
}

# ============================================================================
# DATASET EXTRACTOR CLASS
# ============================================================================

class NSynthDatasetExtractor:
    """Extract and organize NSynth dataset into splits"""
    
    def __init__(self, nsynth_dir, output_dir, target_instruments=None, family_mapping=None):
        """
        Initialize the extractor
        
        Args:
            nsynth_dir: Path to NSynth dataset directory
            output_dir: Path to output directory for organized splits
            target_instruments: List of target instrument categories
            family_mapping: Dict mapping target categories to NSynth families
        """
        self.nsynth_dir = Path(nsynth_dir)
        self.output_dir = Path(output_dir)
        self.audio_dir = self.nsynth_dir / 'audio'
        self.examples_path = self.nsynth_dir / 'examples.json'
        
        self.target_instruments = target_instruments or TARGET_INSTRUMENTS
        self.family_mapping = family_mapping or FAMILY_MAPPING
        
        # Validate paths
        if not self.nsynth_dir.exists():
            raise ValueError(f"NSynth directory not found: {nsynth_dir}")
        if not self.examples_path.exists():
            raise ValueError(f"examples.json not found: {self.examples_path}")
        if not self.audio_dir.exists():
            raise ValueError(f"Audio directory not found: {self.audio_dir}")
    
    def load_metadata(self):
        """Load NSynth metadata"""
        print(f"Loading metadata from {self.examples_path}...")
        with open(self.examples_path, 'r') as f:
            metadata = json.load(f)
        print(f"Total samples in NSynth: {len(metadata):,}")
        return metadata
    
    def filter_samples(self, metadata, samples_per_class):
        """
        Filter samples by instrument family
        
        Args:
            metadata: NSynth metadata dict
            samples_per_class: Number of samples to collect per instrument
            
        Returns:
            Dict mapping instrument to list of sample info
        """
        print(f"\nFiltering samples (target: {samples_per_class} per instrument)...")
        
        filtered = {inst: [] for inst in self.target_instruments}
        
        for note_id, note_data in tqdm(metadata.items(), desc="Processing samples"):
            family = note_data.get('instrument_family_str', '')
            
            # Map to target instrument
            for target, families in self.family_mapping.items():
                if family in families and target in self.target_instruments:
                    if len(filtered[target]) < samples_per_class:
                        filtered[target].append({
                            'note_id': note_id,
                            'family': family,
                            'pitch': note_data.get('pitch', 0),
                            'velocity': note_data.get('velocity', 0),
                            'instrument_source': note_data.get('instrument_source', 0),
                            'qualities': note_data.get('qualities', [])
                        })
                    break
        
        # Print distribution
        print("\nSample distribution:")
        for inst, samples in filtered.items():
            print(f"  {inst:>10}: {len(samples):>6} samples")
        
        return filtered
    
    def create_splits(self, filtered_samples, train_size, val_size, test_size):
        """
        Split samples into train/val/test sets
        
        Args:
            filtered_samples: Dict of filtered samples by instrument
            train_size: Number of training samples
            val_size: Number of validation samples
            test_size: Number of test samples
            
        Returns:
            Tuple of (train_data, val_data, test_data)
        """
        print(f"\nCreating splits (train: {train_size}, val: {val_size}, test: {test_size})...")
        
        # Flatten samples with labels
        all_samples = []
        all_labels = []
        
        label_to_idx = {inst: idx for idx, inst in enumerate(self.target_instruments)}
        
        for instrument, samples in filtered_samples.items():
            for sample in samples:
                all_samples.append(sample)
                all_labels.append(label_to_idx[instrument])
        
        all_samples = np.array(all_samples)
        all_labels = np.array(all_labels)
        
        print(f"Total samples: {len(all_samples):,}")
        
        # Calculate split sizes
        total_available = len(all_samples)
        total_requested = train_size + val_size + test_size
        
        if total_available < total_requested:
            print(f"Warning: Only {total_available:,} samples available (requested {total_requested:,})")
            # Adjust proportionally
            train_size = int(total_available * (train_size / total_requested))
            val_size = int(total_available * (val_size / total_requested))
            test_size = total_available - train_size - val_size
            print(f"Adjusted splits - train: {train_size}, val: {val_size}, test: {test_size}")
        
        # First split: separate test set
        X_temp, X_test, y_temp, y_test = train_test_split(
            all_samples, all_labels,
            test_size=test_size,
            stratify=all_labels,
            random_state=42
        )
        
        # Second split: separate train and validation
        val_ratio = val_size / (train_size + val_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp,
            test_size=val_ratio,
            stratify=y_temp,
            random_state=42
        )
        
        print(f"\nFinal splits:")
        print(f"  Train:      {len(X_train):>6} samples")
        print(f"  Validation: {len(X_val):>6} samples")
        print(f"  Test:       {len(X_test):>6} samples")
        
        return (X_train, y_train), (X_val, y_val), (X_test, y_test)
    
    def copy_audio_files(self, samples, labels, split_name):
        """
        Copy audio files to organized split directory
        
        Args:
            samples: Array of sample info dicts
            labels: Array of label indices
            split_name: Name of split (train/validation/test)
            
        Returns:
            List of saved file metadata
        """
        split_dir = self.output_dir / split_name
        
        # Create directories for each instrument
        for instrument in self.target_instruments:
            (split_dir / instrument).mkdir(parents=True, exist_ok=True)
        
        # Copy files
        saved_files = []
        
        print(f"\nCopying {len(samples):,} files to {split_dir}...")
        
        for sample, label in tqdm(zip(samples, labels), total=len(samples), desc=f"{split_name}"):
            instrument = self.target_instruments[label]
            note_id = sample['note_id']
            
            # Source and destination paths
            src_path = self.audio_dir / f"{note_id}.wav"
            dst_path = split_dir / instrument / f"{note_id}.wav"
            
            if not src_path.exists():
                print(f"Warning: Source file not found: {src_path}")
                continue
            
            # Copy file
            shutil.copy2(src_path, dst_path)
            
            # Save metadata
            saved_files.append({
                'path': str(dst_path.relative_to(self.output_dir)),
                'instrument': instrument,
                'label': int(label),
                'note_id': note_id,
                'pitch': sample['pitch'],
                'velocity': sample['velocity'],
                'family': sample['family'],
                'instrument_source': sample['instrument_source'],
                'qualities': sample['qualities']
            })
        
        # Save split metadata
        metadata_path = split_dir / 'metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump({
                'split': split_name,
                'num_samples': len(saved_files),
                'instruments': self.target_instruments,
                'files': saved_files,
                'label_mapping': {inst: idx for idx, inst in enumerate(self.target_instruments)}
            }, f, indent=2)
        
        print(f"✓ Saved {len(saved_files):,} files and metadata to {split_dir}")
        
        return saved_files
    
    def extract_dataset(self, train_samples, val_samples, test_samples):
        """
        Main extraction pipeline
        
        Args:
            train_samples: Number of training samples
            val_samples: Number of validation samples
            test_samples: Number of test samples
        """
        print("=" * 80)
        print("NSYNTH DATASET EXTRACTION")
        print("=" * 80)
        
        # Load metadata
        metadata = self.load_metadata()
        
        # Calculate samples per class
        total_samples = train_samples + val_samples + test_samples
        samples_per_class = total_samples // len(self.target_instruments)
        
        # Add buffer to ensure we have enough after stratified split
        samples_per_class = int(samples_per_class * 1.2)
        
        # Filter samples
        filtered = self.filter_samples(metadata, samples_per_class)
        
        # Create splits
        train_data, val_data, test_data = self.create_splits(
            filtered, train_samples, val_samples, test_samples
        )
        
        # Copy files to organized structure
        print("\n" + "=" * 80)
        print("COPYING FILES TO ORGANIZED STRUCTURE")
        print("=" * 80)
        
        self.copy_audio_files(train_data[0], train_data[1], 'train')
        self.copy_audio_files(val_data[0], val_data[1], 'validation')
        self.copy_audio_files(test_data[0], test_data[1], 'test')
        
        # Save global config
        config_path = self.output_dir / 'config.json'
        with open(config_path, 'w') as f:
            json.dump({
                'instruments': self.target_instruments,
                'family_mapping': self.family_mapping,
                'train_samples': train_samples,
                'val_samples': val_samples,
                'test_samples': test_samples,
                'source_dataset': str(self.nsynth_dir),
                'extraction_date': str(np.datetime64('now'))
            }, f, indent=2)
        
        print("\n" + "=" * 80)
        print("EXTRACTION COMPLETE!")
        print("=" * 80)
        print(f"Output directory: {self.output_dir}")
        print(f"Global config: {config_path}")
        print("\nDirectory structure:")
        print(f"  {self.output_dir}/")
        print(f"    ├── train/")
        print(f"    │   ├── guitar/")
        print(f"    │   ├── bass/")
        print(f"    │   └── ...")
        print(f"    ├── validation/")
        print(f"    │   └── ...")
        print(f"    ├── test/")
        print(f"    │   └── ...")
        print(f"    └── config.json")

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Extract and organize NSynth dataset into train/val/test splits'
    )
    
    parser.add_argument(
        '--nsynth_dir',
        type=str,
        required=True,
        help='Path to NSynth dataset directory (containing audio/ and examples.json)'
    )
    
    parser.add_argument(
        '--output_dir',
        type=str,
        required=True,
        help='Path to output directory for organized splits'
    )
    
    parser.add_argument(
        '--train_samples',
        type=int,
        default=10000,
        help='Number of training samples (default: 10000)'
    )
    
    parser.add_argument(
        '--val_samples',
        type=int,
        default=1000,
        help='Number of validation samples (default: 1000)'
    )
    
    parser.add_argument(
        '--test_samples',
        type=int,
        default=1000,
        help='Number of test samples (default: 1000)'
    )
    
    args = parser.parse_args()
    
    # Create extractor
    extractor = NSynthDatasetExtractor(
        nsynth_dir=args.nsynth_dir,
        output_dir=args.output_dir
    )
    
    # Extract dataset
    extractor.extract_dataset(
        train_samples=args.train_samples,
        val_samples=args.val_samples,
        test_samples=args.test_samples
    )

if __name__ == '__main__':
    main()