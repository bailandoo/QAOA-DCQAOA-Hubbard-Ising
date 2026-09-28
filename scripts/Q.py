import os
import sys
import numpy as np
from typing import Optional

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp
from qiskit.circuit.library import StatePreparation, PauliEvolutionGate
from qiskit_algorithms.optimizers import COBYLA


class Hubbard1D:
    def __init__(self, L: int, J: float, U: float):
        self.L, self.J, self.U = L, J, U
        self.H, self.H_hop, self.H_int = self._build()

    def _build(self):
        L, J, U = self.L, self.J, self.U
        hop_terms, int_terms = [], []

        # hopping
        for i in range(L - 1):
            # spin ↑
            hop_terms += [
                ("I" * i + "XX" + "I" * (2 * L - i - 2), -J / 2),
                ("I" * i + "YY" + "I" * (2 * L - i - 2), -J / 2),
            ]
            # spin ↓
            j = i + L
            hop_terms += [
                ("I" * j + "XX" + "I" * (2 * L - j - 2), -J / 2),
                ("I" * j + "YY" + "I" * (2 * L - j - 2), -J / 2),
            ]

        # on-site interaction
        for i in range(L):
            Iall = "I" * (2 * L)
            Zup = "I" * i + "Z" + "I" * (2 * L - i - 1)
            Zdn = "I" * (i + L) + "Z" + "I" * (2 * L - (i + L) - 1)
            ZZ = "I" * i + "Z" + "I" * (L - 1) + "Z" + "I" * (L - i - 1)
            int_terms += [(ZZ, U / 4.0), (Zup, U / 4.0), (Zdn, U / 4.0), (Iall, U / 4.0)]

        H_hop = SparsePauliOp.from_list(hop_terms).simplify()
        H_int = SparsePauliOp.from_list(int_terms).simplify()
        H = (H_hop + H_int).simplify()

        return H, H_hop, H_int


class QAOASolver:
    def __init__(
        self,
        qubits: int,
        H: SparsePauliOp,
        Mixer: Optional[SparsePauliOp] = None,
        Is: Optional[Statevector] = None,
    ):
        self.nq = qubits
        self.H = H
        self.Hm = Mixer
        self.initial = Is

    def circuit(self, p: int, gammas: np.ndarray, betas: np.ndarray):
        qc = QuantumCircuit(self.nq)

        if self.initial is None:
            qc.h(range(self.nq))
        else:
            qc.append(StatePreparation(self.initial.data), qc.qubits)

        for i in range(p):
            qc.append(PauliEvolutionGate(self.H, time=float(gammas[i])), qc.qubits)
            if self.Hm is None:
                qc.rx(2 * float(betas[i]), range(self.nq))
            else:
                qc.append(PauliEvolutionGate(self.Hm, time=float(betas[i])), qc.qubits)

        return qc

    def energy(self, params: np.ndarray, p: int):
        gammas = params[::2]
        betas = params[1::2]
        qc = self.circuit(p, gammas, betas)
        psi = Statevector.from_instruction(qc)
        return float(np.real(psi.expectation_value(self.H)))

    def layer_search(self, p: int, rng: np.random.Generator, maxiter: int = 800):
        opt = COBYLA(maxiter=maxiter)

        x0 = rng.uniform(0.0, np.pi, 2 * p)
        res = opt.minimize(fun=lambda x: self.energy(x, p), x0=x0)

        Energy, Parameters = res.fun, res.x

        qc = self.circuit(p, Parameters[::2], Parameters[1::2])
        State = Statevector.from_instruction(qc)

        return Energy, Parameters, State


