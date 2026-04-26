import json
import os
from datetime import datetime
from flask import Flask, render_template, abort
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go
import plotly.utils
import pandas as pd
import numpy as np

from data_manager import GymDataManager

load_dotenv()

app = Flask(__name__)
data_manager = GymDataManager()


def get_template_data(df, category_map, category_order, stats):
    """
    Helper to prepare common template data.
    """
    categories = []
    stats_by_category = {cat: [] for cat in category_order}
    for cat in category_order:
        cat_stats = [s for s in stats if s.get('category') == cat]
        categories.append({'name': cat, 'exercises': [s['name'] for s in cat_stats]})
        stats_by_category[cat] = cat_stats
    
    return categories, stats_by_category


def calculate_trend_and_prediction(series: pd.DataFrame, exercise_name: str, ex_stat: dict) -> tuple:
    """
    Calculates trendline and predicts next target weight.
    """
    m, c = 0.0, 0.0
    prediction_info = None
    trend_data = pd.DataFrame()
    first_recent_date = None

    if len(series) >= 3:
        recent_points = series.tail(8).copy()
        first_recent_date = recent_points['Datum'].min()
        x_recent = (recent_points['Datum'] - first_recent_date).dt.days.values
        y_recent = recent_points[exercise_name].values
        
        weights = np.linspace(1.0, 2.5, len(y_recent))
        m, c = np.polyfit(x_recent, y_recent, 1, w=weights)
        
        # Prediction
        latest_val = ex_stat.get('current_max', 0.0)
        target_weight = ((latest_val // 5) + 1) * 5
        
        if m > 0.05:
            days_to_target = (target_weight - c) / m
            target_date = first_recent_date + pd.Timedelta(days=int(days_to_target))
            
            if target_date < datetime.now():
                target_date = datetime.now() + pd.Timedelta(days=max(1, int(5/m) if m > 0 else 7))

            prediction_info = {
                'target_weight': int(target_weight),
                'target_date': target_date.strftime('%d.%m.%Y'),
                'days_remaining': (target_date - datetime.now()).days
            }

        # Trendline visualization data
        extrapolate_to = datetime.now() + pd.Timedelta(days=30)
        future_days_max = (extrapolate_to - first_recent_date).days
        x_trend = np.array([0, future_days_max])
        y_trend = m * x_trend + c
        dates_trend = [first_recent_date + pd.Timedelta(days=int(d)) for d in x_trend]
        
        trend_data = pd.DataFrame({'Datum': dates_trend, 'Trendline': y_trend})

    return prediction_info, trend_data


def create_plot_json(series: pd.DataFrame, exercise_name: str, trend_data: pd.DataFrame) -> str:
    """
    Creates a Plotly figure and returns it as JSON.
    """
    fig = go.Figure()
    series_x = series['Datum'].tolist()
    series_y = series[exercise_name].tolist()
    
    fig.add_trace(go.Scatter(
        x=series_x, y=series_y, mode='lines+markers+text', name='Kraftmessung',
        text=[f"{val:g}" for val in series_y], textposition='top center',
        line=dict(color='#3b82f6', width=4),
        marker=dict(size=10, symbol='circle', line=dict(width=2, color='#ffffff')),
        hovertemplate='<b>Datum</b>: %{x}<br><b>Gewicht</b>: %{y} kg<extra></extra>'
    ))

    if not trend_data.empty:
        fig.add_trace(go.Scatter(
            x=trend_data['Datum'].tolist(), y=trend_data['Trendline'].tolist(),
            mode='lines', name='Trend-Prognose',
            line=dict(color='#10b981', width=2, dash='dash'),
            hovertemplate='<b>Prognose</b><br>Datum: %{x}<br>Gewicht: %{y:.1f} kg<extra></extra>'
        ))
    
    y_range_max = float(max(series[exercise_name].max(), trend_data['Trendline'].max() if not trend_data.empty else 0)) * 1.1
    fig.update_layout(
        template='plotly_dark',
        title=dict(text=f'Entwicklung: {exercise_name}', font=dict(size=22), x=0.05, y=0.95),
        xaxis=dict(title='Datum', gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title='Gewicht (kg)', gridcolor='rgba(255,255,255,0.05)', 
                   range=[float(series[exercise_name].min()) * 0.85, y_range_max]),
        hovermode='x unified', margin=dict(l=50, r=50, t=80, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


@app.route('/')
def index():
    """
    Main dashboard view.
    Displays overall progress, last increased exercise, and stagnating exercises.
    """
    dashboard_data = data_manager.get_dashboard_data()
    return render_template('index.html', **dashboard_data)


@app.route('/exercise/<name>')
def details(name):
    """
    Detailed view for a specific exercise.
    Displays a progress chart and measurement history.
    """
    df, category_map, category_order = data_manager.load_data_with_categories()
    
    if name not in df.columns or name == 'Datum':
        abort(404)

    series = df[['Datum', name]].dropna().sort_values('Datum')
    if series.empty:
        abort(404)

    series[name] = series[name].round(1)

    # Sidebar and general stats
    stats = data_manager.get_all_stats(df, category_map)
    categories, _ = get_template_data(df, category_map, category_order, stats)
    
    ex_stat = next((s for s in stats if s['name'] == name), None)
    if not ex_stat:
        abort(404)

    prediction_info, trend_data = calculate_trend_and_prediction(series, name, ex_stat)
    graph_json = create_plot_json(series, name, trend_data)

    return render_template(
        'details.html',
        name=name,
        categories=categories,
        ex_stat=ex_stat,
        graphJSON=graph_json,
        prediction=prediction_info
    )


@app.route('/ai-coach')
def ai_coach():
    """
    View for generating an AI prompt for training analysis.
    """
    df, category_map, category_order = data_manager.load_data_with_categories()
    stats = data_manager.get_all_stats(df, category_map)
    categories, _ = get_template_data(df, category_map, category_order, stats)
    
    coach_data = data_manager.get_ai_coach_data()

    # Load defaults from .env
    defaults = {
        'gender': os.getenv('DEFAULT_GENDER', ''),
        'age': os.getenv('DEFAULT_AGE', ''),
        'height': os.getenv('DEFAULT_HEIGHT', ''),
        'weight': os.getenv('DEFAULT_WEIGHT', ''),
        'goal': os.getenv('DEFAULT_GOAL', ''),
        'frequency': os.getenv('DEFAULT_FREQUENCY', ''),
        'experience': os.getenv('DEFAULT_EXPERIENCE', ''),
        'notes': os.getenv('DEFAULT_NOTES', '')
    }
    
    return render_template(
        'ai_coach.html',
        categories=categories,
        defaults=defaults,
        **coach_data
    )


if __name__ == '__main__':
    # Running in debug mode for development
    app.run(debug=True)
