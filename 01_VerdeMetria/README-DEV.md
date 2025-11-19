# VerdeMetria - Developer Guide

## Development Workflow

### Branch Policy

- `main`: Stable, production-ready code
- `dev`: Integration branch for ongoing development
- `feature/xxx`: Feature branches for specific tasks
- `fix/xxx`: Bug fix branches

### Making Changes

1. Create a feature branch from `main`:
```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

2. Make your changes following the coding style (see below)

3. Run tests locally:
```bash
pytest tests/ -v
```

4. Commit your changes with clear messages:
```bash
git add .
git commit -m "feat: add feature description"
```

5. Push and open a Pull Request:
```bash
git push origin feature/your-feature-name
```

### Running Tests

Run all tests:
```bash
pytest tests/
```

Run specific test file:
```bash
pytest tests/test_processing.py -v
```

Run with coverage:
```bash
pytest tests/ --cov=src/verdemetria --cov-report=html
```

### Coding Style

- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Write docstrings for all public functions (Google style)
- Keep functions focused and single-purpose
- Maximum line length: 100 characters

Example:
```python
def compute_ndvi_array(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """
    Compute NDVI from red and NIR arrays.
    
    Args:
        red: Red band array (wavelength ~665nm)
        nir: Near-infrared band array (wavelength ~842nm)
        
    Returns:
        NDVI array with values in range [-1, 1]
    """
    return (nir - red) / (nir + red + 1e-8)
```

### Linting

Run flake8 (if installed):
```bash
flake8 src/ scripts/ --max-line-length=100
```

### Adding New Dependencies

1. Add to `environment.yml` under appropriate section
2. Update the environment:
```bash
conda env update -f environment.yml --prune
```

### Opening Pull Requests

**PR Title Format:**
- `feat: description` for new features
- `fix: description` for bug fixes
- `docs: description` for documentation
- `test: description` for test additions
- `refactor: description` for refactoring

**PR Body Should Include:**
- Summary of changes
- Related issue numbers
- Testing performed
- Any breaking changes

### Code Review Guidelines

- Keep PRs focused and small
- Respond to review comments promptly
- Update tests for any logic changes
- Ensure CI passes before requesting review

### Local Development Tips

1. Use `tsc --watch` equivalent for Python (optional):
```bash
pytest-watch tests/
```

2. Interactive development in notebooks:
   - Keep exploratory work in `notebooks/`
   - Extract reusable code to `src/verdemetria/`

3. Debugging rasters:
```bash
gdalinfo outputs/ndvi.tif
rio info outputs/ndvi.tif
```

### Troubleshooting

**Environment issues:**
```bash
conda deactivate
conda env remove -n ndvi
conda env create -f environment.yml
```

**Import errors:**
Make sure you're in the project root and the package is importable:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Questions?

Open an issue or reach out to the maintainers.
