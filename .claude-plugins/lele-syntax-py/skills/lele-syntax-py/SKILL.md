---
name: lele-syntax-py
description: Use for Python code in this project. Enforces atomic file structure (*Method/ subpackages), new-import-system, dataclass/enum patterns, pytest markers, loguru logging, PascalCase subpackages, and __HELPER_DIR__ conventions.
---

# Project Conventions (Python)

This project uses a custom `new-import-system` for absolute imports. All rules here override standard Python conventions.

## 1. Import System: new-import-system

### Top-level `__init__.py`

Every top-level package `__init__.py` must install it:

```python
import new_import_system
new_import_system.install(__file__)
```

### What it does

`new-import-system` (GitHub: https://github.com/Uomocosa/new-python-import-system) is an external package that hooks into Python's import machinery. After `.install(__file__)` is called, it enables:

1. **Lazy submodules** — subpackages are loaded on demand, not eagerly, via a `LazyModule` wrapper over `pkgutil.iter_modules`.
2. **Callable packages/modules** — if a package has a function named `__call__` or with the same name as the package, calling the package directly invokes that function.
3. **Empty `__init__.py`** — you are expected to keep all `__init__.py` files (except the top-level one) empty. The import hook handles resolution without relying on `__init__.py` contents.

**Dependency** (from `pixi.toml`):
```toml
[pypi-dependencies]
new-import-system = { git = "https://github.com/Uomocosa/new-python-import-system" }
```

If something behaves unexpectedly (wrong module resolved, eager loading, callable not triggering), inspect the source at `https://github.com/Uomocosa/new-python-import-system/tree/master/new_import_system` — the package is small (< 500 lines across `__init__.py`, `set_lazy_submodules.py`, `make_module_callable.py`, `LazyModule.py`, `P.py`).

### Import Rules

- **NEVER use relative imports** (`from .Module import ...` is forbidden)
- **Always use absolute imports** (e.g., `import {{package}}`, `from {{package}}.Module import MyClassMethod`)
- **No need to repeat module name** in function calls when the module name matches the function name:

```python
# Instead of (repeating the function name when it is the only export):
{{package}}.Module.MyClassMethod.my_function(df, options)

# Do (no repetition, function name is inferred):
{{package}}.Module.MyClassMethod(df, options)
```

### Empty `__init__.py` Files

All `__init__.py` files EXCEPT the top-level one must be **empty**:

```
{{package}}/
├── __init__.py          # Contains new-import-system installation
├── Module/
│   ├── __init__.py      # EMPTY
│   ├── MyClass.py
│   └── MyClassMethod/
│       ├── __init__.py  # EMPTY
│       └── my_method.py
```

## 2. Code Granularity & Organization

### Dataclasses, Enums, and Functions

Prefer dataclasses and enums for structured data. Regular functions are also welcome at the package level.

```python
from dataclasses import dataclass
from enum import IntEnum

@dataclass
class Config:
    csv_file: Path
    max_size: int = 100

class Status(IntEnum):
    UNKNOWN = -1
    INACTIVE = 0
    ACTIVE = 1

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    return df[df['value'] > 0]
```

**Never use manual `__init__`** in classes that should be dataclasses.

### Method Subpackages: `ClassNameMethod/`

When a dataclass needs methods, create a subpackage named `ClassNameMethod/` and implement methods there.

```
{{package}}/Module/
├── MyClass.py              # Dataclass definition
└── MyClassMethod/
    ├── __init__.py         # EMPTY
    ├── my_method.py        # Method implementation
    └── process_data.py
```

**Dataclass references methods via the subpackage:**

```python
# {{package}}/Module/MyClass.py
from dataclasses import dataclass
import {{package}}

@dataclass
class MyClass:
    data: pd.DataFrame
    config: Config

    def my_method(self, options=MyClassMethod.my_method.Options()):
        return MyClassMethod.my_method(self.data, options)

    def another_method(self, options=MyClassMethod.another_method.Options()):
        return MyClassMethod.another_method(self.data, options)
```

**Caution — lazy resolution timing:** The new-import-system may not have resolved `MyClassMethod` at class-definition time when the default arguments above are evaluated. If you encounter `NameError` on `MyClassMethod`, use `None` as the default and resolve inside the method body:

```python
def my_method(self, options=None):
    if options is None:
        options = MyClassMethod.my_method.Options()
    return MyClassMethod.my_method(self.data, options)
```

### Function Organization in Method Modules

Each method file follows this pattern:

```python
# {{package}}/Module/MyClassMethod/my_method.py
from dataclasses import dataclass, field
import pandas as pd
import {{package}}

@dataclass
class Options:
    option_a: str = "default_value"
    n_points: int = 2

def my_method(df: pd.DataFrame, options: Options = Options()) -> pd.DataFrame:
    return df

def test_usage():
    from {{package}}.__global__ import DATA_DIR
    df = pd.read_csv(DATA_DIR / "data.csv")
    df = my_method(df, Options(option_a="value"))
    assert len(df) > 0
```

## 3. Testing Conventions

### `test_usage()` Function Pattern

Every module (function, dataclass, enum) must have at least one `test_usage()` function with **no arguments**:

```python
def test_usage():
    from {{package}}.__global__ import DATA_DIR
    config = Config(csv_file=DATA_DIR / "data.csv")
    instance = MyClass(config)
    instance.my_method()
    logger.info(f"Data shape: {instance.data.shape}")
```

### Multiple Test Functions

Use descriptive names when testing different aspects:

```python
def test_method_a():
    pass

def test_method_b():
    pass

def test_complete_workflow():
    pass
```

### Pytest Markers

Use pytest markers to categorize and control test execution.

#### Defining markers in pyproject.toml

```toml
[tool.pytest.ini_options]
markers = [
    "above10s: Test takes more than 10 seconds",
    "todo: Feature not yet implemented",
    "unreliable: Depends on external factors",
    "verbose: Test with visible output",
    "infinite: Will not finish",
]
```

#### Available Markers

```python
import pytest

@pytest.mark.above10s       # Long-running test (>10s)
def test_long_running():
    pass

@pytest.mark.todo           # Feature not yet implemented
def test_not_yet_implemented():
    pass

@pytest.mark.unreliable     # Depends on external factors
def test_external_dependency():
    pass

@pytest.mark.verbose        # Tests with printed output
def test_with_output():
    pass

@pytest.mark.infinite       # Will not finish
def test_wont_finish():
    pass

@pytest.mark.skip(reason="Needed once for specific debugging")  # pytest built-in
def test_debug_one_time():
    pass
```

#### Running with markers

```bash
# Run only fast tests (skip slow)
pytest -m "not above10s"

# Run todo tests
pytest -m "todo"

# Skip unreliable tests in CI
pytest -m "not unreliable"

# Run verbose tests with output
pytest -m "verbose" -s
```

## 4. Global Constants: `__global__.py` (MANDATORY)

Every package **must** have a `__global__.py` at the top level for constants and shared configuration:

```python
from pathlib import Path

REPO_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = REPO_DIR / 'DATA'
RESULTS_DIR = REPO_DIR / 'RESULTS'

from joblib import Memory
CACHE_MEMORY = Memory(location=".cache_dir", verbose=0)
```

Each subpackage can also have its own `__global__.py`.

## 5. Code Style Rules

### No Comments (Unless Required)

Code should be self-documenting through clear naming.

### No `if __name__ == "__main__"`

Never use `if __name__ == "__main__":` blocks. Use test functions instead.

### Logging with loguru

```python
from loguru import logger

logger.debug(f"Processing {len(df)} rows")
logger.info("Operation completed successfully")
logger.warning("Missing data detected")
```

## 6. Directory Structure

```
{{package}}/
├── __init__.py              # new-import-system installation
├── __global__.py            # Global constants
├── ModuleA/
│   ├── __init__.py          # EMPTY
│   ├── __global__.py        # Module-specific constants
│   ├── Config.py            # Config dataclass
│   ├── MyClass.py           # Main dataclass
│   └── MyClassMethod/       # Methods for MyClass
│       ├── __init__.py      # EMPTY
│       ├── my_method.py
│       └── ...
```

### Top-Level Package Naming

The top-level package folder must be in `snake_case` and **must match `[project].name` in `pyproject.toml`**.

### Subpackage Naming (PascalCase)

All subpackages (folders with `__init__.py`) must use **PascalCase**:

```
✅ MyPackage/, ModuleA/, BioInformatics/, Utils/
❌ {{package}}/, module_a/, bio_informatics/
```

### `__HELPER_DIR__` Convention

Each top-level package should contain a `__HELPER_DIR__` subfolder for non-code assets with a `.gitkeep` file:

```
{{package}}/
├── __init__.py
├── __HELPER_DIR__/
│   ├── .gitkeep
│   └── template.txt
└── __global__.py
```

Import pattern:
```python
from {{package}}.__global__ import HELPER_DIR
```

## 7. Naming Conventions Summary

| Element | Convention | Example |
|---------|------------|---------|
| **Top-level package** | snake_case | `{{package}}/` |
| **Subpackages** | PascalCase | `Utils/`, `BioInformatics/` |
| **Classes** | PascalCase | `MyClass`, `Config` |
| **Enums** | PascalCase | `Status`, `LogLevel` |
| **Functions** | snake_case | `my_function`, `process_data` |
