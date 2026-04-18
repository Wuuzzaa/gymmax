import json
from datetime import datetime
from flask import Flask, render_template, abort
import plotly.express as px
import plotly.graph_objects as go
import plotly.utils
import pandas as pd
import numpy as np

from data_manager import GymDataManager

app = Flask(__name__)
data_manager = GymDataManager()


@app.route('/')
def index():
    """
    Main dashboard view.
    Displays overall progress, last increased exercise, and stagnating exercises.
    """
    df, category_map, category_order = data_manager.load_data_with_categories()
    if df.empty:
        return render_template('index.html', stats_by_category={}, category_order=[], latest_date='N/A')

    stats = data_manager.get_all_stats(df, category_map)

    # Find the exercise that was most recently increased
    last_increased_exercise = None
    latest_increase_time = None
    for stat in stats:
        if stat['last_increase_date']:
            if latest_increase_time is None or stat['last_increase_date'] > latest_increase_time:
                latest_increase_time = stat['last_increase_date']
                last_increased_exercise = stat

    # Find stagnating exercises (longest time without improvement)
    stagnating = [s for s in stats if s['last_increase_date'] is not None]
    stagnating.sort(key=lambda x: x['last_increase_date'])
    top_stagnating = stagnating[:3]

    # Global last measurement date for the badge
    latest_dt = pd.to_datetime(df['Datum']).dropna().max() if 'Datum' in df.columns else None
    latest_date = latest_dt.strftime('%d.%m.%Y') if pd.notna(latest_dt) else 'N/A'

    # Group statistics by category for the UI
    categories = []
    stats_by_category = {cat: [] for cat in category_order}
    for cat in category_order:
        names = [s['name'] for s in stats if s.get('category') == cat]
        categories.append({'name': cat, 'exercises': names})
        stats_by_category[cat] = [s for s in stats if s.get('category') == cat]

    return render_template(
        'index.html',
        categories=categories,
        stats_by_category=stats_by_category,
        category_order=category_order,
        last_increased=last_increased_exercise,
        stagnating=top_stagnating,
        latest_date=latest_date
    )


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

    # Round values for better display in the plot
    series[name] = series[name].round(1)

    # Calculate statistics for this exercise
    latest_dt = series['Datum'].iloc[-1]
    latest_val = round(float(series[name].iloc[-1]), 1)
    latest_date_str = latest_dt.strftime('%d.%m.%Y')
    days_since_last = (datetime.now() - latest_dt).days

    diff = 0.0
    total_increase_pct = 0.0
    if len(series) > 1:
        prev_val = float(series[name].iloc[-2])
        diff = round(latest_val - prev_val, 1)
        
        first_val = float(series[name].iloc[0])
        if first_val > 0:
            total_increase_pct = round(((latest_val - first_val) / first_val) * 100, 1)

    # Trendline calculation and prediction
    prediction_info = None
    trend_data = pd.DataFrame()
    if len(series) >= 3:  # Need at least 3 points for a trend
        # Use last 8 points for trend to be more responsive to recent progress
        recent_points = series.tail(8).copy()
        
        # Convert dates to numbers (days since first of these points)
        first_recent_date = recent_points['Datum'].min()
        x_recent = (recent_points['Datum'] - first_recent_date).dt.days.values
        y_recent = recent_points[name].values
        
        # Weighted linear regression: y = m*x + c
        # We assign more weight to newer data points (recent progress)
        # Weights increase from 1.0 to 2.5 for the most recent point
        weights = np.linspace(1.0, 2.5, len(y_recent))
        m, c = np.polyfit(x_recent, y_recent, 1, w=weights)
        
        # Prediction for next target (next 5kg increment)
        target_weight = ((latest_val // 5) + 1) * 5
        
        # Only predict if trend is positive and not stagnant
        if m > 0.05:  # at least 50g per day increase (~1.5kg per month)
            # Use the trend to find when target_weight is reached
            # target = m * x_target + c  => x_target = (target - c) / m
            days_to_target = (target_weight - c) / m
            target_date = first_recent_date + pd.Timedelta(days=int(days_to_target))
            
            # If predicted date is in the past (due to regression noise), 
            # adjust it to be at least today + some realistic buffer
            if target_date < datetime.now():
                # If we are already near target, maybe it's just 1-2 days away
                target_date = datetime.now() + pd.Timedelta(days=max(1, int(5/m) if m > 0 else 7))

            prediction_info = {
                'target_weight': int(target_weight),
                'target_date': target_date.strftime('%d.%m.%Y'),
                'days_remaining': (target_date - datetime.now()).days
            }
        
        # Generate points for trendline visualization (from first recent point to 30 days future)
        extrapolate_to = datetime.now() + pd.Timedelta(days=30)
        future_days_max = (extrapolate_to - first_recent_date).days
        
        x_trend = np.array([0, future_days_max])
        y_trend = m * x_trend + c
        dates_trend = [first_recent_date + pd.Timedelta(days=int(d)) for d in x_trend]
        
        trend_data = pd.DataFrame({
            'Datum': dates_trend,
            'Trendline': y_trend
        })

    # Create Plotly figure with a modern, clean look
    fig = go.Figure()

    # Convert numpy arrays to lists for JSON serialization to avoid binary encoding in Plotly
    series_x = series['Datum'].tolist()
    series_y = series[name].tolist()
    
    # Add the main progress line (measurements)
    fig.add_trace(go.Scatter(
        x=series_x,
        y=series_y,
        mode='lines+markers+text',
        name='Kraftmessung',
        text=[f"{val:g}" for val in series_y],
        textposition='top center',
        line=dict(color='#3b82f6', width=4),
        marker=dict(size=10, symbol='circle', line=dict(width=2, color='#ffffff')),
        hovertemplate='<b>Datum</b>: %{x}<br><b>Gewicht</b>: %{y} kg<extra></extra>'
    ))

    # Add the trendline if available
    if not trend_data.empty:
        trend_x = trend_data['Datum'].tolist()
        trend_y = trend_data['Trendline'].tolist()
        fig.add_trace(go.Scatter(
            x=trend_x,
            y=trend_y,
            mode='lines',
            name='Trend-Prognose',
            line=dict(color='#10b981', width=2, dash='dash'),
            hovertemplate='<b>Prognose</b><br>Datum: %{x}<br>Gewicht: %{y:.1f} kg<extra></extra>'
        ))
    
    # Elegant dark theme layout
    fig.update_layout(
        template='plotly_dark',
        title=dict(
            text=f'Entwicklung: {name}',
            font=dict(size=22, color='#ffffff'),
            x=0.05,
            y=0.95
        ),
        xaxis=dict(
            title='Datum',
            gridcolor='rgba(255,255,255,0.05)',
            showgrid=True,
            zeroline=False
        ),
        yaxis=dict(
            title='Gewicht (kg)',
            gridcolor='rgba(255,255,255,0.05)',
            showgrid=True,
            zeroline=False,
            # Start y-axis slightly below the minimum value for better focus on progress
            range=[float(series[name].min()) * 0.85, float(max(series[name].max(), trend_data['Trendline'].max() if not trend_data.empty else 0)) * 1.1]
        ),
        hovermode='x unified',
        margin=dict(l=40, r=40, t=80, b=40),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            bgcolor='rgba(0,0,0,0)'
        ),
        plot_bgcolor='rgba(15,23,42,1)',  # Deep slate background
        paper_bgcolor='rgba(15,23,42,1)',
    )
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Sidebar: grouped by categories, only exercises with data
    categories = []
    for cat in category_order:
        names = [ex for ex, ex_cat in category_map.items() 
                 if ex_cat == cat and ex in df.columns and not df[ex].dropna().empty]
        categories.append({'name': cat, 'exercises': names})

    # History for the table (newest first)
    history = series.sort_values('Datum', ascending=False).to_dict('records')
    for h in history:
        h['Datum_str'] = h['Datum'].strftime('%d.%m.%Y')

    current_category = category_map.get(name)

    return render_template(
        'details.html',
        name=name,
        graph_json=graph_json,
        categories=categories,
        current_category=current_category,
        latest_val=latest_val,
        latest_date=latest_date_str,
        days_since_last=days_since_last,
        diff=diff,
        total_increase_pct=total_increase_pct,
        prediction=prediction_info,
        history=history
    )


if __name__ == '__main__':
    # Running in debug mode for development
    app.run(debug=True)
