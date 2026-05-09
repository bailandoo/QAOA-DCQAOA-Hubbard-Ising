import glob
import os
import re
import shutil
import numpy as np


# Dla bezpieczeństwa domyślnie NIE usuwam plików wejściowych.
# Jeśli chcesz zachować stare zachowanie, ustaw na True.
CLEAN_INPUT_FILES = True


##########################################
# Wyszukiwanie plików:
# energies<kategoria>_<seed>.out
# np.:
#   energies1_7.out
#   energies12_3.out
##########################################
def list_energy_files_by_category():
    """
    Zwraca słownik:
        {
            "<kategoria>": [(seed_int, filepath), ...],
            ...
        }

    Uwzględnia tylko pliki dokładnie pasujące do wzorca:
        energies<liczba>_<liczba>.out
    """
    files = glob.glob("energies*.out")
    grouped = {}

    pattern = re.compile(r"^energies(\d+)_(\d+)\.out$")

    for fpath in files:
        base = os.path.basename(fpath)
        m = pattern.match(base)
        if not m:
            continue

        category = m.group(1)   # zachowujemy jako string, np. "1", "12"
        seed = int(m.group(2))

        grouped.setdefault(category, []).append((seed, fpath))

    for category in grouped:
        grouped[category].sort(key=lambda x: x[0])

    return grouped


##########################################
# Parsowanie pliku energii
##########################################
def parse_energy_file(fname):
    """
    Czyta plik energii i zwraca:
      - p_list: lista wartości p
      - e_list: lista energii E_val
      - e_norm_list: lista energii znormalizowanych E_val_norm
      - e_exact: wartość E_exact albo None
      - e_subspace: wartość E_subspace albo None

    Obsługiwany format:
      p E_val E_val_norm
      ...
      E_exact <wartość>
      E_subspace <wartość>   # opcjonalnie
    """
    p_list = []
    e_list = []
    e_norm_list = []
    e_exact = None
    e_subspace = None

    with open(fname, "r") as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue

            tag = parts[0]

            if tag == "E_exact":
                if len(parts) >= 2:
                    try:
                        e_exact = float(parts[1])
                    except Exception:
                        pass
                continue

            if tag == "E_subspace":
                if len(parts) >= 2:
                    try:
                        e_subspace = float(parts[1])
                    except Exception:
                        pass
                continue

            if len(parts) < 3:
                continue

            try:
                p = int(parts[0])
                e_val = float(parts[1])
                e_val_norm = float(parts[2])
            except Exception:
                continue

            p_list.append(p)
            e_list.append(e_val)
            e_norm_list.append(e_val_norm)

    return p_list, e_list, e_norm_list, e_exact, e_subspace


##########################################
# Wybór wartości metadanych do zapisu
##########################################
def choose_metadata_value(values, label, category):
    """
    values: lista wartości lub None
    Zwraca pierwszą nie-None wartość.
    Jeśli wykryje różne wartości między plikami, wypisuje ostrzeżenie.
    """
    present = [v for v in values if v is not None]
    if not present:
        return None

    first = present[0]
    inconsistent = any(not np.isclose(v, first, rtol=0.0, atol=1e-12) for v in present[1:])
    if inconsistent:
        print(
            f">>> [kategoria {category}] UWAGA: różne wartości {label} w plikach. "
            f"Do wyjścia zapisuję pierwszą napotkaną wartość: {first:.10f}"
        )

    return first


