import json
from datetime import datetime
from flask import Flask, render_template, abort
import plotly.express as px
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
    if len(series) > 2:  # Need at least 3 points for a more stable trend
        # Convert dates to numbers (days since first measurement)
        first_date = series['Datum'].min()
        days_since_start = (series['Datum'] - first_date).dt.days
        x = days_since_start.values
        y = series[name].values
        
        # Logarithmic model (y = a * ln(x + 1) + b) to account for diminishing returns
        # x+1 to avoid log(0)
        x_log = np.log(x + 1)
        params = np.polyfit(x_log, y, 1)  # [a, b]
        a, b = params
        
        # Calculate trendline for existing points
        series['Trendline'] = a * np.log(x + 1) + b
        
        # Extrapolate to end of current quarter
        today = datetime.now()
        current_quarter = (today.month - 1) // 3 + 1
        last_month_of_quarter = current_quarter * 3
        
        import calendar
        _, last_day = calendar.monthrange(today.year, last_month_of_quarter)
        quarter_end = datetime(today.year, last_month_of_quarter, last_day)
        
        # If quarter end is already passed or very close, go to next quarter end
        if (quarter_end - today).days < 14:
            next_q = (current_quarter % 4) + 1
            next_y = today.year + (1 if current_quarter == 4 else 0)
            _, last_day = calendar.monthrange(next_y, next_q * 3)
            quarter_end = datetime(next_y, next_q * 3, last_day)

        # Generate points for extrapolation (from last measurement to quarter end)
        # Limit extrapolation to a reasonable timeframe (max 30 days from today)
        extrapolate_to = min(quarter_end, today + pd.Timedelta(days=30))
        future_days = (extrapolate_to - first_date).days
        x_future = np.linspace(x[-1], future_days, 20)
        y_future = a * np.log(x_future + 1) + b
        dates_future = [first_date + pd.Timedelta(days=int(d)) for d in x_future]
        
        trend_data = pd.DataFrame({
            'Datum': dates_future,
            'Trendline': y_future
        })
        
        # Prediction for next target (next 5kg or 10kg increment)
        target_weight = ((latest_val // 5) + 1) * 5
        # If trend is positive (a > 0)
        if a > 0.01:
            # target = a * ln(x_target + 1) + b => (target - b) / a = ln(x_target + 1)
            # => x_target = exp((target - b) / a) - 1
            days_to_target = np.exp((target_weight - b) / a) - 1
            target_date = first_date + pd.Timedelta(days=int(days_to_target))
            prediction_info = {
                'target_weight': int(target_weight),
                'target_date': target_date.strftime('%d.%m.%Y'),
                'days_remaining': (target_date - datetime.now()).days
            }

    # Create Plotly figure
    fig = px.line(series, x='Datum', y=name, title=f'Fortschritt: {name}',
                  markers=True, text=name, template='plotly_dark')
    
    # Add trendline if available
    if not trend_data.empty:
        # Full trendline: existing part + future part
        # Combine existing trend and future trend for a continuous line
        full_trend_x = pd.concat([series['Datum'], trend_data['Datum']])
        full_trend_y = pd.concat([series['Trendline'], trend_data['Trendline']])
        
        fig.add_scatter(x=full_trend_x, y=full_trend_y, mode='lines', 
                        name='Trend (Logarithmisch)', line=dict(dash='dash', color='rgba(0, 255, 100, 0.6)'))
    
    fig.update_traces(cliponaxis=False, textposition="top center", selector=dict(type='scatter', mode='lines+markers+text'))
    fig.update_layout(
        xaxis_title='Datum',
        yaxis_title='Gewicht (kg)',
        hovermode='x unified',
        yaxis=dict(rangemode='tozero', zeroline=True, gridcolor='rgba(255,255,255,0.1)'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)')
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