def Subspace(
    H: SparsePauliOp,
    Mixer: Optional[SparsePauliOp] = None,
    MZ_QUBIT: int = None,
    MZ_HUBBARD: float = None,
    energy_tol: float = 1e-10,
):
    L = H.num_qubits // 2
    nqubits = 2 * L
    idx = []

    for i in range(1 << nqubits):
        bits = format(i, f"0{nqubits}b")

        N_up = bits[:L].count("0")
        N_down = bits[L:].count("0")

        mz_q = N_up + N_down - L
        mz_h = 0.5 * (N_up - N_down)

        if (MZ_QUBIT is None or mz_q == MZ_QUBIT) and \
           (MZ_HUBBARD is None or np.isclose(mz_h, MZ_HUBBARD)):
            idx.append(i)

    # Energia liczona zawsze dla H w wybranej podprzestrzeni
    Hs = H.to_matrix()[np.ix_(idx, idx)]
    E0_H = float(np.min(np.linalg.eigvalsh(Hs)))

    # Jeśli Mixer nie jest podany, zwracamy tylko energię H
    if Mixer is None:
        initial_state = None
        return E0_H, initial_state

    # Jeśli Mixer jest podany, initial_state bierzemy z Mixera
    Ms = Mixer.to_matrix()[np.ix_(idx, idx)]

    evals_M, evecs_M = np.linalg.eigh(Ms)
    E0_M = float(np.real(evals_M[0]))

    ground_ids = np.where(np.abs(evals_M - E0_M) < energy_tol)[0]

    psi_sub = np.sum(evecs_M[:, ground_ids], axis=1)
    psi_sub = psi_sub / np.linalg.norm(psi_sub)

    psi_full = np.zeros(1 << nqubits, dtype=complex)
    psi_full[idx] = psi_sub

    initial_state = Statevector(psi_full)

    return E0_H, initial_state
# ========================================================================================================================
seed = int(sys.argv[1])
rng = np.random.default_rng(seed)

import argparse


def none_or_int(value):
    if str(value).lower() == "none":
        return None
    return int(value)


def none_or_float(value):
    if str(value).lower() == "none":
        return None
    return float(value)


parser = argparse.ArgumentParser()

parser.add_argument("--L", type=int, required=True)
parser.add_argument("--J", type=float, required=True)
parser.add_argument("--U", type=float, required=True)

parser.add_argument("--p_max", type=int, required=True)

parser.add_argument("--Mq", type=none_or_int, required=True)
parser.add_argument("--Mz", type=none_or_float, required=True)

parser.add_argument("--kat", type=str, required=True)

parser.add_argument("--Mixer", type=str, required=True)

args = parser.parse_args(sys.argv[2:])

# PARAMETRY MODELU
L = args.L
J = args.J
U = args.U
nq = 2 * L

Mq = args.Mq
Mz = args.Mz

kat = args.kat

model = Hubbard1D(L, J, U)
H = model.H

p_max = args.p_max

if args.Mixer == "none":
    Mixer = None
elif args.Mixer in ["H", "model.H"]:
    Mixer = model.H
elif args.Mixer in ["H_hop", "model.H_hop"]:
    Mixer = model.H_hop
elif args.Mixer in ["H_int", "model.H_int"]:
    Mixer = model.H_int
else:
    raise ValueError(f"Nieznany Mixer: {args.Mixer}")
# ========================================================================================================================
# ENERGIA DIAGONALIZACJI
E_exact = float(np.linalg.eigvalsh(H.to_matrix())[0])
E_subspace, initial_state = Subspace(H, Mixer, Mq, Mz)

# QAOA
qaoa = QAOASolver(nq, H, Mixer, initial_state)

energy_filename = f"energies{kat}_{seed}.out"
with open(energy_filename, "w") as f:

    p_list = list(range(1, p_max + 1))
    for p in p_list:
        E_p, x_opt, psi_opt = qaoa.layer_search(p, rng, maxiter=800)
        E_val = float(E_p)
        E_val_norm = float(E_p) / E_exact

        f.write(f"{p} {E_val:.10f} {E_val_norm:.10f}\n")
        f.flush()
        os.fsync(f.fileno())

    f.write(f"E_exact {E_exact:.10f}\n")
    f.write(f"E_subspace {E_subspace:.10f}\n")
    f.flush()
    os.fsync(f.fileno())
