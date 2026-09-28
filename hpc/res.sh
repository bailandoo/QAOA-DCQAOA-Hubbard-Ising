#!/bin/bash

j1start=$1   # pierwszy indeks
j1end=$2     # ostatni indeks

# WARUNEK CZY UZYTKOWNIK PODAL DWIE WARTOSCI
if [ -z "$j1start" ] || [ -z "$j1end" ]; then
    echo "Użycie: ./res.sh <start> <end>"
    exit 1
fi

for (( c=$j1start; c<=$j1end; c++ ))
do
    echo "job z v=$c"
    sbatch --export=ALL,var1=$c run.sh
    sleep 0.1
done