# PyDataQuality: The Complete Technical Study Guide
### Concepts, Mathematics, and Engineering Behind the Library

---

> **How to use this guide:** Read it from top to bottom like a textbook. Each chapter builds on the last. Every formula has a plain-English explanation, and every concept has a worked example. By the end, you will understand *exactly* what PyDataQuality does and *why* it works — from the statistics to the software architecture.

---

# TABLE OF CONTENTS

1. [The Big Picture — What You Actually Built](#chapter-1-the-big-picture)
2. [Python Fundamentals Used in the Project](#chapter-2-python-fundamentals)
3. [Pandas & NumPy — The Engines Under the Hood](#chapter-3-pandas-and-numpy)
4. [Descriptive Statistics — The Language of Data](#chapter-4-descriptive-statistics)
5. [Missing Values — Finding the Gaps](#chapter-5-missing-values)
6. [Outlier Detection — The IQR Method (Tukey Fences)](#chapter-6-outlier-detection)
7. [Skewness & Kurtosis — The Shape of Data](#chapter-7-skewness-and-kurtosis)
8. [Shannon Entropy — Measuring Categorical Randomness](#chapter-8-shannon-entropy)
9. [Correlation — How Variables Move Together](#chapter-9-correlation)
10. [Data Drift Detection: Population Stability Index (PSI)](#chapter-10-population-stability-index)
11. [Data Drift Detection: Kolmogorov-Smirnov Test (KS Test)](#chapter-11-kolmogorov-smirnov-test)
12. [Sampling — How to Handle Big Datasets](#chapter-12-sampling)
13. [Software Architecture — How You Designed the Library](#chapter-13-software-architecture)
14. [Data Visualisation — The Plots You Generate](#chapter-14-data-visualisation)
15. [Report Generation with Jinja2](#chapter-15-report-generation)
16. [The Command-Line Interface (CLI)](#chapter-16-the-cli)
17. [Putting It All Together — A Full Walkthrough](#chapter-17-full-walkthrough)

---

# CHAPTER 1: The Big Picture

## What Is PyDataQuality?

Before you touch a single formula, you need to understand **what problem you were solving**.

Imagine you are a data scientist. Your boss hands you a CSV file with 500,000 rows of customer data and says "run your ML model on this." You open it and… panic. You have no idea if the data is good. Are there missing ages? Crazy outliers? Was the January data collected differently from June data?

Before PyDataQuality existed, your options were:

| Tool | Problem |
|---|---|
| `df.describe()` | Only gives you basic stats. Doesn't tell you anything is *wrong*. |
| pandas-profiling / YData | Takes 10+ minutes. Produces 200MB reports. Still doesn't show you the bad rows. |
| Great Expectations | Requires extensive YAML config files and setup. |
| Manual checking | Slow, error-prone, not repeatable. |

**PyDataQuality fills the gap.** It gives you answers in under 30 seconds, shows you which exact rows are bad, and can even write a prompt to send to an AI to fix everything.

## The Analogy: PyDataQuality is a Doctor for Your Data

When you go to a doctor, they:
1. **Take your vitals** (blood pressure, temperature, etc.) — this is the **profiling** step.
2. **Identify what's wrong** (you have high blood pressure) — this is the **issue detection** step.
3. **Compare to normal** (your pressure is higher than it was 6 months ago) — this is the **drift detection** step.
4. **Write a prescription** — this is the **AI remediation prompt** step.

PyDataQuality does the exact same thing, but for data instead of patients.

## The Five Layers of Your Architecture

Your project has **five distinct layers**. Think of them like the floors of a building:

```
┌─────────────────────────────────────────┐
│  FLOOR 5: PRESENTATION LAYER            │
│  (reporter.py, visualizer.py)           │
│  HTML reports, charts, text reports     │
├─────────────────────────────────────────┤
│  FLOOR 4: DRIFT & DECISION ENGINE       │
│  (comparator.py)                        │
│  PSI, KS Test, drift detection          │
├─────────────────────────────────────────┤
│  FLOOR 3: CORE PROFILING KERNEL         │
│  (analyzer.py)                          │
│  IQR, entropy, missing value detection  │
├─────────────────────────────────────────┤
│  FLOOR 2: SAMPLING ENGINE               │
│  (utils.py → sample_large_dataset)      │
│  Chunk-based sampling for big files     │
├─────────────────────────────────────────┤
│  FLOOR 1: INGESTION LAYER               │
│  (cli.py, __init__.py)                  │
│  CSV, Excel, JSON, Parquet loading      │
└─────────────────────────────────────────┘
```

Data comes in at Floor 1, gets processed up through each layer, and comes out at Floor 5 as a beautiful report.

---

# CHAPTER 2: Python Fundamentals

## 2.1 Dataclasses

In `analyzer.py`, you used Python **dataclasses**. These are a way of creating a "blueprint" for structured data.

```python
from dataclasses import dataclass, field

@dataclass
class QualityIssue:
    column: str
    issue_type: str
    severity: str          # 'critical', 'warning', 'info'
    message: str
    affected_count: int = 0
    affected_percentage: float = 0.0
    details: Dict = field(default_factory=dict)
```

**What is this doing?**

Think of a `dataclass` like a **standardised form**. Every time you detect an issue, you fill in the same form. The form has fields:
- **column**: Which column has the problem? (e.g., `"age"`)
- **issue_type**: What kind of problem? (e.g., `"outliers"`)
- **severity**: How bad is it? (`"critical"`, `"warning"`, or `"info"`)
- **message**: A human-readable description.
- **affected_count**: How many rows are affected?
- **affected_percentage**: What percentage of the data is affected?
- **details**: A dictionary with extra information.

**Without a dataclass**, you would just use raw dictionaries everywhere, which gets messy fast. A dataclass enforces a consistent structure.

**`field(default_factory=dict)`** — This is special. If you wrote `details: Dict = {}`, every `QualityIssue` would *share the same dictionary*, which is a famous Python bug. Using `field(default_factory=dict)` creates a **fresh new dictionary** for every instance. Always do this for mutable defaults.

**Worked Example:**
```python
# When the analyzer finds an outlier in the 'age' column:
issue = QualityIssue(
    column="age",
    issue_type="outliers",
    severity="warning",
    message="Found 12 outliers outside range [7.50, 68.60]",
    affected_count=12,
    affected_percentage=2.4,
    details={"lower_bound": 7.50, "upper_bound": 68.60}
)

print(issue.column)        # "age"
print(issue.severity)      # "warning"
print(issue.affected_count) # 12
```

## 2.2 Type Hints

Throughout the code, you see things like:

```python
def get_problematic_rows(self, column: str, issue_type: str = "all") -> pd.DataFrame:
```

The `: str`, `: pd.DataFrame`, and `-> pd.DataFrame` are **type hints**. They don't change how the code runs, but they:
1. Make the code self-documenting (you know what types to pass in)
2. Allow code editors (like VS Code) to warn you if you pass the wrong type
3. Make the code easier to maintain

```python
# These are all type hints:
def my_function(
    name: str,          # name must be a string
    count: int,         # count must be an integer
    data: Dict,         # data must be a dictionary
) -> pd.DataFrame:      # the function returns a DataFrame
    ...
```

## 2.3 The `Optional` Type

```python
from typing import Dict, List, Optional, Tuple, Union

def get_column_report(self, column: str) -> Optional[Dict]:
```

`Optional[Dict]` means the function can return either a `Dict` or `None`. In Python, this is equivalent to `Union[Dict, None]`. When you write:

```python
if column not in self.column_stats:
    return None   # <-- this is the "Optional" part
```

## 2.4 The `defaultdict`

In `analyzer.py`:
```python
from collections import defaultdict

def _count_issues_by_type(self) -> Dict:
    counts = defaultdict(int)
    for issue in self.issues:
        counts[issue.issue_type] += 1
    return dict(counts)
```

A **regular dictionary** raises a `KeyError` if you try to access a key that doesn't exist:
```python
d = {}
d["outliers"] += 1  # ERROR! KeyError: 'outliers'
```

A **defaultdict** automatically creates a default value if the key doesn't exist:
```python
from collections import defaultdict
d = defaultdict(int)   # Default value is int() = 0
d["outliers"] += 1     # Works! It creates "outliers": 0, then adds 1 → 1
d["outliers"] += 1     # Now it's 2
d["missing"]           # Automatically creates "missing": 0
```

This is very useful when counting things, because you don't have to check `if key in d` first.

## 2.5 Class Methods and `self`

Your `DataQualityAnalyzer` is a **class**. All the methods inside it receive `self` as the first argument, which is a reference to the object itself.

```python
class DataQualityAnalyzer:
    def __init__(self, df, name="Dataset"):
        self.df = df.copy()    # Store df as an instance variable
        self.name = name       # Store name as an instance variable
        self.issues = []       # Start with empty list of issues

    def get_summary(self):
        # 'self' lets us access the instance variables
        return {"name": self.name, "rows": len(self.df)}
```

When you do `analyzer = DataQualityAnalyzer(df, "My Data")`, Python creates an **instance** of the class and passes it as `self` to all method calls. So `analyzer.get_summary()` is the same as `DataQualityAnalyzer.get_summary(analyzer)`.

## 2.6 Exception Handling

In multiple places, you use `try/except`:

```python
try:
    Q1 = numeric_data.quantile(0.25)
    Q3 = numeric_data.quantile(0.75)
    IQR = Q3 - Q1
    # ... more calculations
except Exception:
    # If quantile calculation fails, skip outlier detection
    pass
```

This means: "Try to run this code. If *anything* goes wrong (any exception), just skip it and continue." This is called **defensive programming** — you write code that won't crash even when something unexpected happens.

---

# CHAPTER 3: Pandas and NumPy

## 3.1 What is a DataFrame?

A **DataFrame** is pandas' version of a table. Imagine a spreadsheet:

```
   age   salary    department   hired_date
0   25   45000     Engineering  2021-03-01
1   30   72000     Marketing    2019-07-15
2  150   99000     Engineering  2023-01-10   ← age=150 is suspicious!
3   27     NaN     Sales        2022-08-20   ← salary is missing!
4   35   58000     marketing    2020-04-05   ← "marketing" vs "Marketing"!
```

Each row is a **record** (one employee). Each column is a **feature** (one piece of information). The numbers on the left (0, 1, 2, 3, 4) are the **index**.

## 3.2 Series vs DataFrame

- A **Series** is a single column: `df["age"]` → `[25, 30, 150, 27, 35]`
- A **DataFrame** is the whole table: `df`

Most of PyDataQuality's analysis happens on individual Series.

## 3.3 Data Types in Pandas

This is crucial. Pandas assigns a **dtype** (data type) to each column. Your analyzer handles different dtypes differently:

| Pandas dtype | Python equivalent | Example | How analyzer handles it |
|---|---|---|---|
| `int64` | Integer | `25`, `30` | Numeric analysis (IQR, mean, std) |
| `float64` | Float | `3.14`, `NaN` | Numeric analysis |
| `object` | String or mixed | `"Marketing"` | Categorical analysis |
| `category` | Categorical | `"Low"/"Med"/"High"` | Categorical analysis |
| `datetime64` | Date/time | `2021-03-01` | DateTime analysis |
| `bool` | Boolean | `True/False` | Numeric analysis (special case) |

Your code uses `pd.api.types` to check these:
```python
if pd.api.types.is_numeric_dtype(col_data):
    self._analyze_numeric_column(col_data, stats)
elif pd.api.types.is_string_dtype(col_data):
    self._analyze_categorical_column(col_data, stats)
elif pd.api.types.is_datetime64_any_dtype(col_data):
    self._analyze_datetime_column(col_data, stats)
```

## 3.4 Key Pandas Operations Used

### `.isnull()` and `.sum()`

```python
missing_count = col_data.isnull().sum()
```

- `col_data.isnull()` returns a **boolean Series**: `[False, False, False, True, False]` (True where value is NaN)
- `.sum()` on a boolean Series counts the `True` values (because `True = 1`, `False = 0`)

**Example:**
```
age Series:  [25, 30, NaN, 27, 35]
isnull():    [F,  F,  T,   F,  F]
.sum():      1   (one missing value)
```

### `.nunique()`

Counts the number of unique (distinct) values in a Series.
```
department: ["Engineering", "Marketing", "Engineering", "Sales", "marketing"]
.nunique():  4  (Engineering, Marketing, Sales, marketing — case-sensitive!)
```

### `.quantile()`

Returns the value at a given percentile. This is fundamental to IQR-based outlier detection (Chapter 6).
```python
Q1 = numeric_data.quantile(0.25)  # 25th percentile
Q3 = numeric_data.quantile(0.75)  # 75th percentile
```

### `.value_counts()`

Counts occurrences of each unique value:
```
department.value_counts():
Engineering    2
Marketing      1
Sales          1
marketing      1
```

### Boolean Masking

This is how you select rows that meet a condition:
```python
# Select rows where age is an outlier
mask = (col_data < lower_bound) | (col_data > upper_bound)
outlier_rows = df[mask]
```

The `|` is bitwise OR (works element-wise on boolean Series). `&` is bitwise AND.

### `.copy()`

```python
self.df = df.copy()
```

In pandas, when you do `self.df = df`, you create a **reference** — both variables point to the same data. If you later modify `self.df`, you'd also modify the original `df` the user passed in! `.copy()` creates a completely independent copy, so the original data is never modified.

---

# CHAPTER 4: Descriptive Statistics

This chapter covers the statistics your analyzer computes for every numeric column.

## 4.1 Mean (Average)

**What it is:** The sum of all values divided by the count.

**Formula:**
```
Mean (μ) = (x₁ + x₂ + x₃ + ... + xₙ) / n
```

**Worked Example:**

Dataset of salaries: `[45000, 72000, 99000, 58000, 62000]`

```
Mean = (45000 + 72000 + 99000 + 58000 + 62000) / 5
     = 336000 / 5
     = 67200
```

**In code:**
```python
stats_dict["mean"] = float(numeric_data.mean())
# → 67200.0
```

**What it tells you:** The "centre" of the data. But the mean is heavily influenced by extreme values (outliers). A salary of 999999 would drag the mean way up even if everyone else earns 50000.

## 4.2 Median

**What it is:** The middle value when the data is sorted.

**Steps:**
1. Sort the data
2. If n is odd: the median is the middle value
3. If n is even: the median is the average of the two middle values

**Worked Example:**

Dataset: `[45000, 72000, 99000, 58000, 62000]`

Sorted: `[45000, 58000, 62000, 72000, 99000]`

n = 5 (odd), so median = the 3rd value = **62000**

Now add an outlier: `[45000, 58000, 62000, 72000, 99000, 999999]`

n = 6 (even), so median = average of 3rd and 4th = (62000 + 72000) / 2 = **67000**

The mean with the outlier: (45000 + 58000 + 62000 + 72000 + 99000 + 999999) / 6 = **222666** — a huge distortion!

**Key insight:** When mean and median are very different, you likely have outliers or a skewed distribution.

**In code:**
```python
stats_dict["median"] = float(numeric_data.median())
```

## 4.3 Standard Deviation

**What it is:** A measure of how spread out the values are from the mean.

**Formula:**
```
σ = √( Σ(xᵢ - μ)² / n )
```

Where:
- μ = mean
- xᵢ = each individual value
- n = number of values

**Worked Example:**

Salaries: `[50000, 60000, 70000, 80000, 90000]`

Mean = 70000

Deviations from mean:
```
50000 - 70000 = -20000 → squared: 400,000,000
60000 - 70000 = -10000 → squared: 100,000,000
70000 - 70000 = 0      → squared: 0
80000 - 70000 = 10000  → squared: 100,000,000
90000 - 70000 = 20000  → squared: 400,000,000
```

Average of squared deviations = (400M + 100M + 0 + 100M + 400M) / 5 = 200,000,000

Standard deviation = √200,000,000 = **14,142**

**Interpretation:** The average salary (70,000) is "typically" about £14,142 away from any individual salary.

**In code:**
```python
stats_dict["std"] = float(numeric_data.std())
```

Note: pandas uses `n-1` in the denominator (Bessel's correction for sample standard deviation) rather than `n`. This makes the estimate less biased when working with a sample rather than the entire population.

## 4.4 Minimum and Maximum

Simple — the smallest and largest values.

```python
stats_dict["min"] = float(numeric_data.min())
stats_dict["max"] = float(numeric_data.max())
```

The range = max - min. If the range seems implausible (like age from -5 to 150), you know something is wrong.

## 4.5 Quartiles and IQR

This is critical for outlier detection (Chapter 6), so we introduce the concept here.

Data is divided into **four equal parts** (quarters):

```
|--- 25% ---|--- 25% ---|--- 25% ---|--- 25% ---|
            ↑           ↑           ↑
            Q1          Q2          Q3
         (25th %ile)  (median)  (75th %ile)
```

**Q1** (First Quartile / 25th percentile): 25% of values fall below this.
**Q2** (Second Quartile / 50th percentile): This is the median.
**Q3** (Third Quartile / 75th percentile): 75% of values fall below this.
**IQR** (Interquartile Range): The middle 50% of the data.

```
IQR = Q3 - Q1
```

**Worked Example:**

Dataset: `[10, 20, 25, 30, 35, 40, 45, 50, 55, 70, 90, 150]`

Sorted: `[10, 20, 25, 30, 35, 40, 45, 50, 55, 70, 90, 150]`

n = 12

Q1 = value at 25th percentile = between index 3 and 4 = (25 + 30) / 2 = **27.5**
Q3 = value at 75th percentile = between index 9 and 10 = (55 + 70) / 2 = **62.5**

IQR = 62.5 - 27.5 = **35**

```python
stats_dict["q1"] = float(numeric_data.quantile(0.25))   # 27.5
stats_dict["q3"] = float(numeric_data.quantile(0.75))   # 62.5
```

---

# CHAPTER 5: Missing Values

## 5.1 What Are Missing Values?

A missing value is a cell in your table where no data was recorded. In pandas, these appear as **NaN** (Not a Number) or **None**.

```
age   salary   dept
25    45000    Engineering
NaN   72000    Marketing    ← age is missing
30    NaN      Engineering  ← salary is missing
```

## 5.2 Why They Matter

Missing values cause problems:
- **Averages are wrong**: mean([25, NaN, 30]) should be 27.5, but some programs return NaN
- **ML models crash**: Most scikit-learn models refuse to train on data with NaN values
- **Analysis is biased**: If only rich people answered the salary question, your average salary will be too high

## 5.3 How PyDataQuality Detects Them

```python
missing_count = col_data.isnull().sum()
total_count = len(col_data)
missing_percentage = (missing_count / total_count) * 100 if total_count > 0 else 0
```

**Worked Example:**

Age column: `[25, NaN, 30, NaN, 27, 35, NaN]`

- `isnull()` → `[F, T, F, T, F, F, T]`
- `.sum()` → 3 (three missing)
- `total_count` = 7
- `missing_percentage` = (3/7) × 100 = **42.86%**

## 5.4 The Two-Tier Threshold System

Your config defines two thresholds:

```python
QUALITY_THRESHOLDS = {
    "missing_warning": 0.05,   # > 5% missing → WARNING
    "missing_critical": 0.3,   # > 30% missing → CRITICAL
}
```

**Decision logic:**

```
If missing% > 30%:  → CRITICAL issue (data is unusable without imputation)
Elif missing% > 5%: → WARNING issue (needs attention)
Else:               → Fine, no issue raised
```

**Visual representation:**

```
0%           5%                  30%                 100%
|-----------|-------------------|-------------------|
  All good       WARNING                CRITICAL
```

**Why these thresholds?**
- 5% is a common "acceptable missing data" threshold in data science practice.
- 30% is where most statisticians say you can no longer reliably impute missing values — there's just not enough good data.

---

# CHAPTER 6: Outlier Detection — The IQR Method (Tukey Fences)

This is one of the most important chapters. Outlier detection is a core feature of PyDataQuality.

## 6.1 What is an Outlier?

An outlier is a data point that is dramatically different from the rest. Imagine measuring the heights of 100 people: most are between 150cm and 200cm. If one person is listed as 350cm, something is clearly wrong (data entry error, unit conversion mistake, etc.).

But outliers aren't always errors. Sometimes they are genuinely extreme-but-real values that you need to handle carefully.

## 6.2 The IQR Method (Tukey Fences)

John Tukey invented this method in 1977. It is the most widely used outlier detection technique for univariate (single-variable) analysis.

**The Formula:**

```
Lower Fence = Q1 - (k × IQR)
Upper Fence = Q3 + (k × IQR)

Where k is the "multiplier" (default k = 1.5 in PyDataQuality)

Any value < Lower Fence or > Upper Fence is an OUTLIER.
```

**In your config:**
```python
QUALITY_THRESHOLDS = {
    "outlier_threshold": 1.5,  # This is k
}
```

## 6.3 Step-by-Step Worked Example

**Dataset:** Student test scores
```
[55, 62, 68, 70, 71, 73, 74, 75, 76, 78, 79, 80, 82, 85, 98, 15, 142]
```

That `15` looks suspiciously low, and `142` is impossibly high for a 0-100 test. Let's see if IQR catches them.

**Step 1: Sort the data**
```
[15, 55, 62, 68, 70, 71, 73, 74, 75, 76, 78, 79, 80, 82, 85, 98, 142]
```

n = 17

**Step 2: Calculate Q1 and Q3**

Q1 = 25th percentile → the 4.5th value → (68 + 70) / 2 = **69**

Q3 = 75th percentile → the 13.5th value → (80 + 82) / 2 = **81**

**Step 3: Calculate IQR**
```
IQR = Q3 - Q1 = 81 - 69 = 12
```

**Step 4: Calculate the fences**
```
Lower Fence = Q1 - 1.5 × IQR = 69 - (1.5 × 12) = 69 - 18 = 51
Upper Fence = Q3 + 1.5 × IQR = 81 + (1.5 × 12) = 81 + 18 = 99
```

**Step 5: Identify outliers**

Values outside [51, 99]:
- 15 < 51 → **OUTLIER** ✓
- 142 > 99 → **OUTLIER** ✓
- All others are within [51, 99] → Fine

**Result:** Found 2 outliers. PyDataQuality would report:
> "Found 2 outliers outside range [51.00, 99.00]"

## 6.4 The Code

```python
Q1 = numeric_data.quantile(0.25)
Q3 = numeric_data.quantile(0.75)
IQR = Q3 - Q1

lower_bound = Q1 - self.config["outlier_threshold"] * IQR
upper_bound = Q3 + self.config["outlier_threshold"] * IQR

outliers = numeric_data[
    (numeric_data < lower_bound) | (numeric_data > upper_bound)
]
```

## 6.5 Why k=1.5 and Not Some Other Number?

With k=1.5, for a **perfectly normal distribution** (bell curve), the fences will catch approximately **0.7% of the data** as outliers. This is a deliberate, mathematically calibrated choice — not arbitrary. If you use k=2 or k=3, you capture fewer extreme values. If you use k=1, you flag more values as outliers.

PyDataQuality lets you customise this:
```python
# More lenient (fewer outliers flagged):
config = {"outlier_threshold": 2.0}

# More strict (more outliers flagged):
config = {"outlier_threshold": 1.0}
```

## 6.6 Outlier Severity

Your code also decides **how bad** the outlier situation is:

```python
severity = "warning" if outlier_percentage < 10 else "critical"
```

- If < 10% of values are outliers → **WARNING** (manageable)
- If ≥ 10% of values are outliers → **CRITICAL** (data is seriously corrupted)

## 6.7 `get_problematic_rows()` — Isolating the Bad Rows

This is one of PyDataQuality's headline features. After detecting outliers, you can extract exactly which rows they are:

```python
def get_problematic_rows(self, column: str, issue_type: str = "all") -> pd.DataFrame:
    mask = pd.Series(False, index=self.df.index)  # Start: no rows selected

    if issue_type in ["outliers", "all"] and pd.api.types.is_numeric_dtype(col_data):
        Q1 = numeric_data.quantile(0.25)
        Q3 = numeric_data.quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - self.config["outlier_threshold"] * IQR
        upper = Q3 + self.config["outlier_threshold"] * IQR

        is_outlier = (col_data < lower) | (col_data > upper)
        mask |= is_outlier   # Add outlier rows to the mask

    return self.df[mask].copy()  # Return only the selected rows
```

**Practical use:**
```python
analyzer = pdq.analyze_dataframe(df)
bad_age_rows = analyzer.get_problematic_rows('age', 'outliers')
bad_age_rows.to_csv('rows_to_fix.csv')  # Export for the data team
```

---

# CHAPTER 7: Skewness and Kurtosis

## 7.1 Skewness — The Lean of the Distribution

**Skewness** measures how "lopsided" a distribution is. A perfectly symmetric distribution (like a bell curve) has a skewness of 0.

```
Symmetric (Skew = 0):
     ████
   ████████
  ██████████
 ████████████
──────────────
    Mean = Median

Right-Skewed (Positive Skew):
█
███
█████
███████████
──────────────────────────►
Mean > Median (mean pulled right by outliers)

Left-Skewed (Negative Skew):
                          █
                        ███
                      █████
         ███████████████████
◄──────────────────────────
Mean < Median (mean pulled left by outliers)
```

**The Formula:**

```
Skewness = [ n / ((n-1)(n-2)) ] × Σ [ (xᵢ - μ) / σ ]³
```

The key thing is that skewness uses the **cube** of deviations from the mean. Cubing preserves the sign (negative or positive), so:
- A distribution with a long right tail: positive skew
- A distribution with a long left tail: negative skew

## 7.2 Your Skewness Threshold

```python
QUALITY_THRESHOLDS = {
    "skew_threshold": 1.0,  # Flag if absolute skewness > 1
}
```

**Interpretation guide:**
| |Skewness| Value | Interpretation |
|---|---|
| 0.0 – 0.5 | Approximately symmetric |
| 0.5 – 1.0 | Moderately skewed |
| > 1.0 | **Highly skewed** (your threshold) |

**In your code:**
```python
if abs(stats.stats["skew"]) > self.config["skew_threshold"]:
    self.issues.append(
        QualityIssue(
            issue_type="skewed_distribution",
            severity="info",  # Info only, not critical
            ...
        )
    )
```

**Why does skewness matter?** Many machine learning algorithms assume data is approximately normally distributed. A highly skewed variable might need a transformation (like log-transform) before training.

**Example:** Income data is almost always right-skewed — most people earn moderate amounts, but a few billionaires pull the mean far right.

## 7.3 Kurtosis — The Pointiness of the Distribution

**Kurtosis** measures how "peaked" or "heavy-tailed" a distribution is, relative to a normal distribution.

```python
stats_dict["kurtosis"] = float(numeric_data.kurtosis())
```

- **Kurtosis ≈ 0** (excess kurtosis): Looks like a normal bell curve
- **Kurtosis > 0**: Very peaked with heavy tails (leptokurtic) — more extreme values than expected
- **Kurtosis < 0**: Flatter than normal (platykurtic) — fewer extreme values than expected

```
High Kurtosis (>0):     Low Kurtosis (<0):
     ▲                   ______
     █                  /      \
    ███                /        \
   █████              /          \
  ███████____________/            \______
  Very peaked, heavy tails          Flat, thin tails
```

PyDataQuality computes kurtosis but doesn't currently raise issues from it — it's stored as context. This is future-proof design.

---

# CHAPTER 8: Shannon Entropy — Measuring Categorical Randomness

## 8.1 What is Entropy?

Claude Shannon invented **information entropy** in 1948 in his landmark paper *"A Mathematical Theory of Communication"*. It measures how much **unpredictability** or **information** is in a variable.

**Intuition:** If a coin always lands heads, there's no uncertainty. Entropy = 0. If a coin is perfectly fair (50/50), the entropy is maximum.

For data, this translates to:
- **A column where every row is "Male"** → entropy = 0 (completely predictable, no information)
- **A column with many different equally-distributed categories** → high entropy (lots of information)

## 8.2 The Shannon Entropy Formula

```
H = -Σ pᵢ × log₂(pᵢ)
```

Where:
- `pᵢ` is the **proportion** (probability) of each unique category
- `log₂` is the logarithm base 2
- The sum is over all unique categories
- The negative sign makes the result positive (log of a fraction is negative)

**Units:** "bits" of information (because we use log base 2)

## 8.3 Step-by-Step Worked Example

**Dataset:** Department column with 100 employees

```
Engineering: 60 employees
Marketing:   25 employees
Sales:       15 employees
```

**Step 1: Calculate proportions**
```
p(Engineering) = 60/100 = 0.60
p(Marketing)   = 25/100 = 0.25
p(Sales)       = 15/100 = 0.15
```

**Step 2: Calculate each term**
```
Engineering: -0.60 × log₂(0.60) = -0.60 × (-0.737) =  0.442
Marketing:   -0.25 × log₂(0.25) = -0.25 × (-2.000) =  0.500
Sales:       -0.15 × log₂(0.15) = -0.15 × (-2.737) =  0.411
```

**Step 3: Sum them**
```
H = 0.442 + 0.500 + 0.411 = 1.353 bits
```

**Maximum possible entropy** for 3 categories = log₂(3) = 1.585 bits

So this distribution has 1.353 / 1.585 = **85.3% of maximum entropy** — fairly well distributed.

**Extreme cases:**

If all 100 were Engineering:
```
p = 1.0
H = -1.0 × log₂(1.0) = -1.0 × 0 = 0 bits  (no information)
```

If all 4 categories had exactly 25 employees each:
```
Each p = 0.25
H = -4 × (0.25 × log₂(0.25)) = -4 × (0.25 × -2) = 2.0 bits  (maximum entropy)
```

## 8.4 The Code

```python
def _calculate_entropy(self, series: pd.Series) -> float:
    """Calculate entropy of a categorical series."""
    value_counts = series.value_counts(normalize=True)  # Gets proportions (p_i)
    entropy = -np.sum(value_counts * np.log2(value_counts))  # H = -Σ p_i × log₂(p_i)
    return float(entropy)
```

`normalize=True` makes `.value_counts()` return proportions instead of counts. So if Engineering appears 60 times out of 100, it returns 0.60 instead of 60.

## 8.5 Low Cardinality Detection

Related to entropy but simpler, PyDataQuality also checks for **low cardinality**:

```python
if stats.unique_count / stats.total_count < self.config["unique_threshold"]:
    # Flag as low cardinality issue
```

```python
QUALITY_THRESHOLDS = {
    "unique_threshold": 0.01,  # < 1% unique values
}
```

**Example:** If you have 10,000 rows and only 3 unique values in a column, that's 3/10000 = 0.03% uniqueness — much less than 1%. This might mean the column needs to be treated as categorical, or it might be suspicious.

---

# CHAPTER 9: Correlation — How Variables Move Together

## 9.1 What is Correlation?

**Correlation** measures the strength and direction of the linear relationship between two numeric variables.

```
Pearson Correlation Coefficient:
      Σ[(xᵢ - μₓ)(yᵢ - μᵧ)]
r = ─────────────────────────────────
        √[Σ(xᵢ-μₓ)²] × √[Σ(yᵢ-μᵧ)²]

Range: -1 to +1
```

**Interpretation:**

```
r = +1.0 : Perfect positive correlation (as X increases, Y always increases)
r = +0.7 : Strong positive correlation
r = +0.3 : Weak positive correlation
r =  0.0 : No linear correlation
r = -0.3 : Weak negative correlation
r = -0.7 : Strong negative correlation
r = -1.0 : Perfect negative correlation (as X increases, Y always decreases)
```

**Visualisation:**

```
r ≈ +1          r ≈ 0          r ≈ -1
  *               * *           *
   *              *   *          *
    *            *  *  *          *
     *          *    *    *        *
      *        * *  * * *  *        *
```

## 9.2 The Correlation Heatmap

In `visualizer.py`:
```python
corr_matrix = self.analyzer.df[numeric_cols].corr()
sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", center=0)
```

This creates a grid where each cell shows the correlation between two columns:
- **Red** cells (r close to +1): Strong positive correlation
- **Blue** cells (r close to -1): Strong negative correlation
- **White** cells (r close to 0): No relationship

## 9.3 Duplicate Column Detection

Your `utils.py` uses correlation to find near-duplicate columns:

```python
corr_matrix = df[numeric_cols].corr().abs()  # .abs() → all values 0 to 1

for i, col1 in enumerate(numeric_cols):
    for j, col2 in enumerate(numeric_cols[i + 1:], start=i + 1):
        if corr_matrix.iloc[i, j] > threshold:  # threshold = 0.95
            duplicates.append(col2)
```

**Why this works:** If column A has a correlation of 0.99 with column B, they're essentially saying the same thing. One might be in dollars, the other in thousands of dollars. Having both in your ML model causes **multicollinearity**, which can destabilise model training.

---

# CHAPTER 10: Population Stability Index (PSI)

This is the main drift detection algorithm. PSI answers: **"Has the distribution of this column changed significantly from one time period to another?"**

## 10.1 What is Data Drift?

Imagine you trained a machine learning model on loan applications from January. The model learned that people with incomes between £30k-£80k are low risk. Now it's October, and due to economic changes, most applicants have incomes between £20k-£50k. The model was never trained on this pattern — it will make bad predictions. This is **data drift**.

Data drift = the statistical properties of a feature have changed over time.

## 10.2 PSI Intuition

PSI compares two histograms of the same variable — the **reference** (old/training data) and the **current** (new/production data). If the histograms look different, PSI is high. If they look the same, PSI is low.

```
Reference (January):         Current (October):
    ▓▓                           ▓▓
   ▓▓▓▓                        ▓▓▓▓▓
  ▓▓▓▓▓▓                      ▓▓▓▓▓▓▓▓
 ▓▓▓▓▓▓▓▓                    ▓▓▓▓▓▓▓▓▓▓
────────────────────────────────────────────►
 20k  40k  60k  80k           20k  40k  60k  80k
       Income                       Income

These look different! PSI will be high.
```

## 10.3 The PSI Formula

**Step 1:** Bin both distributions into the same buckets (usually 10 buckets based on the reference percentiles)

**Step 2:** Calculate the proportion of each bin in each dataset

**Step 3:** Apply the formula:

```
PSI = Σ [ (Currentᵢ - Referenceᵢ) × ln(Currentᵢ / Referenceᵢ) ]
```

Where:
- `Referenceᵢ` = proportion of data in bucket i in the reference dataset
- `Currentᵢ` = proportion of data in bucket i in the current dataset
- `ln` = natural logarithm (log base e)
- The sum is over all buckets

## 10.4 Step-by-Step Worked Example

Let's track income distribution over two months.

**Reference (January) — 100 people:**
```
Bucket 1: £0-20k     → 5 people  → p_ref = 0.05
Bucket 2: £20k-40k   → 25 people → p_ref = 0.25
Bucket 3: £40k-60k   → 40 people → p_ref = 0.40
Bucket 4: £60k-80k   → 20 people → p_ref = 0.20
Bucket 5: £80k+      → 10 people → p_ref = 0.10
```

**Current (October) — 100 people:**
```
Bucket 1: £0-20k     → 15 people → p_curr = 0.15
Bucket 2: £20k-40k   → 35 people → p_curr = 0.35
Bucket 3: £40k-60k   → 30 people → p_curr = 0.30
Bucket 4: £60k-80k   → 15 people → p_curr = 0.15
Bucket 5: £80k+      → 5 people  → p_curr = 0.05
```

**PSI Calculation per bucket:**

| Bucket | p_ref | p_curr | (curr - ref) | ln(curr/ref) | Term |
|--------|-------|--------|--------------|--------------|------|
| 1 | 0.05 | 0.15 | +0.10 | ln(0.15/0.05)=1.099 | +0.110 |
| 2 | 0.25 | 0.35 | +0.10 | ln(0.35/0.25)=0.336 | +0.034 |
| 3 | 0.40 | 0.30 | -0.10 | ln(0.30/0.40)=-0.288 | +0.029 |
| 4 | 0.20 | 0.15 | -0.05 | ln(0.15/0.20)=-0.288 | +0.014 |
| 5 | 0.10 | 0.05 | -0.05 | ln(0.05/0.10)=-0.693 | +0.035 |

**PSI = 0.110 + 0.034 + 0.029 + 0.014 + 0.035 = 0.222**

## 10.5 PSI Interpretation Thresholds

```python
if psi >= 0.25:
    drift_status = "significant"    # Major change! Retrain your model!
elif psi >= 0.1:
    drift_status = "moderate"       # Some change, investigate
else:
    drift_status = "stable"         # Distribution hasn't changed
```

In our example, PSI = 0.222 → **"moderate"** drift. Something changed, but not catastrophically.

## 10.6 The PSI Code

```python
def calculate_psi(self, col: str) -> float:
    # Step 1: Create bins using percentiles of the REFERENCE data
    percentiles = np.linspace(0, 100, 11)    # 0, 10, 20, ..., 100
    bins = np.percentile(ref_series, percentiles)
    bins = np.unique(bins)  # Remove duplicate bin edges

    # Step 2: Bin both datasets using the same bins
    ref_counts, _ = np.histogram(ref_series, bins=bins)
    curr_counts, _ = np.histogram(curr_series, bins=bins)

    # Step 3: Convert to proportions
    ref_pct = ref_counts / len(ref_series)
    curr_pct = curr_counts / len(curr_series)

    # Step 4: Add epsilon to prevent log(0) errors
    eps = 1e-4
    ref_pct = np.where(ref_pct == 0, eps, ref_pct)
    curr_pct = np.where(curr_pct == 0, eps, curr_pct)

    # Step 5: Apply PSI formula
    psi_val = np.sum((curr_pct - ref_pct) * np.log(curr_pct / ref_pct))
    return float(psi_val)
```

**The epsilon trick:** What happens if `ref_pct = 0` and `curr_pct = 0.15` for a bucket? Then `ln(0.15/0) = ln(∞) = infinity`, and your PSI would be infinity. Adding a tiny `eps = 0.0001` to any zero prevents this mathematical impossibility. This is called **Laplace smoothing** (or additive smoothing).

## 10.7 Why ln (Natural Log) and Not log₂?

PSI uses natural logarithm (`np.log` in Python). The formula is mathematically related to the **Kullback-Leibler (KL) Divergence**, a foundational concept in information theory. KL Divergence uses natural log by convention. PSI is essentially a symmetrised version of KL Divergence — both measure how different two distributions are.

---

# CHAPTER 11: Kolmogorov-Smirnov Test (KS Test)

## 11.1 What the KS Test Does

The PSI tells you **how much** a distribution has shifted. The KS Test is a formal **statistical hypothesis test** that tells you whether the shift is **statistically significant** — i.e., is it real, or could it be random chance?

## 11.2 The Concept of Hypothesis Testing

Before understanding KS, you need to understand hypothesis testing:

**Null Hypothesis (H₀):** "The two samples come from the same distribution." (nothing changed)

**Alternative Hypothesis (H₁):** "The two samples come from different distributions." (something changed)

The KS test gives you a **p-value**. The p-value is the probability of observing a difference this extreme (or more extreme) if H₀ were true.

```
If p-value < 0.05: "This difference is statistically significant.
                    Reject H₀. The distributions are different."

If p-value ≥ 0.05: "This difference could plausibly be random chance.
                    We cannot reject H₀."
```

**0.05 is the standard threshold.** It's called the "significance level" or "alpha level." It means you're willing to accept a 5% chance of falsely concluding the distributions differ when they actually don't.

## 11.3 The KS Statistic

The KS test compares the **cumulative distribution functions (CDF)** of two samples.

The **CDF** of a dataset tells you: "What percentage of values are ≤ x?"

```
Test Scores: [55, 62, 70, 75, 80, 85, 90]

CDF:
At x=55: 1/7 = 14.3% of values ≤ 55
At x=62: 2/7 = 28.6% of values ≤ 62
At x=70: 3/7 = 42.9% of values ≤ 70
At x=75: 4/7 = 57.1% of values ≤ 75
At x=80: 5/7 = 71.4% of values ≤ 80
At x=85: 6/7 = 85.7% of values ≤ 85
At x=90: 7/7 = 100.0% of values ≤ 90
```

When plotted, this looks like a staircase going from 0% to 100%.

The **KS Statistic (D)** is the **maximum vertical distance** between the two CDFs:

```
CDF₁ (Reference):   ─────────────────────────────────
                                          ________
CDF₂ (Current):     ________________________
                                    ↑
                            D = max gap here

D = 0.25 means the biggest difference between CDFs is 25 percentage points.
```

## 11.4 Full Worked Example

**Reference:** `[10, 20, 30, 40, 50]`
**Current:** `[15, 25, 35, 45, 55]` (slightly shifted up)

**Sorted combined values:** `[10, 15, 20, 25, 30, 35, 40, 45, 50, 55]`

| Value | CDF₁ (Reference) | CDF₂ (Current) | |CDF₁ - CDF₂| |
|-------|-----------------|----------------|--------------|
| 10 | 1/5 = 0.20 | 0/5 = 0.00 | **0.20** |
| 15 | 1/5 = 0.20 | 1/5 = 0.20 | 0.00 |
| 20 | 2/5 = 0.40 | 1/5 = 0.20 | **0.20** |
| 25 | 2/5 = 0.40 | 2/5 = 0.40 | 0.00 |
| 30 | 3/5 = 0.60 | 2/5 = 0.40 | **0.20** |
| 35 | 3/5 = 0.60 | 3/5 = 0.60 | 0.00 |
| 40 | 4/5 = 0.80 | 3/5 = 0.60 | **0.20** |
| 45 | 4/5 = 0.80 | 4/5 = 0.80 | 0.00 |
| 50 | 5/5 = 1.00 | 4/5 = 0.80 | **0.20** |
| 55 | 5/5 = 1.00 | 5/5 = 1.00 | 0.00 |

**D = max(|CDF₁ - CDF₂|) = 0.20**

## 11.5 Calculating the p-value (Asymptotic Approximation)

This is what your pure-numpy fallback code implements:

```
λ (lambda) = D × √( (n₁ × n₂) / (n₁ + n₂) )

p-value ≈ 2 × e^(-2λ²)
```

From our example:
```
n₁ = 5, n₂ = 5, D = 0.20

λ = 0.20 × √(5 × 5 / (5 + 5))
  = 0.20 × √(25/10)
  = 0.20 × √2.5
  = 0.20 × 1.581
  = 0.316

p-value ≈ 2 × e^(-2 × 0.316²)
        = 2 × e^(-2 × 0.100)
        = 2 × e^(-0.200)
        = 2 × 0.819
        = 1.638
```

Since p-value can't exceed 1, your code caps it: `p_val = min(1.0, 1.638) = 1.0`

A p-value of 1.0 means we have no evidence the distributions differ — which makes sense because our shift of 5 units is too small to detect with only 5 data points each.

## 11.6 The Code

```python
try:
    from scipy.stats import ks_2samp      # Prefer the robust library version
    res = ks_2samp(ref_series, curr_series)
    return {"statistic": float(res.statistic), "p_value": float(res.pvalue)}
except ImportError:
    # Pure numpy fallback if scipy isn't installed
    data1 = np.sort(ref_series)
    data2 = np.sort(curr_series)
    n1, n2 = len(data1), len(data2)

    data_all = np.concatenate([data1, data2])
    cdf1 = np.searchsorted(data1, data_all, side="right") / n1
    cdf2 = np.searchsorted(data2, data_all, side="right") / n2

    d = np.max(np.abs(cdf1 - cdf2))   # The KS statistic

    val = d * math.sqrt((n1 * n2) / (n1 + n2))   # λ
    p_val = min(1.0, 2.0 * math.exp(-2.0 * val * val))  # Asymptotic p-value
    return {"statistic": float(d), "p_value": float(p_val)}
```

**`np.searchsorted(data, values, side="right")`**: This efficiently computes the empirical CDF. For each value in `data_all`, it returns how many elements in `data1` are less than or equal to it. Dividing by `n1` gives the CDF proportion.

## 11.7 PSI vs KS — Which Is Better?

| | PSI | KS Test |
|---|---|---|
| **What it measures** | Magnitude of shift | Statistical significance |
| **Output** | A number (higher = more drift) | p-value (lower = more significant) |
| **Works with categorical?** | Yes | No (numeric only) |
| **Requires large n?** | Not really | More reliable with large n |
| **Standard in industry** | Yes (banking/credit scoring) | Yes (general ML monitoring) |

**PyDataQuality uses both.** PSI tells you *how much* things changed. KS tells you *how confident* we are that the change is real, not just noise.

---

# CHAPTER 12: Sampling — How to Handle Big Datasets

## 12.1 The Problem with Big Data

If your CSV file has 10 million rows, loading it all into memory might take several GB of RAM. Running statistics on 10 million rows takes a long time. For a quick data quality check, you don't need all 10 million rows — a good sample gives almost the same results.

## 12.2 Simple Random Sampling

```python
def sample_dataframe(df, n_samples=1000, random_state=42):
    if len(df) <= n_samples:
        return df.copy()  # If already small enough, return everything
    return df.sample(n=min(n_samples, len(df)), random_state=random_state)
```

`df.sample(n=1000)` randomly picks 1000 rows from the DataFrame. `random_state=42` makes this reproducible — you'll always get the same 1000 rows.

## 12.3 Stratified Sampling

Sometimes random sampling can accidentally miss rare categories. For example, if only 1% of your data is "Fraud = Yes", a 1000-row sample might have only 10 fraud cases — not enough to analyze.

**Stratified sampling** ensures each category is proportionally represented:

```python
sample_rate = n_samples / len(df)  # e.g., 1000/10000 = 0.10 (10%)

# Sample 10% from EACH group
sampled = df.groupby(stratify_by, group_keys=False).apply(
    lambda x: x.sample(frac=sample_rate, random_state=random_state)
)
```

**Example:**
- 9000 rows "Non-Fraud" → sample 10% → 900 rows
- 1000 rows "Fraud" → sample 10% → 100 rows
- Total sample: 1000 rows, but the 1:9 fraud/non-fraud ratio is preserved

## 12.4 Chunk-Based Sampling for Huge Files

For files too large to even fit in memory, your `sample_large_dataset` function reads the file in **chunks**:

```python
def sample_large_dataset(filepath, n_samples=1000, chunksize=100000):
    sampled_chunks = []

    for chunk in pd.read_csv(filepath, chunksize=chunksize):
        # Read 100,000 rows at a time
        chunk_sample = chunk.sample(frac=0.1, random_state=42)
        # Take 10% of each chunk
        sampled_chunks.append(chunk_sample)

        if sum(len(c) for c in sampled_chunks) > n_samples * 5:
            break  # Stop once we have enough

    full_sample = pd.concat(sampled_chunks, ignore_index=True)
    return full_sample.sample(n=n_samples, random_state=42)
```

**How it works conceptually:**

```
Large File (10 million rows)
           ↓
┌──────────────────┐
│  Chunk 1 (100k)  │ → sample 10% → 10,000 rows
│  Chunk 2 (100k)  │ → sample 10% → 10,000 rows
│  Chunk 3 (100k)  │ → sample 10% → 10,000 rows
│  Chunk 4 (100k)  │ → STOP (have > 5,000 rows already)
└──────────────────┘
           ↓
Combined: ~30,000 rows
           ↓
Final sample: 1,000 rows
```

This approach uses constant memory — you never load the whole file at once.

---

# CHAPTER 13: Software Architecture

## 13.1 The Object-Oriented Design

PyDataQuality is built using **Object-Oriented Programming (OOP)**. Let's understand the key design choices.

### Classes as "Things"

Your project defines several classes, each representing a conceptual "thing":

```
DataQualityAnalyzer  → "A tool for analysing a dataset"
QualityReportGenerator → "A tool for generating reports from an analysis"
DataQualityVisualizer → "A tool for creating charts from an analysis"
DataQualityComparator → "A tool for comparing two analyses"
```

### Composition: "Has-a" Relationship

`QualityReportGenerator` **has** a `DataQualityAnalyzer`:
```python
class QualityReportGenerator:
    def __init__(self, analyzer: DataQualityAnalyzer):
        self.analyzer = analyzer  # It OWNS an analyzer
```

This is called **composition**. It's better than **inheritance** ("is-a") here because a `QualityReportGenerator` is not an `Analyzer` — it just uses one. Favour composition over inheritance in complex systems.

## 13.2 The Single Responsibility Principle

Each class has ONE job:
- `analyzer.py` → Only analyses data, never creates reports or charts
- `reporter.py` → Only creates reports, never analyses raw data
- `visualizer.py` → Only creates charts, never analyses raw data
- `comparator.py` → Only compares two analyzers, nothing else

This is called the **Single Responsibility Principle (SRP)**, one of the SOLID design principles. It makes code:
- Easier to understand (each file has one purpose)
- Easier to test (you can test each class independently)
- Easier to maintain (changing the HTML template doesn't break the analysis logic)

## 13.3 The `__init__.py` — The Public API

Your `__init__.py` is the library's **public face**. It defines what users see when they `import pydataquality`:

```python
# Users only need to know about these functions:
from .analyzer import DataQualityAnalyzer
from .reporter import QualityReportGenerator
from .comparator import compare_reports, compare_drift
# ... etc

def analyze_dataframe(df, name="Dataset"):
    """This is a CONVENIENCE function — it hides complexity."""
    analyzer = DataQualityAnalyzer(df, name=name)
    return analyzer
```

The **convenience functions** (`analyze_dataframe`, `quick_quality_check`, `generate_report`, etc.) are a design pattern called the **Facade Pattern**. They hide the complexity of creating multiple objects, letting beginners use the library with a single line.

## 13.4 Configuration as a Dictionary (`config.py`)

```python
QUALITY_THRESHOLDS = {
    "missing_critical": 0.3,
    "missing_warning": 0.05,
    "outlier_threshold": 1.5,
    "skew_threshold": 1.0,
    "unique_threshold": 0.01,
}
```

Storing thresholds in a separate config file means:
1. **Centralised control**: Change a threshold once, it applies everywhere
2. **User customisation**: Users can override these with `config={"outlier_threshold": 2.0}`
3. **No magic numbers**: Instead of `if pct > 0.3` buried deep in code, you see `if pct > config["missing_critical"]`, which is self-documenting

**How the merge works:**
```python
self.config = QUALITY_THRESHOLDS.copy()   # Start with defaults
if config:
    self.config.update(config)  # Override with user values
```

`dict.update()` adds/replaces keys from the user's dict into the defaults dict. Keys the user doesn't provide remain at their defaults.

## 13.5 The `@dataclass` Pattern

Using `@dataclass` for `QualityIssue` and `ColumnStats` instead of raw dictionaries provides:

1. **Type safety**: You know exactly what fields exist
2. **Auto-generated `__init__`**: You don't write `def __init__(self, column, issue_type, ...):`
3. **Auto-generated `__repr__`**: `print(issue)` gives readable output
4. **Default values**: `affected_count: int = 0` is clear and clean

---

# CHAPTER 14: Data Visualisation

## 14.1 Matplotlib Architecture

`matplotlib` is Python's main plotting library. Its architecture:

```
Figure → The whole image
  └── Axes (ax) → A single chart/plot
        └── Artists → Lines, bars, text, etc.
```

```python
fig, ax = plt.subplots(figsize=(12, 8))
# fig = the whole image
# ax = the chart inside the image
```

`figsize=(12, 8)` means 12 inches wide, 8 inches tall. At 100 DPI (dots per inch), this is 1200×800 pixels.

## 14.2 Seaborn — The Beautiful Wrapper

`seaborn` is built on top of matplotlib and makes statistical charts much easier:

```python
# Without seaborn (matplotlib):
ax.imshow(missing_matrix.values.T, cmap='Greys', aspect='auto')
ax.set_xticks(range(len(missing_matrix.columns)))
ax.set_xticklabels(missing_matrix.columns, rotation=45)
# ... many more lines

# With seaborn:
sns.heatmap(
    missing_matrix.T,
    cmap=["white", "gray"],
    ax=ax
)
```

Seaborn handles the tedious formatting automatically.

## 14.3 The Missing Values Matrix

```python
missing_matrix = self.analyzer.df.isnull().astype(int)
sns.heatmap(
    missing_matrix.T,     # Transposed: rows=columns, cols=rows
    cmap=["white", "gray"],  # White=present, Gray=missing
)
```

**What it produces:** A grid where each column of your dataset is shown as a row. White cells = data exists. Gray cells = data is missing. You can instantly see **patterns** — for example, if age and income are always missing together, they were probably on the same survey page that people skipped.

## 14.4 The Boxplot for Outlier Detection

A **boxplot** visually represents the IQR:

```
         ┌─────────┐
  ───────┤         ├───────  ×  ×  ×   ← Outliers (dots beyond whiskers)
         │    │    │
         └─────────┘
  ↑         ↑    ↑       ↑
  Q1        Med  Q3     Upper whisker (Q3 + 1.5×IQR)
Lower whisker (Q1 - 1.5×IQR)
```

```python
ax.boxplot(
    data,
    vert=True,
    patch_artist=True,
    boxprops=dict(facecolor=self.colors["info"], alpha=0.7),     # Box colour
    medianprops=dict(color=self.colors["critical"], linewidth=2),  # Median line
    flierprops=dict(marker="o", color=self.colors["critical"])    # Outlier dots
)
```

## 14.5 Histogram with Inset Boxplot

Your `create_numeric_distributions()` creates a histogram with a tiny boxplot in the corner — a compound visualisation:

```python
# Main histogram
ax.hist(data, bins=n_bins, alpha=0.7, color=self.colors["info"])

# Mean and median lines
ax.axvline(mean_val, color="red", linestyle="-", label=f"Mean: {mean_val:.2f}")
ax.axvline(median_val, color="orange", linestyle="--", label=f"Median: {median_val:.2f}")

# Inset boxplot in top-right corner
box_ax = ax.inset_axes([0.65, 0.65, 0.3, 0.3])  # [x, y, width, height] in axes coords
box_ax.boxplot(data, vert=True, patch_artist=True)
```

`ax.inset_axes([0.65, 0.65, 0.3, 0.3])` creates a new small Axes positioned at 65% from the left, 65% from the bottom, with width=30% and height=30% of the parent axes.

## 14.6 The Correlation Heatmap

```python
corr_matrix = df[numeric_cols].corr()   # n×n matrix of correlation coefficients
sns.heatmap(
    corr_matrix,
    annot=True,        # Show numbers in cells
    fmt=".2f",         # Format: 2 decimal places
    cmap="coolwarm",   # Red=positive, Blue=negative, White=zero
    center=0,          # White is at 0.0 (no correlation)
    square=True,       # Each cell is square
)
```

## 14.7 The DPI Setting

```python
VISUAL_CONFIG = {
    "dpi": 100,  # Dots Per Inch
}

fig.savefig(filename, dpi=VISUAL_CONFIG["dpi"], bbox_inches="tight")
```

- **100 DPI** is good for screen viewing
- **300 DPI** is needed for print quality (your paper used this)
- `bbox_inches="tight"` prevents labels from being cut off at the edges

---

# CHAPTER 15: Report Generation with Jinja2

## 15.1 What is a Template Engine?

Imagine you have to write 100 personalised letters. Instead of writing each one from scratch, you create a template:

```
Dear [NAME],

Your account has [NUM_ISSUES] quality issues.
Generated on [DATE].
```

Then you fill in `[NAME]`, `[NUM_ISSUES]`, and `[DATE]` for each letter. **Jinja2** is a template engine — it does this for HTML reports.

## 15.2 The Jinja2 Syntax

In your HTML templates, Jinja2 uses special markers:

```html
{{ variable }}           → Insert a variable's value
{% for item in list %}   → Loop through a list
{% if condition %}       → Conditional block
{{ value | filter }}     → Apply a filter to a value
```

**Example from your template:**
```html
<div class="metric-value">{{ summary.dataset.rows|int|comma }}</div>
```

This inserts the number of rows, converts it to an integer, then applies your custom `comma` filter to format it as `1,234,567`.

## 15.3 Custom Filters

```python
def comma_filter(value):
    return f"{value:,}"   # Python's built-in thousands separator

env = Environment()
env.filters["comma"] = comma_filter  # Register it

# Now in your template you can use:
# {{ 1234567 | comma }}  → "1,234,567"
```

## 15.4 The Three Themes

Your reporter offers three HTML themes:

```python
if theme == "creative":
    html_template = self._get_creative_template()   # Dark mode, glassmorphism
elif theme == "professional":
    html_template = self._get_professional_template()  # Clean, formal
else:
    html_template = self._get_simple_template()        # Minimal
```

The **creative theme** uses:
- Dark background (`#0f172a`) — a very dark navy
- Glassmorphism: `backdrop-filter: blur(10px)` — frosted glass effect
- CSS gradient text: `background: linear-gradient(...); -webkit-background-clip: text`
- Hover animations: `transition: transform 0.2s; card:hover { transform: translateY(-5px) }`

## 15.5 The AI Remediation Prompt

This is a clever bridge between deterministic software (PyDataQuality) and generative AI (ChatGPT/Claude/Gemini):

```python
def generate_ai_remediation_prompt(self, include_eda=True) -> str:
    prompt = f"I have a dataset '{name}' with {rows} rows. "
    prompt += f"It has the following quality issues: {issue_list}. "
    prompt += "\n\nHere is the statistical context (EDA):\n"
    
    for col in affected_columns:
        prompt += f"- {col} (int64): Mean=42.3, Median=40.0, Min=-5, Max=150\n"
    
    prompt += "Please write a Python script using pandas to clean this dataset."
    return prompt
```

**Why this is smart:** An AI given raw data doesn't know what "clean" means in your context. But PyDataQuality has already detected the specific issues, computed the statistical context (where the mean is, what the IQR boundaries are), and presents all of this as a clear, structured prompt. The AI can then write targeted, contextualised code.

---

# CHAPTER 16: The CLI

## 16.1 What is a CLI?

A **Command-Line Interface (CLI)** lets users run your program without writing Python code. They just type in a terminal:

```bash
python -m pydataquality data.csv --report html --theme professional
```

## 16.2 How `argparse` Works

`argparse` is Python's built-in library for building CLIs:

```python
import argparse

parser = argparse.ArgumentParser(
    description="PyDataQuality - Automated Data Quality Analysis Tool"
)

# Positional argument (required, no flag needed)
parser.add_argument("file", help="Input data file")

# Optional argument (--name flag)
parser.add_argument("--name", default="Dataset", help="Name of the dataset")

# Optional with choices
parser.add_argument(
    "--report",
    choices=["html", "text", "json", "none"],
    default="html",
)

# Flag (True if present, False if absent)
parser.add_argument("--visualize", action="store_true")

args = parser.parse_args()  # Parse what the user typed

# Access values:
print(args.file)        # "data.csv"
print(args.name)        # "Dataset" (default)
print(args.report)      # "html" (default)
print(args.visualize)   # False (not provided)
```

## 16.3 The `__main__.py` File

Your `pydataquality/__main__.py` file has just two lines:
```python
from .cli import main
main()
```

This makes `python -m pydataquality` work. When Python runs a package with `-m`, it looks for `__main__.py` and executes it. This calls `main()` in `cli.py`, which runs the full CLI.

## 16.4 Auto-Detecting File Format

```python
ext = os.path.splitext(args.file)[1].lower()   # Gets ".csv", ".xlsx", etc.

if ext == ".csv":
    df = pd.read_csv(args.file)
elif ext in [".xlsx", ".xls"]:
    df = pd.read_excel(args.file)
elif ext == ".json":
    df = pd.read_json(args.file)
elif ext == ".parquet":
    df = pd.read_parquet(args.file)
```

`os.path.splitext("data.csv")` returns `("data", ".csv")`. Index `[1]` gets `.csv`. `.lower()` handles `.CSV` (uppercase) too.

---

# CHAPTER 17: Putting It All Together — A Full Walkthrough

Let's trace a complete execution of PyDataQuality from the moment a user calls `pdq.analyze_dataframe(df)` to the moment they get a report.

## 17.1 The Dataset

```python
import pandas as pd
import pydataquality as pdq

data = {
    "age": [25, 30, 150, 27, None, 35, 22, 29, 31, 26],   # 150 is outlier, None is missing
    "salary": [45000, 72000, 99000, None, 58000, 62000, 41000, 55000, 68000, 48000],
    "department": ["Engineering", "Marketing", "engineering", "Sales", "Sales",
                   "Marketing", "Engineering", "Sales", "Engineering", "marketing"],
    "hired_date": ["2021-03-01", "2019-07-15", "2023-01-10", "2022-08-20",
                   "2020-04-05", "2021-11-30", "2022-06-15", "2019-03-22",
                   "2023-05-01", "2021-09-14"]
}
df = pd.DataFrame(data)
```

## 17.2 Step 1: Initialization

```python
analyzer = pdq.analyze_dataframe(df, name="Employee Data")
# This calls: DataQualityAnalyzer(df, name="Employee Data")
```

**Inside `__init__`:**
```python
self.df = df.copy()        # Safe copy of the data
self.name = "Employee Data"
self.config = QUALITY_THRESHOLDS.copy()  # Default thresholds
self.issues = []           # Empty issues list (will be filled)
self.column_stats = {}     # Empty stats dict (will be filled)

self._analyze_dataset_structure()  # Count rows, columns, memory
self._analyze_columns()            # Analyse each column
```

**Dataset structure:**
```python
self.dataset_stats = {
    "rows": 10,
    "columns": 4,
    "total_cells": 40,
    "memory_usage_mb": 0.003,
}
```

## 17.3 Step 2: Column Analysis (Numeric — "age")

The `age` column has dtype `float64` (because of the None value, which forces float).

**Missing value check:**
```
missing_count = col_data.isnull().sum() = 1
missing_percentage = (1/10) × 100 = 10%
10% > 5% (warning threshold) → Issue: "warning" missing_values
10% < 30% (critical threshold) → Not critical
```

**Outlier check:**
```
numeric_data (excluding NaN) = [25, 30, 150, 27, 35, 22, 29, 31, 26]

Sorted: [22, 25, 26, 27, 29, 30, 31, 35, 150]

Q1 = 25.5 (between 25 and 26)
Q3 = 32.5 (between 31 and 35)
IQR = 32.5 - 25.5 = 7.0

Lower Fence = 25.5 - 1.5 × 7.0 = 25.5 - 10.5 = 15.0
Upper Fence = 32.5 + 1.5 × 7.0 = 32.5 + 10.5 = 43.0

Outliers: [150] → 150 > 43.0 ✓
Outlier count = 1
Outlier % = 1/9 × 100 = 11.1%

11.1% > 10% → severity = "CRITICAL"
```

**Issue created:**
```python
QualityIssue(
    column="age",
    issue_type="outliers",
    severity="critical",
    message="Found 1 outliers outside range [15.00, 43.00]",
    affected_count=1,
    affected_percentage=11.1,
    details={"lower_bound": 15.0, "upper_bound": 43.0, "outlier_examples": [150]}
)
```

**Skewness check:**
```
numeric_data.skew() ≈ 3.8 (very right-skewed because of the 150)
3.8 > 1.0 (skew threshold) → Issue: "info" skewed_distribution
```

## 17.4 Step 3: Column Analysis (Categorical — "department")

Values: `["Engineering", "Marketing", "engineering", "Sales", "Sales", "Marketing", "Engineering", "Sales", "Engineering", "marketing"]`

**Cardinality check:**
```
unique_count = 5 (Engineering, Marketing, engineering, Sales, marketing)
total_count = 10
5/10 = 50% > 1% (unique threshold) → No low cardinality issue
```

**Inconsistency check:**
```
Normalise each value (lowercase + strip):
"Engineering" → "engineering"
"Marketing"   → "marketing"
"engineering" → "engineering"  ← SAME as "Engineering" after normalisation!
"marketing"   → "marketing"   ← SAME as "Marketing" after normalisation!

Inconsistent groups found:
  "engineering": ["Engineering", "engineering"]
  "marketing":   ["Marketing", "marketing"]

Affected count = 3 + 2 = 5 rows
```

**Issue created:**
```python
QualityIssue(
    column="department",
    issue_type="inconsistent_values",
    severity="warning",
    message="Potential inconsistent values (different casing/spacing)",
    affected_count=5,
    affected_percentage=50.0,
    details={"examples": ["Normalised 'engineering': ['Engineering', 'engineering']",
                          "Normalised 'marketing': ['Marketing', 'marketing']"]}
)
```

## 17.5 Step 4: Column Analysis (DateTime — "hired_date")

```
min_date = "2019-03-22"
max_date = "2023-05-01"
date_range_days = 1501 days
future_dates = 0 (all in the past)
```

No issues detected (no future dates).

## 17.6 Step 5: Generating the Report

```python
reporter = QualityReportGenerator(analyzer)
html = reporter.generate_html_report(theme="creative")
```

The reporter collects all the issues, formats them, applies Jinja2 templating, and generates a complete HTML file with:
- Summary cards (10 rows, 4 columns, X critical issues)
- Issues table (sorted by severity)
- Recommendations
- Missing data overview

## 17.7 Step 6: Using `get_problematic_rows()`

```python
bad_age_rows = analyzer.get_problematic_rows("age", "outliers")
```

**Inside the function:**
```
Re-computes IQR boundaries for "age":
  Lower = 15.0, Upper = 43.0

Boolean mask: is 150 > 43? → True
              is 25 > 43?  → False
              ... etc.

Returns df[mask] = only the row where age=150
```

```
   age   salary  department  hired_date
2  150   99000   engineering 2023-01-10
```

This is the row you send to the data team to fix!

## 17.8 Step 7: Drift Detection (Later, When New Data Arrives)

```python
# 3 months later, you get October data
df_october = pd.read_csv("october_data.csv")

# Create analyzers for both
ref_analyzer = pdq.analyze_dataframe(df_january, name="January")
curr_analyzer = pdq.analyze_dataframe(df_october, name="October")

# Compare them
drift_results = pdq.compare_drift(ref_analyzer, curr_analyzer)
```

**`compare_drift` calls `DataQualityComparator.compare_distributions()`**

For each common column:
1. Computes PSI → tells you how much the distribution shifted
2. Computes KS test → tells you if the shift is statistically significant

```
drift_results DataFrame:
column    dtype    psi     drift_status  pct_change  ks_stat  ks_pvalue
age       float64  0.15    moderate      +2.3%       0.18     0.032
salary    float64  0.08    stable        -1.1%       0.12     0.187
```

Interpretation: 
- `age` has **moderate drift** (PSI=0.15) and the KS test is significant (p=0.032 < 0.05) — the age distribution genuinely changed.
- `salary` is **stable** (PSI=0.08) and KS is not significant (p=0.187 > 0.05) — the salary distribution change is just random noise.

---

# CHAPTER 18: Key Concepts Quick Reference

## Formulas Summary

| Concept | Formula | Code |
|---|---|---|
| Mean | `μ = Σxᵢ / n` | `df[col].mean()` |
| Standard Deviation | `σ = √(Σ(xᵢ-μ)² / n)` | `df[col].std()` |
| IQR | `IQR = Q3 - Q1` | `q3 - q1` |
| Lower Fence | `Q1 - 1.5 × IQR` | `q1 - 1.5 * iqr` |
| Upper Fence | `Q3 + 1.5 × IQR` | `q3 + 1.5 * iqr` |
| Shannon Entropy | `H = -Σ pᵢ × log₂(pᵢ)` | `-np.sum(p * np.log2(p))` |
| PSI | `Σ (curr - ref) × ln(curr/ref)` | `np.sum((c-r) * np.log(c/r))` |
| KS Statistic | `D = max|CDF₁ - CDF₂|` | `np.max(np.abs(cdf1 - cdf2))` |
| KS p-value | `2 × e^(-2λ²), λ = D√(n₁n₂/(n₁+n₂))` | `2.0 * math.exp(-2.0 * val**2)` |
| Missing % | `(missing / total) × 100` | `isnull().sum() / len() * 100` |

## Thresholds Summary

| Check | Warning | Critical |
|---|---|---|
| Missing values | > 5% | > 30% |
| Outliers | < 10% of column | ≥ 10% of column |
| Skewness | — | > ±1.0 (info only) |
| PSI drift | ≥ 0.10 (moderate) | ≥ 0.25 (significant) |
| KS test p-value | — | < 0.05 (significant) |

## Design Patterns Used

| Pattern | Where | Purpose |
|---|---|---|
| Facade | `__init__.py` convenience functions | Hide complexity from users |
| Composition | `Reporter` has `Analyzer` | Flexible, loosely coupled design |
| Strategy | theme="creative"/"professional" | Swap report formats easily |
| Dataclass | `QualityIssue`, `ColumnStats` | Structured, typed data containers |
| Defensive programming | `try/except` blocks | Never crash on bad data |

---

*PyDataQuality v0.1.0 — Technical Study Guide | May 2026*
