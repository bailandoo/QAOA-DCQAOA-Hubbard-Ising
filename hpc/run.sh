#!/bin/bash -l

#SBATCH -p lem-cpu
#SBATCH -t 2:00:00
#SBATCH -N 1
#SBATCH -c 1
#SBATCH --mem=1G
#SBATCH -o /dev/null
#SBATCH -e /dev/null


module load Mamba/23.11.0-0


# ============================================================
# SEED
# ============================================================

j="$var1"


# ============================================================
# PARAMETRY MODELU
# ============================================================

L=3
J=1.0
U=0.1

p_max=3

Mq=None
Mz=None

kat="1"

Mixer="none"
#Mixer="model.H_hop"


# ============================================================
# DIAGNOSTYKA
# ============================================================

echo "HOST: $(hostname)"
echo "PWD: $(pwd)"
echo "SEED: $j"


# ============================================================
# URUCHOMIENIE PYTHONA
# ============================================================

mamba run -n mag python Q.py "$j" \
  --L "$L" \
  --J "$J" \
  --U "$U" \
  --p_max "$p_max" \
  --Mq "$Mq" \
  --Mz "$Mz" \
  --kat "$kat" \
  --Mixer "$Mixer"
