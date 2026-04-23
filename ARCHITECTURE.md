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
    - `get_all_stats(df)`: Calculates current max weight, relative increase (total %), and difference from the previous measurement.
3.  **Routing (`app.py`)**:
    - `/`: Displays the dashboard with aggregated statistics and overview.
    - `/exercise/<name>`: Displays the detailed page with progress chart, weighted linear regression trendline (based on the last 8 measurements for responsiveness), extrapolation for 30 days, and milestone prediction.
4.  **Visualization**:
    - `plotly.graph_objects`: Generates interactive high-quality charts from the pandas DataFrames.
    - `Flask Templates`: Render HTML (Jinja2) using Bootstrap for styling.

## Key Components

### Backend (`app.py`, `data_manager.py`)
Responsible for handling web requests, calling the data manager, and providing data to the frontend templates.

### Frontend (`templates/`)
- `layout.html`: Base layout with navigation bar and common assets.
- `index.html`: Dashboard view.
- `details.html`: Detailed view for an exercise, including a Plotly chart.

### Testing
- `test_data_manager.py`: Unit tests for data loading and processing logic.
- `test_app.py`: Integration tests for web routes and views.

## Refactoring Principles
To ensure long-term maintainability, the following principles apply:
- **Separation of Concerns**: Keep business logic out of `app.py`. Routes should only coordinate between the `GymDataManager` and the templates.
- **Model-View-Controller (MVC)**: Although not a strict MVC setup, `data_manager.py` acts as the Model, `templates/` as the View, and `app.py` as the Controller.
- **Statelessness**: The application should remain mostly stateless, reading the source of truth from the Excel file.

## External Dependencies
- **Pandas**: Data manipulation and processing.
- **Plotly**: Chart generation.
- **Flask**: Web framework.
- **Openpyxl**: Engine for reading Excel files.
- **Bootstrap**: UI styling framework.
