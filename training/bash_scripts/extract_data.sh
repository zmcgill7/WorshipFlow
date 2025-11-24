#!/bin/bash
#SBATCH -A pfw-cs
#SBATCH --qos=standby
#SBATCH -o debug/extract_out.out
#SBATCH -e debug/extract_err.err
#SBATCH --nodes=1
#SBATCH --partition=v100
#SBATCH --cpus-per-task=32
#SBATCH --gres=gpu:1
#SBATCH --time=04:00:00
##SBATCH --mail-type=ALL
#SBATCH --mail-user=raikaa01@pfw.edu
#SBATCH --mem=30G

# Activate your virtual environment
source /scratch/gilbreth/raikaa01/Projects/WorshipFlow/.venv/bin/activate

export MEDLEYDB_PATH="/scratch/gilbreth/raikaa01/Downloads/V1"

# pip3 install -r requirements.txt


cd "/scratch/gilbreth/raikaa01/Projects/WorshipFlow"

# Run the training script
python medleydb_extractor.py \
        --output_dir ./medleydb-multilabel \
        --segment_duration 4.0 \
        --samples_per_class 1000 \
        --train_ratio 0.8 \
        --val_ratio 0.1 \
        --test_ratio 0.1