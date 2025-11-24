"""
MedleyDB Multi-Label Dataset Extractor
=======================================

Extracts multi-label instrument samples from MedleyDB using the official medleydb Python library.

Prerequisites:
    1. Download MedleyDB V1 and/or V2 audio from https://medleydb.weebly.com/
    2. Clone and install medleydb library:
       git clone https://github.com/marl/medleydb.git
       cd medleydb
       pip install -e .
    3. Set environment variable:
       export MEDLEYDB_PATH="/path/to/your/V1"

Usage:
    python medleydb_extractor.py \
        --output_dir ./medleydb-multilabel \
        --segment_duration 4.0 \
        --samples_per_class 1000 \
        --train_ratio 0.8 \
        --val_ratio 0.1 \
        --test_ratio 0.1

Author: Worship Flow Team
"""

import os
import json
import argparse
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from collections import defaultdict, Counter
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# Import medleydb library
try:
    import medleydb
    from medleydb import MultiTrack
except ImportError:
    raise ImportError(
        "medleydb library not found. Please install:\n"
        "  git clone https://github.com/marl/medleydb.git\n"
        "  cd medleydb\n"
        "  pip install -e ."
    )

# ============================================================================
# TARGET INSTRUMENT CONFIGURATION
# ============================================================================

# 7 core worship music instruments
TARGET_INSTRUMENTS = [
    'guitar',
    'bass', 
    'keyboard',
    'drums',
    'strings',
    'brass',
    'vocals'
]

# Map MedleyDB instrument taxonomy to our categories
INSTRUMENT_MAPPING = {
    # Guitars
    'electric guitar': 'guitar',
    'acoustic guitar': 'guitar',
    'clean electric guitar': 'guitar',
    'distorted electric guitar': 'guitar',
    'slide guitar': 'guitar',
    'electric guitar (clean)': 'guitar',
    'electric guitar (distortion)': 'guitar',
    'lap steel guitar': 'guitar',
    'guitar': 'guitar',
    '12 string guitar': 'guitar',
    
    # Bass
    'electric bass': 'bass',
    'acoustic bass': 'bass',
    'bass': 'bass',
    'upright bass': 'bass',
    'double bass': 'bass',
    'synthesizer bass': 'bass',
    'bass guitar': 'bass',
    'electric bass (finger)': 'bass',
    'electric bass (pick)': 'bass',
    
    # Keyboards/Piano
    'piano': 'keyboard',
    'grand piano': 'keyboard',
    'electric piano': 'keyboard',
    'keyboard': 'keyboard',
    'synthesizer': 'keyboard',
    'organ': 'keyboard',
    'accordion': 'keyboard',
    'harmonium': 'keyboard',
    'harpsichord': 'keyboard',
    'rhodes piano': 'keyboard',
    'wurlitzer': 'keyboard',
    'mellotron': 'keyboard',
    
    # Drums
    'drums': 'drums',
    'drum set': 'drums',
    'drum kit': 'drums',
    'kick drum': 'drums',
    'snare drum': 'drums',
    'tom': 'drums',
    'cymbal': 'drums',
    'hi-hat': 'drums',
    'toms': 'drums',
    'ride cymbal': 'drums',
    'crash cymbal': 'drums',
    'auxiliary percussion': 'drums',
    
    # Strings
    'violin': 'strings',
    'viola': 'strings',
    'cello': 'strings',
    'double bass': 'strings',
    'erhu': 'strings',
    'fiddle': 'strings',
    'string section': 'strings',
    'cello section': 'strings',
    'violin section': 'strings',
    
    # Brass
    'trumpet': 'brass',
    'trombone': 'brass',
    'french horn': 'brass',
    'tuba': 'brass',
    'cornet': 'brass',
    'horn': 'brass',
    'flugelhorn': 'brass',
    'trombone section': 'brass',
    'trumpet section': 'brass',
    'brass section': 'brass',
    
    # Vocals
    'male singer': 'vocals',
    'female singer': 'vocals',
    'male speaker': 'vocals',
    'female speaker': 'vocals',
    'male rapper': 'vocals',
    'female rapper': 'vocals',
    'vocalists': 'vocals',
    'choir': 'vocals',
    'voice': 'vocals',
    'singer': 'vocals',
    'vocal': 'vocals',
    'main system': 'vocals',  # Sometimes vocals are labeled as this
}

# ============================================================================
# MEDLEYDB EXTRACTOR
# ============================================================================

