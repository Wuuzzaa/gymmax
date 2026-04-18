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
- Categories (Upper body/Core/Lower body) are specified in the 3rd row (index 2).

### Error Handling
- Since the Excel file is exported manually, `NaN` values can occur in the exercise columns. These must be handled with `.dropna()` during loading and processing.
- Routes should return a `404` error if an exercise does not exist.
- Input validation for Excel file presence and format should be implemented.

### Style Guidelines
- Use `f-strings` for string formatting.
- **All comments must be written in English.**
- Use type hints for functions and methods.
- Use Bootstrap classes for frontend design.
- Encapsulate data logic into classes (e.g., `GymDataManager`).

## Known Limitations
- The application currently re-reads data on every request. For large datasets, a caching mechanism should be considered.
- Icon mapping is based on simple string matching.

## Expected Behaviors
- When implementing new features, write appropriate tests (e.g., in `tests/`).
- Ensure `requirements.txt` remains up-to-date when adding new libraries.
- Maintain clean encapsulation and separation of concerns.
