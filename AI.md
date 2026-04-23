# AI Context for GymMax

This document contains specific information for AI agents working on this repository.

## CRITICAL RULES
- **NEVER delete the `Egym Gewichte.xlsx` file.** This file is the central data source and must never be removed or renamed by an AI agent.

## Project Mission
GymMax is a simple, local solution to visualize E-Gym progress without having to upload sensitive data to the cloud.

## Key Code Patterns

### Data Schema
- The Excel file has a specific format: the first 3 lines are often metadata or empty. The header begins at index 3 (4th row).
- Column names correspond to the names of the fitness machines/exercises.
- There is always a `Datum` (Date) column.
- **CRITICAL**: The entries represent individual strength measurements (Kraftmessungen), not regular training sessions. A date indicates when a strength test was performed.
- Categories (Upper body/Core/Lower body) are specified in the 3rd row (index 2).

### Error Handling
- Since the Excel file is exported manually, `NaN` values can occur in the exercise columns. These must be handled with `.dropna()` during loading and processing.
- Routes should return a `404` error if an exercise does not exist.
- Input validation for Excel file presence and format should be implemented.

### Style & Refactoring Guidelines
- **Solid Principles**: Maintain a clear separation of concerns. Data logic stays in `data_manager.py`, presentation in templates, and routing in `app.py`.
- **DRY (Don't Repeat Yourself)**: Extract common logic into reusable methods within `GymDataManager`.
- **Type Hinting**: All new functions and methods must use Python type hints for better maintainability and IDE support.
- **Refactoring First**: Before adding complex new features, check if existing code needs refactoring to support the change cleanly.
- **English Only**: All code identifiers, comments, docstrings, and documentation must be in English.
- **Variable Naming**: Use descriptive, intention-revealing names (e.g., `days_since_last_measurement` instead of `d`).
- **Function Size**: Keep functions focused and small. If a function does too many things, split it.

## Known Limitations
- The application currently re-reads data on every request. For large datasets, a caching mechanism should be considered.
- Icon mapping is based on simple string matching.

## Expected Behaviors
- When implementing new features, write appropriate tests (e.g., in `tests/`).
- Ensure `requirements.txt` remains up-to-date when adding new libraries.
- Maintain clean encapsulation and separation of concerns.
