# GymMax - E-Gym Progress Dashboard

A Flask-based dashboard for visualizing and tracking your training progress on E-Gym machines. Data is read directly from an Excel export file.

## Features

- **Clear Dashboard**: View all exercises, current maximum weights, and the difference from the last strength measurement.
- **Detailed Analysis**: Interactive progress charts (Plotly) for each individual exercise.
- **History**: Tabular view of your previous best performances.
- **Highlights**: Automatic detection of the most recent increase and identification of stagnating exercises.
- **Category Grouping**: Exercises are automatically grouped by muscle groups (Upper Body, Core, Lower Body).

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/gymmax.git
    cd gymmax
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  (Optional) Copy your E-Gym data (`Egym Gewichte.xlsx`) into the main directory.

## Usage

Start the application with:

```bash
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.

## Tests

Alle Unit-Tests können mit einem einzigen Befehl ausgeführt werden:

```bash
python -m unittest discover tests
```

## Project Structure

- `app.py`: Main application (Flask server and routing).
- `data_manager.py`: Data access and processing logic (encapsulation).
- `Egym Gewichte.xlsx`: Data source (standard export format).
- `templates/`: HTML templates for the frontend.
- `requirements.txt`: Required Python libraries.
- `tests/`: Enthält Unit-Tests für Datenmanagement und die Web-App.
- `AI.md`: Context and guidelines for AI agents.
- `ARCHITECTURE.md`: Technical documentation of the system.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.
