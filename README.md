# QAOA and DC-QAOA for Hubbard and Ising Models

This repository contains implementations of the Quantum Approximate Optimization Algorithm (QAOA) and digitized-counterdiabatic QAOA (DC-QAOA) for quantum many-body models, including Hubbard- and Ising-type Hamiltonians.

The code is organized in two parts:

- files intended for local work and testing in VS Code or Jupyter notebooks,
- files prepared for execution on an HPC cluster using Slurm.

## Repository structure

```text
.
├── README.md
├── local/
│   ├── QAOA.ipynb
│   ├── QAOA.py
│   ├── DC-QAOA.ipynb
│   └── DC-QAOA.py
└── hpc/
    ├── Q.py
    ├── QCD.py
    ├── ISING.py
    ├── ISINGCD.py
    ├── ave.py
    ├── res.sh
    ├── run.sh
    └── mag-hpc.yml
```

## Local execution

The `local/` directory contains two versions of each algorithm:

- `QAOA.ipynb` and `DC-QAOA.ipynb` — notebook versions intended for interactive work,
- `QAOA.py` and `DC-QAOA.py` — script versions intended for execution from a terminal.

The notebook files can be opened directly in VS Code or Jupyter and run with a Python kernel that contains the required Qiskit dependencies.

The Python scripts accept a seed as a command-line argument. For example:

```bash
python QAOA.py <seed>
```

or:

```bash
python DC-QAOA.py <seed>
```

The model parameters used in the files are examples and can be changed directly in the source code depending on the calculation being performed.

Output files are written to the current working directory.

## HPC execution

The `hpc/` directory contains the versions prepared for batch execution on an HPC cluster.

The main files are:

- `Q.py` — QAOA calculation for the Hubbard model,
- `QCD.py` — DC-QAOA calculation for the Hubbard model,
- `ISING.py` — QAOA calculation for the Ising model,
- `ISINGCD.py` — DC-QAOA calculation for the Ising model,
- `res.sh` — helper script that submits a range of Slurm jobs,
- `run.sh` — Slurm job script that defines computational resources, model parameters, the selected Python program, and the Python environment,
- `ave.py` — post-processing script for averaging output files produced for different seeds.

### Slurm workflow

The typical workflow is:

```text
res.sh
  ↓
sbatch
  ↓
run.sh
  ↓
Python script
  ↓
output files
```

`res.sh` accepts the first and last seed to be submitted:

```bash
bash res.sh <start_seed> <end_seed>
```

For every seed in the selected range, `res.sh` submits one Slurm job and passes the seed to `run.sh`.

`run.sh` contains the Slurm configuration and the parameters passed to the selected Python script. Before submitting calculations, edit `run.sh` and choose:

- the Python script to execute,
- model parameters,
- variational depth,
- optional subspace parameters,
- output category,
- mixer definition,
- requested Slurm resources.

The Python program is executed inside the configured Mamba/Conda environment.

## Averaging results

The `ave.py` script searches for output files generated for multiple seeds and groups them by output category.

It creates:

- a file containing the best result found for a category,
- a file containing averaged energies and standard deviations.

Run it from the directory containing the generated output files:

```bash
python ave.py
```

or inside the configured HPC environment, for example:

```bash
mamba run -n <environment_name> python ave.py
```

Before running `ave.py`, check its configuration at the beginning of the file:

- which categories should be processed,
- whether the original input files should be preserved or removed after averaging.

## Python environment

The repository includes an environment file:

```text
mag-hpc.yml
```

This file describes the Python environment and package versions required to reproduce the HPC setup.

A compatible Conda/Mamba environment can be created with:

```bash
mamba env create -f mag-hpc.yml
```

or:

```bash
conda env create -f mag-hpc.yml
```

The created environment can then be used to run the Python scripts locally or on the cluster.

## Requirements

The code uses Python together with packages including:

- NumPy,
- Qiskit,
- qiskit-algorithms.

Additional packages listed in `mag-hpc.yml` are installed as part of the environment.

## Notes

- Numerical values and model parameters present in the scripts are example calculation settings and can be modified.
- The local and HPC versions serve different purposes: the local files are convenient for development and testing, while the HPC files are structured for batch execution through Slurm.
- Output files are created in the current working directory unless the code is modified to use a different path.

## Reference

The attached reference paper is not my work. It is included only as background literature for the DC-QAOA method:

P. Chandarana, N. N. Hegade, K. Paul, F. Albarrán-Arriagada, E. Solano, A. del Campo, and X. Chen, "Digitized-counterdiabatic quantum approximate optimization algorithm," *Physical Review Research* **4**, 013141 (2022). DOI: 10.1103/PhysRevResearch.4.013141.

The paper is published under the Creative Commons Attribution 4.0 International license, which allows redistribution with proper attribution.