##########################################
# Przetwarzanie jednej kategorii
##########################################
def process_category(category, seed_files):
    """
    category: string, np. "1", "12"
    seed_files: lista [(seed_int, filepath), ...]

    Tworzy pliki:
      - best_energy<kategoria>.out
      - energies_average<kategoria>.out
    """
    if not seed_files:
        return

    print(f">>> Przetwarzam kategorię {category}")

    parsed = []
    p_values = None

    e_exact_values = []
    e_subspace_values = []

    best_file = None
    best_seed = None
    best_p = None
    best_energy = None

    # Wczytanie i walidacja plików
    for seed, fname in seed_files:
        p_list, e_list, e_norm_list, e_exact, e_subspace = parse_energy_file(fname)

        if not p_list:
            raise RuntimeError(f"Plik {fname} nie zawiera żadnych poprawnych danych (p, E, E_norm).")

        if p_values is None:
            p_values = p_list
        else:
            if p_list != p_values:
                raise RuntimeError(
                    f"Niespójne listy p w kategorii {category}. Problem w pliku: {fname}"
                )

        if len(e_list) != len(e_norm_list):
            raise RuntimeError(f"Niespójna liczba kolumn energii i norm w pliku: {fname}")

        parsed.append({
            "seed": seed,
            "fname": fname,
            "p_list": p_list,
            "e_list": e_list,
            "e_norm_list": e_norm_list,
            "e_exact": e_exact,
            "e_subspace": e_subspace,
        })

        e_exact_values.append(e_exact)
        e_subspace_values.append(e_subspace)

        # Szukanie globalnego minimum energii E_val (druga kolumna)
        for p, E in zip(p_list, e_list):
            if best_energy is None or E < best_energy:
                best_energy = E
                best_file = fname
                best_seed = seed
                best_p = p

    if best_file is None:
        raise RuntimeError(f"Nie udało się znaleźć najlepszej energii w kategorii {category}")

    ##########################################
    # 1) Zapis najlepszego pliku
    ##########################################
    best_energy_out = f"best_energy{category}.out"
    shutil.copyfile(best_file, best_energy_out)

    print(
        f">>> [kategoria {category}] Najlepszy plik: {best_file} "
        f"(seed={best_seed}, p={best_p}, E={best_energy:.10f})"
    )
    print(f">>> Zapisano {best_energy_out}")

    ##########################################
    # 2) Uśrednianie energii i energii znormalizowanej
    ##########################################
    energies_by_seed = [item["e_list"] for item in parsed]
    energies_norm_by_seed = [item["e_norm_list"] for item in parsed]

    energies_arr = np.array(energies_by_seed, dtype=float)          # shape: (n_seeds, n_p)
    energies_norm_arr = np.array(energies_norm_by_seed, dtype=float)

    ddof = 1 if energies_arr.shape[0] > 1 else 0

    energies_mean = energies_arr.mean(axis=0)
    energies_std = energies_arr.std(axis=0, ddof=ddof)

    energies_norm_mean = energies_norm_arr.mean(axis=0)
    energies_norm_std = energies_norm_arr.std(axis=0, ddof=ddof)

    e_exact_out = choose_metadata_value(e_exact_values, "E_exact", category)
    e_subspace_out = choose_metadata_value(e_subspace_values, "E_subspace", category)

    energies_average_out = f"energies_average{category}.out"
    with open(energies_average_out, "w") as f:
        # 5 kolumn:
        # p, mean_E, std_E, mean_E_norm, std_E_norm
        for p, mean_e, std_e, mean_en, std_en in zip(
            p_values, energies_mean, energies_std, energies_norm_mean, energies_norm_std
        ):
            f.write(
                f"{p} {mean_e:.10f} {std_e:.10f} {mean_en:.10f} {std_en:.10f}\n"
            )

        # Linie specjalne na końcu
        if e_exact_out is not None:
            f.write(f"E_exact {e_exact_out:.10f}\n")
        if e_subspace_out is not None:
            f.write(f"E_subspace {e_subspace_out:.10f}\n")

    print(f">>> Zapisano {energies_average_out}")

    ##########################################
    # 3) Opcjonalne czyszczenie plików wejściowych
    ##########################################
    if CLEAN_INPUT_FILES:
        print(f">>> Usuwam pliki wejściowe dla kategorii {category} ...")
        for _, fname in seed_files:
            os.remove(fname)
        print(">>> Usunięto pliki wejściowe.")

    print()


##########################################
# Główne uruchomienie
##########################################
if __name__ == "__main__":
    grouped = list_energy_files_by_category()

    if not grouped:
        print(">>> Brak plików pasujących do wzorca energies<kategoria>_<seed>.out")
    else:
        for category in sorted(grouped.keys(), key=lambda x: int(x)):
            process_category(category, grouped[category])