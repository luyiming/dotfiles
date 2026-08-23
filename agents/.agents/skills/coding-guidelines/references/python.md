## Python Coding Guidelines

### Python Version Compatibility

- Do not support Python 2 or add `__future__` imports for Python 2 compatibility.
- When using features that vary across Python 3 releases, check the nearest `pyproject.toml` and respect its `requires-python` minimum version.
