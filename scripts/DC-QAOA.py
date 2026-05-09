import sys
import numpy as np
from typing import Optional

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp
from qiskit.circuit.library import StatePreparation, PauliEvolutionGate
from qiskit_algorithms.optimizers import COBYLA

class Ising1D:
    def __init__(self, L: int, h: float, k: float, J: float):
        self.L, self.h, self.k, self.J = L, h, k, J
        self.H_prob = self._build()

    def _build(self):
        L, h, k, J = self.L, self.h, self.k, self.J
        zz_terms, z_terms, x_terms = [], [], []

        # - sum_<i,j> J Z_i Z_j   (nearest neighbours, periodic boundary)
        for j in range(L):
            ops = ["I"] * L
            ops[j] = "Z"
            ops[(j + 1) % L] = "Z"
            zz_terms.append(("".join(ops), -J))

        # - sum_i h Z_i
        for j in range(L):
            ops = ["I"] * L
            ops[j] = "Z"
            z_terms.append(("".join(ops), -h))

        # - sum_i k X_i
        for j in range(L):
            ops = ["I"] * L
            ops[j] = "X"
            x_terms.append(("".join(ops), -k))

        H_prob = SparsePauliOp.from_list(zz_terms + z_terms + x_terms).simplify()
        return H_prob

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
            hop_terms += [("I"*i + "XX" + "I"*(2*L - i - 2), -J/2),
                          ("I"*i + "YY" + "I"*(2*L - i - 2), -J/2)]
            # spin ↓
            j = i + L
            hop_terms += [("I"*j + "XX" + "I"*(2*L - j - 2), -J/2),
                          ("I"*j + "YY" + "I"*(2*L - j - 2), -J/2)]

        # on-site interaction
        for i in range(L):
            Iall = "I" * (2*L)
            Zup  = "I"*i       + "Z" + "I"*(2*L - i - 1)
            Zdn  = "I"*(i + L) + "Z" + "I"*(2*L - (i + L) - 1)
            ZZ   = "I"*i + "Z" + "I"*(L - 1) + "Z" + "I"*(L - i - 1)
            int_terms += [(ZZ, U/4.0), (Zup, U/4.0), (Zdn, U/4.0), (Iall, U/4.0)]

        H_hop = SparsePauliOp.from_list(hop_terms).simplify()
        H_int = SparsePauliOp.from_list(int_terms).simplify()
        H = (H_hop + H_int).simplify()

        return H, H_hop, H_int


class QAOASolver:
    def __init__(self, qubits: int, H: SparsePauliOp, Mixer: Optional[SparsePauliOp] = None, Is: Optional[Statevector] = None):
        self.nq = qubits
        self.H = H
        self.initial = Is

        if Mixer is None:
            mixer_terms = [("I"*i + "X" + "I"*(qubits - i - 1), 1.0) for i in range(qubits)]
            Mixer = SparsePauliOp.from_list(mixer_terms).simplify()

        self.M = Mixer
        self.CD = (1.0j * (Mixer.compose(H) - H.compose(Mixer))).simplify()
        
        '''terms = []
        for i in range(self.nq):
            s = ["I"] * self.nq
            s[i] = "Y"
            terms.append(("".join(s), 1.0))'''
            
        '''terms = []
        for i in range(self.nq):
            s = ["I"] * self.nq
            s[i] = "Z"
            s[(i + 1) % self.nq] = "Y"   # periodic boundary conditions
            terms.append(("".join(s), 1.0))'''

        #self.CD = SparsePauliOp.from_list(terms).simplify()

    def circuit(self, p: int, gammas: np.ndarray, betas: np.ndarray, alphas: np.ndarray):
        qc = QuantumCircuit(self.nq)

        if self.initial is None:
            qc.h(range(self.nq))
        else:
            qc.append(StatePreparation(self.initial.data), qc.qubits)

        for i in range(p):
            qc.append(PauliEvolutionGate(self.H, time=gammas[i]), qc.qubits)
            qc.append(PauliEvolutionGate(self.M, time=betas[i]), qc.qubits)
            qc.append(PauliEvolutionGate(self.CD, time=alphas[i]), qc.qubits)

        return qc

    def energy(self, params: np.ndarray, p: int):
        gammas = params[0::3]
        betas  = params[1::3]
        alphas = params[2::3]
        qc = self.circuit(p, gammas, betas, alphas)
        psi = Statevector.from_instruction(qc)

        return float(np.real(psi.expectation_value(self.H)))

    def layer_search(self, p: int, rng: np.random.Generator, maxiter=800):
        opt = COBYLA(maxiter=maxiter)

        x0 = rng.uniform(0.0, np.pi, 3 * p)
        res = opt.minimize(fun=lambda x: self.energy(x, p), x0=x0)

        Energy, Parameters = res.fun, res.x
        qc = self.circuit(p, Parameters[0::3], Parameters[1::3], Parameters[2::3])
        State = Statevector.from_instruction(qc)

        return Energy, Parameters, State
    
    
def Subspace(H: SparsePauliOp, MZ_QUBIT: int = None, MZ_HUBBARD: float = None):
    L = H.num_qubits // 2
    idx = []
    
    for i in range(1 << (2 * L)):
        bits = format(i, f"0{2*L}b")
        N_up = bits[:L].count("0")
        N_down = bits[L:].count("0")
        mz_q = N_up + N_down - L
        mz_h = 0.5 * (N_up - N_down)
        
        if (MZ_QUBIT is None or mz_q == MZ_QUBIT) and (MZ_HUBBARD is None or np.isclose(mz_h, MZ_HUBBARD)):
            idx.append(i)

    Hs = H.to_matrix()[np.ix_(idx, idx)]
    
    return float(np.min(np.linalg.eigvalsh(Hs)))
 # ========================================================================================================================
seed = int(sys.argv[1])
rng = np.random.default_rng(seed)

# PARAMETRY MODELU
L, J, U = 4, 1.0, 10.0
#L, h, k, J = 10, 0.0, 1.0, 1.0
nq = 2 * L

initial_state = None

model = Hubbard1D(L, J, U)
#model = Ising1D(L, h, k, J)
H = model.H
Mixer = None
p_max = 12
# ========================================================================================================================
# ENERGIA DIAGONALIZACJI
E_exact = float(np.linalg.eigvalsh(H.to_matrix())[0])
E_subspace = Subspace(H, -2, 0.0)

# QAOA
qaoa = QAOASolver(nq, H, Mixer, initial_state)

energy_filename = f"energies902_{seed}.out"
with open(energy_filename, "w") as f:

    p_list = list(range(1, p_max+1))
    for p in p_list:
        E_p, x_opt, psi_opt = qaoa.layer_search(p, rng, maxiter=800)
        E_val = float(E_p)
        E_val_norm = float(E_p) / E_exact
        f.write(f"{p} {E_val:.10f} {E_val_norm:.10f}\n")

    f.write(f"E_exact {E_exact:.10f}\n")
    f.write(f"E_subspace {E_subspace:.10f}\n")
