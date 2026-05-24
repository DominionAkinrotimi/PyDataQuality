# Reproducibility Package — PyDataQuality Research Paper

> **Paper Title:** PyDataQuality: An Actionable, Lightweight Data Profiling and Distribution Drift Detection Framework for Production Machine Learning Pipelines
> **Author:** Dominion Akinrotimi
> **Submitted to:** D3AI Journal, Vol. 2, Issue 2, July 2026

This document is the **complete reproducibility guide** for all claims, tables, and figures in the paper. Any reader should be able to independently re-run every experiment and obtain the same results.

---

## 1. Environment Specifications

All experiments were conducted on the following hardware and software environment. **Execution time benchmarks are hardware-dependent** — your absolute timings may differ, but the *relative ordering* and *scaling behaviour* should remain consistent.

| Property | Value |
|---|---|
| **Operating System** | Windows 10 (Build 10.0.22631) |
| **Python Version** | 3.10.11 |
| **Processor** | Intel64 Family 6 Model 61 (GenuineIntel), AMD64 |
| **Virtual Environment** | `.venv` (created via `python -m venv .venv`) |

### 1.1 Exact Package Versions

| Package | Version | Used In |
|---|---|---|
| `pydataquality` | 0.1.0 (git commit `3507dd2`) | All experiments |
| `pandas` | 2.3.3 | All experiments |
| `numpy` | 2.2.6 | All experiments |
| `scipy` | 1.15.3 | KS Test (SciPy backend) |
| `scikit-learn` | 1.7.2 | ML case study (`ml_case_study.py`) |
| `ydata-profiling` | 4.18.4 | Benchmark comparison (`run_benchmarks.py`) |
| `matplotlib` | 3.10.0 | Benchmark chart (`gen_bw_benchmark.py`) |
| `psutil` | 7.2.2 | Memory profiling (`run_benchmarks.py`) |
| `Jinja2` | 3.1.6 | HTML report generation |
| `pytest` | 9.0.3 | Test suite |

---

## 2. Dependency Installation

The main library dependencies are covered:

*   **OS:** Windows 10
*   **Processor:** Intel Core i7 (Intel64 Family 6 Model 61)
*   **Memory:** 16GB RAM
*   **Python:** 3.10.11
*   **Dependencies:** `pandas==2.3.3`, `numpy==2.2.6`, `scipy==1.15.3`, `ydata-profiling==4.18.4`, `evidently>=0.4.0`, `memory-profiler>=0.61.0`, `scikit-learn==1.7.2`, `psutil==7.2.2`

Or to exactly match our full environment:

```bash
pip install -r paperwriting/requirements_experiments.txt
```

---

## 3. File Index — What Each File Proves

| File | Proves / Generates | Relevant Paper Section |
|---|---|---|
| `run_benchmarks.py` | **Tables 1 & 2** — execution time and memory benchmarks | §5.1 |
| `benchmark_results.json` | **Raw data** for Tables 1 & 2 (exact numbers, unmodified) | §5.1 |
| `benchmark_performance.png` | **Figure 8** — scaling chart | §5.1 |
| `ml_case_study.py` | **Tables 3 & 4** — MLOps pipeline accuracy and drift metrics | §5.2 |
| `ml_case_study_results.json` | **Raw data** for Tables 3 & 4 (exact numbers, unmodified) | §5.2 |
| `drift_verification.py` | **Tables C & D, Section IV** — PSI/KS/Entropy/IQR verification | §4.1–4.4 |
| `drift_verification_results.json` | **Raw data** for mathematical worked examples | §4.1–4.4 |
| `gen_bw_benchmark.py` | Regenerates Figure 8 in grayscale from `benchmark_results.json` | §5.1 |
| `../tests/` | **20/20 unit tests** — verifies all core library functions | §5.3 |

---

## 4. Step-by-Step Reproduction Instructions

Run all commands from the **project root** (`pydataquality/`) directory with the virtual environment activated.

### Step 0 — Activate Environment & Install Dependencies

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install experiment extras
pip install ydata-profiling==4.18.4 evidently==0.4.0 memory-profiler==0.61.0 scikit-learn==1.7.2 psutil==7.2.2
```

---

### Step 1 — Run the Full Test Suite (§5.3)

**What it verifies:** All 20 unit tests pass, confirming core library correctness.

```bash
python -m pytest tests/ -v
```

**Expected output:**
```
20 passed, 11 warnings in ~5s
```

The 11 warnings are `PyparsingDeprecationWarning` from matplotlib internals — not from PyDataQuality code.

---

### Step 2 — Run the Mathematical Verification Script (§4.1–4.4)

**What it verifies:** Shannon Entropy, IQR, PSI, and KS Test computations match the worked examples in the paper exactly.

```bash
python paperwriting/drift_verification.py
```

**Expected console output (verify against paper §4.1–4.4):**

```
=== Shannon Entropy Results ===
Entropy 50/30/20 distribution: 1.485475 bits   ← matches §4.1 derivation
Entropy near-uniform 33/33/34: 1.584819 bits   ← matches §4.1 derivation
Binary entropy 50/50:          1.000000 bits   ← matches §4.1 derivation

=== IQR Outlier Detection ===
Q1=14.25, Q3=21.5, IQR=7.25, Lower fence=3.38, Upper fence=32.38
Outliers detected: [100, 200]                  ← matches §4.2 derivation

=== PSI & KS Grid Results ===
Stable (~2pt diff)      PSI=0.021496  stable      KS=0.0760  p=4.18e-02  ← Table C
Moderate (~60pt diff)   PSI=0.702023  significant  KS=0.4040  p=4.08e-49  ← Table C
Severe (~120pt diff)    PSI=4.605624  significant  KS=0.7960  p=2.33e-212 ← Table C

