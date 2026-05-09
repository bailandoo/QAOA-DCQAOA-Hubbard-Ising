# QAOA and DC-QAOA for Hubbard and Ising Models

This repository contains code prepared as part of my Master's thesis in Technical Physics / Quantum Engineering.
The project focuses on variational quantum algorithms for ground-state energy estimation of quantum many-body models, mainly the Hubbard model and the Ising model.

The repository includes implementations of the standard Quantum Approximate Optimization Algorithm (QAOA) and a digitized-counterdiabatic QAOA approach (DC-QAOA). The calculations are based on Qiskit, statevector simulation, Hamiltonian construction with Pauli operators, and classical optimization of variational parameters.

## Repository structure

```text
.
├── README.md
├── environment-wcss.yml
├── notebooks/
│   ├── QAOA.ipynb
│   └── DC-QAOA.ipynb
├── scripts/
│   ├── QAOA.py
│   ├── DC-QAOA.py
│   └── average.py
├── hpc/
│   ├── submit_jobs.sh
│   └── run_job.sh
└── references/
    └── chandarana_2022_dc_qaoa.pdf
```

## Files

- `notebooks/QAOA.ipynb` - notebook version of the standard QAOA implementation.
- `notebooks/DC-QAOA.ipynb` - notebook version of the DC-QAOA implementation.
- `scripts/QAOA.py` - Python script version of the QAOA calculation.
- `scripts/DC-QAOA.py` - Python script version of the DC-QAOA calculation.
- `scripts/average.py` - script for collecting and averaging energy output files.
- `environment-wcss.yml` - Conda/Mamba environment used on the WCSS/HPC system.
- `hpc/submit_jobs.sh` - helper script for submitting a range of Slurm jobs.
- `hpc/run_job.sh` - Slurm job script used to run a selected Python file.
- `references/chandarana_2022_dc_qaoa.pdf` - reference paper used as background literature.

## Running locally

From the main repository directory:

```bash
python scripts/QAOA.py 1
```

or:

```bash
python scripts/DC-QAOA.py 1
```

The argument `1` is the job index / seed parameter passed to the Python script.

## Running on HPC with Slurm

The repository contains two helper scripts for running jobs on an HPC cluster with Slurm:

- `hpc/submit_jobs.sh` submits a range of jobs.
- `hpc/run_job.sh` defines the Slurm job configuration and runs the selected Python script.

Example:

```bash
bash hpc/submit_jobs.sh 1 20
```

This submits jobs with indices from `1` to `20`.

The script executed on the cluster is selected inside `hpc/run_job.sh`. For standard QAOA, use:

```bash
python scripts/QAOA.py "$j"
```

For DC-QAOA, replace the last line with:

```bash
python scripts/DC-QAOA.py "$j"
```

## Reference

The attached reference paper is not my work. It is included only as background literature for the DC-QAOA method:

P. Chandarana, N. N. Hegade, K. Paul, F. Albarrán-Arriagada, E. Solano, A. del Campo, and X. Chen, "Digitized-counterdiabatic quantum approximate optimization algorithm," Physical Review Research 4, 013141 (2022). DOI: 10.1103/PhysRevResearch.4.013141.

The paper is published under the Creative Commons Attribution 4.0 International license, which allows redistribution with proper attribution.
