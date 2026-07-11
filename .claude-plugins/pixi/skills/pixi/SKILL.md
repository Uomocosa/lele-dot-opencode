---
name: pixi
description: Use when the user wants to run tests, install dependencies, build the project, or manage the Python environment via pixi. Covers pytest invocation, environment activation, dependency management, and common pixi commands.
---

# Pixi Environment & Testing

This project uses **pixi** for environment and dependency management. This skill covers the relevant commands.

## 1. Running Tests

### Run All Tests

```bash
pixi run pytest
```

### Run a Specific Test File

```bash
pixi run pytest path/to/test.py
```

### Run a Specific Test Function

```bash
pixi run pytest path/to/test.py::test_function -o "addopts="
```

### Run with Verbose/Print Output

```bash
pixi run pytest -s -v path/to/test.py::test_function
```

### Run Without Default Marker Filters

If the project's `pyproject.toml` sets default marker filters (e.g., `addopts = "-m 'not slow'"`), override them with:

```bash
pixi run pytest -m "" path/to/test.py -o "addopts="
```

## 2. Environment Management

### Activate Environment

```bash
pixi shell
```

### Install a New Dependency

```bash
pixi add <package-name>
```

### Install a Development Dependency

```bash
pixi add --dev <package-name>
```

### Update Lockfile

```bash
pixi update
```

## 3. Lint

```bash
pixi run ruff
```

## 4. Build

Build the package:

```bash
pixi run build
```

## 5. Missing Features

This skill covers commonly used pixi commands. If the user asks for a pixi
feature not listed here (e.g., multi-environment, conda-forge channels, etc.),
search online at `https://pixi.sh/latest/` for the relevant command.
