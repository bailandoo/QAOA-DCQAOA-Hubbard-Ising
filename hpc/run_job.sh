#!/bin/bash -l
#SBATCH -p bem2-cpu
#SBATCH -t 1:00:00
#SBATCH -N 1
#SBATCH -c 1
#SBATCH --mem=1G
#SBATCH -o /dev/null
#SBATCH -e /dev/null

module load Mamba/23.11.0-0
source ~/.bashrc
mamba activate mag

j="$var1"
script_name=${script_name:-QAOA.py}

if [ -n "$repo_root" ]; then
    cd "$repo_root"
fi

python "$script_name" "$j"
