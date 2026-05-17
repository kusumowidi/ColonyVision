# Contributing to ColonyVision AI

Thank you for your interest in contributing! This document explains how to report issues, propose features, and submit pull requests.

> ColonyVision AI is a **research and educational prototype**, not a certified medical device. Please keep this context in mind when proposing changes.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Reporting Bugs](#reporting-bugs)
- [Requesting Features](#requesting-features)
- [Development Setup](#development-setup)
- [Project Architecture Rules](#project-architecture-rules)
- [Coding Conventions](#coding-conventions)
- [Testing](#testing)
- [Submitting a Pull Request](#submitting-a-pull-request)

---

## Code of Conduct

Be respectful and constructive. Discrimination, harassment, or abusive language will not be tolerated.

---

## Reporting Bugs

Before opening an issue, please:

1. Check whether the bug is already reported in [Issues](../../issues).
2. Reproduce the bug on the **latest commit** of `main`.

When opening a bug report, include:

- **Python version** (`python --version`)
- **PySide6 version** (`pip show PySide6`)
- **Operating system** (e.g., Windows 11, Ubuntu 22.04, macOS 14)
- **Steps to reproduce** — as minimal as possible
- **Expected vs. actual behaviour**
- **Error traceback** (full text, not a screenshot)
- Sample image if the bug is image-specific (use a royalty-free or synthetic image)

---

## Requesting Features

Open a GitHub Issue with the label `enhancement`.

Describe:

- The **use case** — why is this needed in a lab/research workflow?
- The **proposed behaviour**
- Any relevant references (papers, existing tools, lab standards)

Features that introduce cloud services, deep-learning model weights, or database dependencies will not be accepted into the MVP branch. These belong in a `feature/*` branch or a separate discussion thread.

---

## Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/ColonyVision.git
cd ColonyVision

# Create a virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS / Linux)
source .venv/bin/activate

# Install dependencies (includes pytest)
pip install -r requirements.txt
```

---

## Project Architecture Rules

| Rule | Rationale |
|---|---|
| GUI code lives in `gui/` | Keeps UI separate from CV logic |
| CV code lives in `core/` | Allows future detector backends |
| Data models live in `models/` | Single source of truth for shared types |
| No cloud services or databases in MVP | Local-only prototype requirement |
| No deep-learning weights in MVP | Keeps install footprint small |
| Preserve `count_colonies(image, params)` signature | Enables future detector swaps without GUI changes |
| Use colony statuses consistently | `valid`, `artifact`, `merged`, `manual_added`, `removed` |
| Confidence score is a heuristic | Never present it as a trained model probability |
| CFU/ml formula is fixed | `count × dilution_factor ÷ plated_volume_ml` |

---

## Coding Conventions

- **Python 3.10+** syntax.
- Use `from __future__ import annotations` at the top of every module.
- Type-annotate all public functions and class attributes.
- Use `@dataclass` for data models.
- Docstrings for all public functions (one-liner or NumPy style for complex ones).
- Keep modules focused: one responsibility per file.
- Do not add `print()` statements to core logic — use return values or exceptions.
- Format with [Black](https://black.readthedocs.io/) (88-character line length):

```bash
pip install black
black .
```

---

## Testing

All PRs must include tests for new behaviour.

```bash
# Run the full test suite
pytest

# Run with coverage (requires pytest-cov)
pip install pytest-cov
pytest --cov=core --cov=models --cov-report=term-missing
```

### Writing Tests

- Place tests in `tests/`.
- Use **synthetic images** (generated with OpenCV or NumPy) — do not commit real Petri dish photos.
- Name test files `test_<module>.py` and test functions `test_<behaviour>`.
- Avoid slow I/O in unit tests; use `tmp_path` (pytest fixture) for file-write tests.

Example test for a new core function:

```python
# tests/test_my_feature.py
from core.my_module import my_function

def test_my_function_returns_expected_value():
    result = my_function(input_value=42)
    assert result == expected_value
```

---

## Submitting a Pull Request

1. **Create a branch** from `main`:

   ```bash
   git checkout -b feature/short-description
   # or
   git checkout -b fix/short-description
   ```

2. **Make your changes** following the conventions above.

3. **Run tests** and ensure they pass:

   ```bash
   pytest
   ```

4. **Commit** with a clear message:

   ```
   feat(core): add adaptive watershed strength scaling
   fix(gui): correct coordinate mapping in image_viewer edit mode
   docs: update CFU/ml formula section in README
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/) where possible.

5. **Push** your branch and open a Pull Request against `main`.

6. In your PR description:
   - Summarise **what** changed and **why**.
   - Reference any related Issues (`Closes #42`).
   - List any **manual testing** you performed.

---

## Questions?

Open a [GitHub Discussion](../../discussions) or an Issue tagged `question`.