=== get_problematic_rows Demo ===
Age outlier rows: 2                            ← matches §3.5 validation
```

**Output file generated:** `drift_verification_results.json`

---

### Step 3 — Run the Performance Benchmark (Tables 1 & 2, Figure 8)

> ⚠️ **Note on timing:** Absolute execution times depend on your hardware. The **directional results** (PyDataQuality sampled ≈ constant, YData-Profiling >> PyDataQuality) should hold on any comparable machine. Our timings were recorded on an Intel Core i7.

*   **Location:** `paperwriting/run_benchmarks.py`
*   **Execution:** `python paperwriting/run_benchmarks.py`
*   **Output:** Generates `benchmark_results.json` and prints console metrics.
*   **Notes:** Measures wall-clock time and peak incremental RSS using `memory_profiler`. Values represent the mean of 5 independent runs to ensure statistical significance. Due to OS-level page caching on Windows, memory deltas for small runs may occasionally register as 0.00 MB.

To verify Tables 1 & 2 from the raw JSON:

```python
import json
with open('paperwriting/benchmark_results.json') as f:
    r = json.load(f)

scales = r['scales']
for i, s in enumerate(scales):
    print(f"\n--- {s:,} rows ---")
    print(f"  pandas describe():   {r['pandas_describe']['time'][i]:.4f}s")
    print(f"  PDQ (sampled):       {r['pydataquality_sampled']['time'][i]:.4f}s")
    print(f"  PDQ (full):          {r['pydataquality_full']['time'][i]:.4f}s")
    print(f"  ydata-profiling:     {r['ydata_profiling']['time'][i]:.4f}s")
```

**Regenerate Figure 8:**
```bash
python paperwriting/gen_bw_benchmark.py
```

---

### Step 4 — Run the MLOps Case Study (Tables 3 & 4)

```bash
python paperwriting/ml_case_study.py
```

**What runs:** Train Random Forest on 5,000 clean samples → evaluate on corrupted 1,000-row test batch → compare Pipeline A (blind) vs Pipeline B (PyDataQuality gate).

**Expected console output (verify against Table 3):**
```
[Baseline Accuracy]:                    0.6260  ← Table 3, row 1
[Pipeline A Accuracy (Blind Ingest)]:   0.5280  ← Table 3, row 2
[Pipeline B Accuracy (Systematic)]:     0.5290  ← Table 3, row 3
Credit score drift status: significant (PSI: 3.5517)  ← Table 4
```

**Output file:** `paperwriting/ml_case_study_results.json` — full JSON with precision, recall, F1, and per-column drift metrics exactly as shown in the paper.

To verify Table 4 from raw JSON:

```python
import json
with open('paperwriting/ml_case_study_results.json') as f:
    r = json.load(f)
for col in r['drift_metrics']:
    print(f"{col['column']:15} PSI={col['psi']:.5f}  status={col['drift_status']}")
```

---

## 5. Claim-to-Evidence Mapping

Every quantitative claim in the paper maps directly to a verifiable output:

| Paper Claim | Exact Value | Evidence File | JSON Path |
|---|---|---|---|
| "PyDataQuality sampled: 68–84 ms at any scale" | 74ms, 84ms, 69ms, 82ms | `benchmark_results.json` | `pydataquality_sampled.time` |
| "YData-Profiling: 3.4–6.9s" | 6.93s, 3.66s, 3.40s, 3.69s | `benchmark_results.json` | `ydata_profiling.time` |
| "14× speedup at 100k rows" | 3.689 / 0.262 = 14.08× | `benchmark_results.json` | Both above |
| "PSI D-stat: 0.7740, p < 10⁻³²¹" | p=1.01e-321 | `ml_case_study_results.json` | `drift_metrics[1].ks_p_value` |
| "PSI credit score: 3.5517" | 3.5517 | `ml_case_study_results.json` | `drift_metrics[1].psi` |
| "Baseline accuracy: 62.60%" | 0.6260 | `ml_case_study_results.json` | `baseline.accuracy` |
| "Pipeline A accuracy: 52.80%" | 0.5280 | `ml_case_study_results.json` | `pipeline_a_dirty.accuracy` |
| "9.8pp accuracy drop" | 0.626 - 0.528 = 0.098 | `ml_case_study_results.json` | derived |
| "Entropy 50/30/20 = 1.485 bits" | 1.485475 | `drift_verification_results.json` | `entropy.skewed_50_30_20` |
| "IQR outliers: [100, 200]" | [100, 200] | `drift_verification_results.json` | `iqr_demo.outliers` |
| "20/20 tests pass" | 20 passed | Run `pytest tests/ -v` | Console output |

---

## 6. Notes on Reproducibility Limits

1. **Timing benchmarks** depend on CPU speed, memory bandwidth, OS scheduling, and background processes. Absolute times will differ across machines; relative ordering should be preserved.

2. **Memory delta measurements** (via `psutil`) are inherently noisy (±2 MB). Values reported as `0.00 MB` in the paper indicate measurement below `psutil` resolution at that point.

3. **Random seeds** are fully fixed (`np.random.seed(42)` for training data, `seed=100` for corrupted test data). Running on the same Python + NumPy version will yield bit-identical results.

4. **SciPy KS test** uses `scipy.stats.ks_2samp` (v1.15.3). Minor floating-point differences may appear with other versions but results will be identical to many significant figures.

---

## 7. Contact

For questions about reproducibility, contact: **Dominion Akinrotimi** — contact.dominionakinrotimi@gmail.com

Repository: https://github.com/DominionAkinrotimi/PyDataQuality