class MedleyDBExtractor:
    """Extract multi-label instrument data from MedleyDB using official library"""
    
    def __init__(self, output_dir, target_instruments=None, 
                 instrument_mapping=None, sample_rate=16000):
        """
        Initialize extractor
        
        Args:
            output_dir: Path to output directory
            target_instruments: List of target instrument categories
            instrument_mapping: Dict mapping MedleyDB instruments to categories
            sample_rate: Target sample rate
        """
        self.output_dir = Path(output_dir)
        self.sample_rate = sample_rate
        
        self.target_instruments = target_instruments or TARGET_INSTRUMENTS
        self.instrument_mapping = instrument_mapping or INSTRUMENT_MAPPING
        
        self.num_classes = len(self.target_instruments)
        self.label_to_idx = {inst: idx for idx, inst in enumerate(self.target_instruments)}
        
        print("=" * 80)
        print("MEDLEYDB MULTI-LABEL EXTRACTOR")
        print("=" * 80)
        print(f"Output: {output_dir}")
        print(f"Target instruments ({len(self.target_instruments)}): {', '.join(self.target_instruments)}")
        
        # Check if medleydb can find audio
        if not medleydb.AUDIO_AVAILABLE:
            raise ValueError(
                "MedleyDB audio not found. Please set MEDLEYDB_PATH:\n"
                "  export MEDLEYDB_PATH='/path/to/your/V1'\n"
                "Current MEDLEYDB_PATH: " + os.environ.get('MEDLEYDB_PATH', 'NOT SET')
            )
        
        print(f"MedleyDB Path: {medleydb.MEDLEYDB_PATH}")
        print("=" * 80)
    
    def load_all_tracks(self):
        """Load all available MedleyDB tracks"""
        print("\nLoading MedleyDB tracks...")
        
        # Load all multitracks (returns generator, convert to list)
        all_tracks = list(medleydb.load_all_multitracks())
        
        print(f"Found {len(all_tracks)} tracks in MedleyDB")
        
        # Filter tracks that have our target instruments
        valid_tracks = []
        print("Filtering tracks with target instruments...")
        for track in tqdm(all_tracks, desc="Filtering tracks"):
            # Get instruments in this track
            instruments = self.extract_instruments_from_track(track)
            
            if len(instruments) > 0:
                valid_tracks.append(track)
        
        print(f"Found {len(valid_tracks)} tracks with target instruments")
        
        return valid_tracks
    
    def extract_instruments_from_track(self, track):
        """Extract target instruments present in a track"""
        mapped_instruments = set()
        
        # Get all stem instruments
        for stem in track.stems.values():
            for instrument in stem.instrument:
                instrument_lower = instrument.lower().strip()
                
                # Map to target category
                if instrument_lower in self.instrument_mapping:
                    category = self.instrument_mapping[instrument_lower]
                    if category in self.label_to_idx:
                        mapped_instruments.add(category)
        
        return list(mapped_instruments)
    
    def create_label_vector(self, instruments):
        """Create multi-hot label vector from list of instruments"""
        label_vector = np.zeros(self.num_classes, dtype=np.float32)
        
        for instrument in instruments:
            if instrument in self.label_to_idx:
                label_vector[self.label_to_idx[instrument]] = 1.0
        
        return label_vector
    
    def get_mix_path(self, track):
        """
        Get the mix audio path for a track, with fallback for V1 structure
        
        Args:
            track: MedleyDB MultiTrack object
            
        Returns:
            Path to mix file or None if not found
        """
        # Try the official mix_path first
        if track.mix_path is not None and os.path.exists(track.mix_path):
            return track.mix_path
        
        # Fallback: construct path manually for V1 structure
        # V1 structure: V1/ArtistName_Track/ArtistName_Track_MIX.wav
        medleydb_path = Path(os.environ.get('MEDLEYDB_PATH', ''))
        track_id = track.track_id
        
        # Try different possible locations
        possible_paths = [
            medleydb_path / track_id / f"{track_id}_MIX.wav",
            medleydb_path / track_id / f"{track_id}_MIX.WAV",
            medleydb_path / "Audio" / track_id / f"{track_id}_MIX.wav",
            medleydb_path / "Audio" / track_id / f"{track_id}_MIX.WAV",
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        return None
    
    def segment_audio(self, track, segment_duration, max_segments=None):
        """
        Segment track audio into fixed-length chunks
        
        Args:
            track: MedleyDB MultiTrack object
            segment_duration: Duration of each segment in seconds
            max_segments: Maximum number of segments to extract
            
        Returns:
            List of audio segments
        """
        try:
            # Get mix audio path with fallback
            mix_path = self.get_mix_path(track)
            
            if mix_path is None:
                return []
            
            if not os.path.exists(mix_path):
                return []
            
            # Load audio
            audio, sr = librosa.load(mix_path, sr=self.sample_rate, mono=True)
            
            segment_samples = int(segment_duration * self.sample_rate)
            segments = []
            
            # Skip if audio is too short
            if len(audio) < segment_samples:
                return []
            
            # Extract non-overlapping segments
            for start in range(0, len(audio) - segment_samples + 1, segment_samples):
                end = start + segment_samples
                segment = audio[start:end]
                
                # Normalize
                max_val = np.max(np.abs(segment))
                if max_val > 0:
                    segment = segment / max_val
                
                segments.append(segment)
                
                if max_segments and len(segments) >= max_segments:
                    break
            
            return segments
            
        except Exception as e:
            return []
    
    def extract_dataset(self, segment_duration=4.0, max_segments_per_track=10,
                       samples_per_class=1000):
        """
        Extract multi-label dataset from MedleyDB
        
        Args:
            segment_duration: Duration of each audio segment in seconds
            max_segments_per_track: Maximum segments to extract per track
            samples_per_class: Target number of samples per instrument class
            
        Returns:
            List of samples with audio segments and labels
        """
        print("\n" + "=" * 80)
        print("EXTRACTING DATASET")
        print("=" * 80)
        print(f"Target: {samples_per_class} samples per class")
        
        # Load tracks
        tracks = self.load_all_tracks()
        
        if len(tracks) == 0:
            raise ValueError("No valid tracks found")
        
        all_samples = []
        instrument_counts = Counter()
        successful_tracks = 0
        failed_tracks = []
        
        print(f"\nProcessing {len(tracks)} tracks...")
        
        for track in tqdm(tracks, desc="Extracting segments"):
            # Get instruments in this track
            instruments = self.extract_instruments_from_track(track)
            
            if len(instruments) == 0:
                continue
            
            # Create label vector
            label_vector = self.create_label_vector(instruments)
            
            # Segment audio
            segments = self.segment_audio(track, segment_duration, max_segments_per_track)
            
            if len(segments) == 0:
                failed_tracks.append(track.track_id)
                continue
            
            successful_tracks += 1
            
            # Create samples
            for seg_idx, segment in enumerate(segments):
                sample = {
                    'audio': segment,
                    'label': label_vector,
                    'instruments': instruments,
                    'track_id': track.track_id,
                    'segment_idx': seg_idx,
                    'genre': track.genre,
                    'artist': track.artist
                }
                all_samples.append(sample)
                
                # Count instruments
                for inst in instruments:
                    instrument_counts[inst] += 1
        
        print(f"\n✓ Generated {len(all_samples)} segments from {successful_tracks}/{len(tracks)} tracks")
        
        if len(failed_tracks) > 0:
            print(f"\nWarning: Failed to extract audio from {len(failed_tracks)} tracks")
            print("Sample failed tracks:", failed_tracks[:5])
            print("\nDebugging first failed track:")
            if len(failed_tracks) > 0:
                # Find the track object
                for track in tracks:
                    if track.track_id == failed_tracks[0]:
                        print(f"  Track ID: {track.track_id}")
                        print(f"  Official mix_path: {track.mix_path}")
                        print(f"  Computed mix_path: {self.get_mix_path(track)}")
                        
                        # Check what files exist
                        medleydb_path = Path(os.environ.get('MEDLEYDB_PATH', ''))
                        track_dir = medleydb_path / track.track_id
                        if track_dir.exists():
                            print(f"  Track directory exists: {track_dir}")
                            print(f"  Files in directory: {list(track_dir.glob('*'))[:5]}")
                        else:
                            print(f"  Track directory NOT found: {track_dir}")
                        break
        
        if len(all_samples) == 0:
            raise ValueError(
                "No audio segments extracted! Check that:\n"
                f"1. MEDLEYDB_PATH is set correctly: {medleydb.MEDLEYDB_PATH}\n"
                "2. Audio files exist in the correct location\n"
                "3. Files are named like: ArtistName_TrackName_MIX.wav"
            )
        
        # Print instrument distribution
        print("\nInstrument distribution (before balancing):")
        for instrument in self.target_instruments:
            count = instrument_counts[instrument]
            percentage = (count / len(all_samples)) * 100 if len(all_samples) > 0 else 0
            print(f"  {instrument:>12}: {count:>6} segments ({percentage:>5.1f}%)")
        
        # Balance dataset to target samples_per_class
        balanced_samples = self.balance_dataset(all_samples, samples_per_class)
        
        # Print multi-label statistics
        num_instruments_per_sample = [np.sum(s['label']) for s in balanced_samples]
        print(f"\nMulti-label statistics:")
        print(f"  Total samples: {len(balanced_samples)}")
        print(f"  Average instruments per sample: {np.mean(num_instruments_per_sample):.2f}")
        print(f"  Min instruments per sample: {int(np.min(num_instruments_per_sample))}")
        print(f"  Max instruments per sample: {int(np.max(num_instruments_per_sample))}")
        
        return balanced_samples
    
    def balance_dataset(self, samples, samples_per_class):
        """Balance dataset to have approximately equal representation per class"""
        print(f"\nBalancing dataset to ~{samples_per_class} samples per class...")
        
        # Group samples by which instruments they contain
        samples_by_instrument = {inst: [] for inst in self.target_instruments}
        
        for sample in samples:
            for inst in sample['instruments']:
                samples_by_instrument[inst].append(sample)
        
        # For each instrument, limit to samples_per_class
        selected_samples = set()
        
        for instrument in self.target_instruments:
            available = samples_by_instrument[instrument]
            
            # Randomly sample up to samples_per_class
            n_to_select = min(len(available), samples_per_class)
            
            if n_to_select > 0:
                selected_indices = np.random.choice(
                    len(available), 
                    size=n_to_select, 
                    replace=False
                )
                
                for idx in selected_indices:
                    selected_samples.add(id(available[idx]))
        
        # Convert back to list
        balanced = [s for s in samples if id(s) in selected_samples]
        
        # Print new distribution
        instrument_counts = Counter()
        for sample in balanced:
            for inst in sample['instruments']:
                instrument_counts[inst] += 1
        
        print("\nInstrument distribution (after balancing):")
        for instrument in self.target_instruments:
            count = instrument_counts[instrument]
            percentage = (count / len(balanced)) * 100 if len(balanced) > 0 else 0
            print(f"  {instrument:>12}: {count:>6} segments ({percentage:>5.1f}%)")
        
        return balanced
    
    def create_splits(self, samples, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1):
        """Split dataset into train/validation/test sets"""
        print("\n" + "=" * 80)
        print("CREATING SPLITS")
        print("=" * 80)
        print(f"Ratios - Train: {train_ratio:.0%}, Val: {val_ratio:.0%}, Test: {test_ratio:.0%}")
        
        # Shuffle
        np.random.seed(42)
        np.random.shuffle(samples)
        
        # Calculate split indices
        n = len(samples)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)
        
        train_samples = samples[:train_end]
        val_samples = samples[train_end:val_end]
        test_samples = samples[val_end:]
        
        print(f"\nSplit sizes:")
        print(f"  Train:      {len(train_samples):>6} samples ({len(train_samples)/n:.1%})")
        print(f"  Validation: {len(val_samples):>6} samples ({len(val_samples)/n:.1%})")
        print(f"  Test:       {len(test_samples):>6} samples ({len(test_samples)/n:.1%})")
        
        return train_samples, val_samples, test_samples
    
    def save_split(self, samples, split_name):
        """Save split to disk"""
        split_dir = self.output_dir / split_name
        split_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nSaving {split_name} split...")
        
        saved_files = []
        
        for i, sample in enumerate(tqdm(samples, desc=f"Saving {split_name}")):
            # Save audio
            filename = f"{split_name}_{i:06d}.wav"
            audio_path = split_dir / filename
            
            sf.write(str(audio_path), sample['audio'], self.sample_rate)
            
            # Save metadata
            saved_files.append({
                'path': str(Path(split_name) / filename),
                'label': sample['label'].tolist(),
                'instruments': sample['instruments'],
                'num_instruments': int(np.sum(sample['label'])),
                'track_id': sample['track_id'],
                'segment_idx': sample['segment_idx'],
                'genre': sample['genre'],
                'artist': sample['artist']
            })
        
        # Save split metadata
        metadata = {
            'split': split_name,
            'num_samples': len(saved_files),
            'instruments': self.target_instruments,
            'multilabel': True,
            'files': saved_files
        }
        
        metadata_path = split_dir / 'metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✓ Saved {len(saved_files)} files to {split_dir}")
        
        return saved_files
    
    def create_dataset(self, segment_duration=4.0, samples_per_class=1000,
                      train_ratio=0.8, val_ratio=0.1, test_ratio=0.1,
                      max_segments_per_track=10):
        """Main pipeline: extract, balance, split, and save dataset"""
        
        # Extract samples
        samples = self.extract_dataset(
            segment_duration=segment_duration,
            max_segments_per_track=max_segments_per_track,
            samples_per_class=samples_per_class
        )
        
        if len(samples) == 0:
            raise ValueError("No samples extracted from dataset")
        
        # Create splits
        train_samples, val_samples, test_samples = self.create_splits(
            samples, train_ratio, val_ratio, test_ratio
        )
        
        # Save splits
        print("\n" + "=" * 80)
        print("SAVING SPLITS")
        print("=" * 80)
        
        self.save_split(train_samples, 'train')
        self.save_split(val_samples, 'validation')
        self.save_split(test_samples, 'test')
        
        # Save global config
        config = {
            'instruments': self.target_instruments,
            'num_classes': self.num_classes,
            'sample_rate': self.sample_rate,
            'segment_duration': segment_duration,
            'samples_per_class_target': samples_per_class,
            'multilabel': True,
            'train_ratio': train_ratio,
            'val_ratio': val_ratio,
            'test_ratio': test_ratio,
            'source_dataset': 'MedleyDB',
            'medleydb_path': medleydb.MEDLEYDB_PATH,
            'instrument_mapping': self.instrument_mapping
        }
        
        config_path = self.output_dir / 'config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("\n" + "=" * 80)
        print("DATASET CREATION COMPLETE!")
        print("=" * 80)
        print(f"Output directory: {self.output_dir}")
        print(f"\nDataset structure:")
        print(f"  {self.output_dir}/")
        print(f"    ├── config.json")
        print(f"    ├── train/")
        print(f"    │   ├── train_000000.wav")
        print(f"    │   ├── ...")
        print(f"    │   └── metadata.json")
        print(f"    ├── validation/")
        print(f"    │   └── ...")
        print(f"    └── test/")
        print(f"        └── ...")
        print(f"\nReady for multi-label training!")

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Extract multi-label dataset from MedleyDB'
    )
    
    parser.add_argument(
        '--output_dir',
        type=str,
        required=True,
        help='Path to output directory'
    )
    
    parser.add_argument(
        '--segment_duration',
        type=float,
        default=4.0,
        help='Duration of audio segments in seconds (default: 4.0)'
    )
    
    parser.add_argument(
        '--samples_per_class',
        type=int,
        default=1000,
        help='Target number of samples per instrument class (default: 1000)'
    )
    
    parser.add_argument(
        '--train_ratio',
        type=float,
        default=0.8,
        help='Training set ratio (default: 0.8)'
    )
    
    parser.add_argument(
        '--val_ratio',
        type=float,
        default=0.1,
        help='Validation set ratio (default: 0.1)'
    )
    
    parser.add_argument(
        '--test_ratio',
        type=float,
        default=0.1,
        help='Test set ratio (default: 0.1)'
    )
    
    parser.add_argument(
        '--max_segments_per_track',
        type=int,
        default=10,
        help='Maximum segments to extract per track (default: 10)'
    )
    
    parser.add_argument(
        '--sample_rate',
        type=int,
        default=16000,
        help='Audio sample rate (default: 16000)'
    )
    
    args = parser.parse_args()
    
    # Validate ratios
    total_ratio = args.train_ratio + args.val_ratio + args.test_ratio
    if abs(total_ratio - 1.0) > 0.001:
        raise ValueError(f"Ratios must sum to 1.0 (got {total_ratio})")
    
    # Create extractor
    extractor = MedleyDBExtractor(
        output_dir=args.output_dir,
        sample_rate=args.sample_rate
    )
    
    # Create dataset
    extractor.create_dataset(
        segment_duration=args.segment_duration,
        samples_per_class=args.samples_per_class,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        max_segments_per_track=args.max_segments_per_track
    )

if __name__ == '__main__':
    main()