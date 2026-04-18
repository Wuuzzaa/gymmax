import json
from datetime import datetime
from flask import Flask, render_template, abort
import plotly.express as px
import plotly.utils
import pandas as pd

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
    if len(series) > 1:
        prev_val = float(series[name].iloc[-2])
        diff = round(latest_val - prev_val, 1)

    # Create Plotly figure
    fig = px.line(series, x='Datum', y=name, title=f'Progress: {name}',
                  markers=True, text=name, template='plotly_dark')
    fig.update_traces(textposition="top center")
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Weight (kg)',
        hovermode='x unified'
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
        history=history
    )


if __name__ == '__main__':
    # Running in debug mode for development
    app.run(debug=True)
