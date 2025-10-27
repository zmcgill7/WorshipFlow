#!/bin/bash
#SBATCH -A pfw-cs
#SBATCH --qos=standby
#SBATCH -o debug/train_out.out
#SBATCH -e debug/train_err.err
#SBATCH --nodes=1
#SBATCH --partition=a100-40gb
#SBATCH --cpus-per-task=32
#SBATCH --gres=gpu:1
#SBATCH --time=04:00:00
##SBATCH --mail-type=ALL
#SBATCH --mail-user=raikaa01@pfw.edu
#SBATCH --mem=30G

DATASET_NAME=$1

# Activate your virtual environment
source /scratch/gilbreth/raikaa01/Projects/WorshipFlow/.venv/bin/activate

# pip3 install -r requirements.txt


cd "/scratch/gilbreth/raikaa01/Projects/WorshipFlow"

# Run the training script
python train.py --splits_dir ./nsynth-splits --output_dir ./models/worship_flow --epochs 100 --batch_size 64
