# Project Architecture: GymMax

This document describes the technical structure of GymMax to provide developers and AI agents with a better understanding of the system.

## System Overview

GymMax is a monolithic web application based on the Flask framework. It serves as a visualization layer for training data stored in an Excel file.

## Data Flow

1.  **Data Source**: An Excel file (`Egym Gewichte.xlsx`).
    - Format: A `Datum` (Date) column and additional columns for each exercise.
    - Context: Each entry represents a strength measurement (Kraftmessung).
    - Metadata: The headers are located in the 4th row (index 3).
2.  **Data Management (`data_manager.py`)**:
    - `GymDataManager`: Encapsulates all data access and processing logic.
    - `load_data_with_categories()`: Reads the Excel file with `pandas`, handles multi-level headers for categories, and cleans the data.
    - `get_all_stats(df)`: Calculates the current maximum weight, difference from the previous measurement, and the date of the last increase for each exercise.
3.  **Routing (`app.py`)**:
    - `/`: Displays the dashboard with aggregated statistics and overview.
    - `/exercise/<name>`: Displays the detailed page for a specific exercise.
4.  **Visualization**:
    - `plotly.express`: Generates interactive line charts from the pandas DataFrames.
    - `Flask Templates`: Render HTML (Jinja2) using Bootstrap for styling.

## Key Components

### Backend (`app.py`, `data_manager.py`)
Responsible for handling web requests, calling the data manager, and providing data to the frontend templates.

### Frontend (`templates/`)
- `layout.html`: Base layout with navigation bar and common assets.
- `index.html`: Dashboard view.
- `details.html`: Detailed view for an exercise, including a Plotly chart.

### Testing
- `test_stats.py`: Unit tests for statistical calculations and data management.
- Integration tests for routes can be added in `test_app.py`.

## External Dependencies
- **Pandas**: Data manipulation and processing.
- **Plotly**: Chart generation.
- **Flask**: Web framework.
- **Openpyxl**: Engine for reading Excel files.
- **Bootstrap**: UI styling framework.
