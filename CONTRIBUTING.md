# Contributing to GymMax

Thank you for your interest in contributing to GymMax! Here are some guidelines to help you get started.

## How Can I Contribute?

### Reporting Bugs

- Use GitHub Issues to report bugs.
- Describe the bug in as much detail as possible and provide steps to reproduce it.

### Suggesting New Features

- Create an issue and describe your desired feature.
- Discuss the feature before starting the implementation.

### Submitting Pull Requests

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/my-new-feature`).
3.  Implement your changes.
4.  **Refactoring**: Ensure your code follows the refactoring guidelines in `AI.md` (SOLID, DRY, Type Hinting).
5.  **Documentation**: Update `README.md`, `ARCHITECTURE.md`, or `AI.md` if your changes affect the system structure or AI guidelines.
6.  **Language**: All comments and documentation must be in English.
7.  **Testing**: Ensure all tests pass (see below).
8.  Commit your changes with a meaningful message.
9.  Push the branch and create a Pull Request.

## Development Environment

To work on GymMax, install the development dependencies:

```bash
pip install -r requirements.txt
# If additional test tools are needed:
pip install pytest
```

### Running Tests

Before submitting changes, make sure the tests run successfully:

```bash
python -m unittest test_stats.py
```

## Code Style

- Adhere to the existing code style (PEP 8 for Python).
- **All comments and documentation must be in English.**
- Document new functions and classes appropriately using type hints.
- Ensure your changes keep the user interface consistent.
- Encapsulate data logic within the `GymDataManager` class.
