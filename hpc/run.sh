#!/bin/bash -l
#SBATCH -p lem-cpu
#SBATCH -t 50:00:00
#SBATCH -N 1
#SBATCH -c 1
#SBATCH --mem=1G
#SBATCH -o /dev/null
#SBATCH -e /dev/null

module load Mamba/23.11.0-0
source ~/.bashrc
mamba activate mag

# ============================================================
# SEED — zostaje bez zmian
# ============================================================

j="$var1"

# ============================================================
# PARAMETRY, KTÓRE CHCESZ ZMIENIAĆ Z POZIOMU TEGO PLIKU
# ============================================================

L=4
J=1.0
U=0.1

p_max=3

Mq=None
Mz=None

kat="705"

Mixer="none"
#Mixer="model.H_hop"

# ============================================================
# URUCHOMIENIE PYTHONA
# ============================================================

python Q.py "$j" \
  --L "$L" \
  --J "$J" \
  --U "$U" \
  --p_max "$p_max" \
  --Mq "$Mq" \
  --Mz "$Mz" \
  --kat "$kat" \
  --Mixer "$Mixer"
