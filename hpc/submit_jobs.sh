#!/bin/bash

j1start=$1   # pierwszy indeks
j1end=$2     # ostatni indeks
script_name=${3:-QAOA.py}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

# WARUNEK CZY UZYTKOWNIK PODAL DWIE WARTOSCI
if [ -z "$j1start" ] || [ -z "$j1end" ]; then
    echo "Użycie: ./hpc/submit_jobs.sh <start> <end> [QAOA.py|DC-QAOA.py]"
    exit 1
fi

if [[ "$script_name" = /* ]]; then
    script_path="$script_name"
elif [ -f "$repo_root/scripts/$script_name" ]; then
    script_path="$repo_root/scripts/$script_name"
else
    script_path="$repo_root/$script_name"
fi

if [ ! -f "$script_path" ]; then
    echo "Nie znaleziono pliku: $script_path"
    exit 1
fi

for (( c=$j1start; c<=$j1end; c++ ))
do
    echo "job z v=$c"
    sbatch --export=ALL,var1=$c,script_name=$script_path,repo_root=$repo_root "$script_dir/run_job.sh" # SCIEZKA DO PLIKU
    sleep 0.1
done
