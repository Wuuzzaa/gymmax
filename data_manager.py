import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any


class GymDataManager:
    """
    Handles loading and processing E-Gym exercise data from Excel files.
    """

    DEFAULT_EXCEL_FILE = 'Egym Gewichte.xlsx'

    def __init__(self, file_path: str = DEFAULT_EXCEL_FILE):
        self.file_path = file_path

    def load_data_with_categories(self) -> Tuple[pd.DataFrame, Dict[str, str], List[str]]:
        """
        Loads the Excel file and extracts exercise data, category mapping, and category order.
        
        Returns:
            Tuple containing:
            - DataFrame with exercise data and 'Datum' column.
            - Dictionary mapping exercise names to categories.
            - List of categories in order.
        """
        try:
            # Read categories (row with Upper body/Core/Lower body) + column names
            raw = pd.read_excel(self.file_path, header=[2, 3])
            
            # Forward-fill categories across columns
            top = pd.Series(raw.columns.get_level_values(0))
            top_ffill = top.ffill()
            bottom = pd.Series(raw.columns.get_level_values(1))
            
            # Set MultiIndex with filled categories
            raw.columns = pd.MultiIndex.from_arrays([top_ffill, bottom])

            # Find Date/Weekday columns
            datum_cols = [col for col in raw.columns if col[1] == 'Datum']
            if not datum_cols:
                return self._fallback_load()

            datum_col = datum_cols[0]

            # Build a flat DataFrame
            df = pd.DataFrame({'Datum': raw[datum_col]})
            category_map = {}
            seen_categories = []

            for (cat, name) in raw.columns:
                if name in ('Wochentag', 'Datum'):
                    continue
                
                category = 'Other' if pd.isna(cat) else cat
                category_map[name] = category
                
                if category not in seen_categories:
                    seen_categories.append(category)
                
                # Take the column
                df[name] = raw[(cat, name)]

            # Clean up
            df['Datum'] = pd.to_datetime(df['Datum'])
            if 'Wochentag' in df.columns:
                df = df.drop(columns=['Wochentag'])

            # Filter categories that actually have data
            category_order = [
                c for c in seen_categories 
                if any((ex_name in df.columns) for ex_name, ex_cat in category_map.items() if ex_cat == c)
            ]
            
            return df, category_map, category_order
            
        except Exception as e:
            # In case of any error during complex loading, try fallback
            print(f"Error loading categories: {e}. Using fallback.")
            return self._fallback_load()

    def _fallback_load(self) -> Tuple[pd.DataFrame, Dict[str, str], List[str]]:
        """
        Fallback loading method for simpler Excel formats or when category reading fails.
        """
        try:
            df_simple = pd.read_excel(self.file_path, header=3)
            df_simple['Datum'] = pd.to_datetime(df_simple['Datum'])
            
            if 'Wochentag' in df_simple.columns:
                df_simple = df_simple.drop(columns=['Wochentag'])
                
            exercises = [c for c in df_simple.columns if c != 'Datum']
            category_map = {ex: 'Other' for ex in exercises}
            category_order = ['Other']
            
            return df_simple, category_map, category_order
        except Exception as e:
            print(f"Critical error loading data: {e}")
            return pd.DataFrame(columns=['Datum']), {}, []

    def get_all_stats(self, df: pd.DataFrame, category_map: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Calculates statistics for all exercises in the DataFrame.
        """
        stats = []
        exercises = [col for col in df.columns if col != 'Datum']

        for exercise in exercises:
            exercise_stats = self.get_exercise_stats(df, exercise, category_map)
            if exercise_stats:
                stats.append(exercise_stats)
                
        return stats

    def get_exercise_stats(self, df: pd.DataFrame, exercise: str, category_map: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """
        Calculates statistics for a single exercise.
        """
        series = df[['Datum', exercise]].dropna()
        if series.empty:
            return None

        series = series.sort_values('Datum')
        today = datetime.now()
        
        latest_dt = series['Datum'].iloc[-1]
        latest_val = round(float(series[exercise].iloc[-1]), 1)
        first_val = float(series[exercise].iloc[0])
        
        # Increases
        total_increase_abs = round(latest_val - first_val, 1)
        total_increase_pct = round((total_increase_abs / first_val) * 100, 1) if first_val > 0 else 0.0
        
        # Quarter increase (last 90 days)
        quarter_ago = latest_dt - timedelta(days=90)
        old_series_q = series[series['Datum'] <= quarter_ago]
        quarter_val = float(old_series_q[exercise].iloc[-1]) if not old_series_q.empty else first_val
        quarter_increase_abs = round(latest_val - quarter_val, 1)
        quarter_increase_pct = round((quarter_increase_abs / quarter_val) * 100, 1) if quarter_val > 0 else 0.0

        # Month increase (last 30 days)
        month_ago = latest_dt - timedelta(days=30)
        old_series_m = series[series['Datum'] <= month_ago]
        month_val = float(old_series_m[exercise].iloc[-1]) if not old_series_m.empty else first_val
        month_increase_abs = round(latest_val - month_val, 1)
        month_increase_pct = round((month_increase_abs / month_val) * 100, 1) if month_val > 0 else 0.0

        diff = 0.0
        last_increase_date = None
        days_since_increase = None

        if len(series) > 1:
            prev_val = float(series[exercise].iloc[-2])
            diff = round(latest_val - prev_val, 1)
            
            # Find last increase date by traversing backwards
            for i in range(len(series) - 1, 0, -1):
                if float(series[exercise].iloc[i]) > float(series[exercise].iloc[i-1]):
                    last_increase_date = series['Datum'].iloc[i]
                    days_since_increase = (today - last_increase_date).days
                    break
        
        # If never increased, use the days since the very first recording or just None
        # But for sorting as requested, we need a value.
        if days_since_increase is None and not series.empty:
             days_since_increase = (today - series['Datum'].iloc[0]).days

        days_since_last = (today - latest_dt).days
        
        # Recommendation for next strength measurement (e.g. every 28 days)
        # We define a score: higher means more urgent
        # Status: 'urgent' (>28 days), 'due' (>21 days), 'ok' (<=21 days)
        measurement_status = 'ok'
        if days_since_last > 28:
            measurement_status = 'urgent'
        elif days_since_last > 21:
            measurement_status = 'due'

        return {
            'name': exercise,
            'current_max': latest_val,
            'first_max': round(first_val, 1),
            'quarter_max': round(quarter_val, 1),
            'month_max': round(month_val, 1),
            'total_increase_abs': total_increase_abs,
            'total_increase_pct': total_increase_pct,
            'quarter_increase_abs': quarter_increase_abs,
            'quarter_increase_pct': quarter_increase_pct,
            'month_increase_abs': month_increase_abs,
            'month_increase_pct': month_increase_pct,
            'diff': diff,
            'last_date': latest_dt.strftime('%d.%m.%Y'),
            'days_since_last': days_since_last,
            'measurement_status': measurement_status,
            'last_increase_date': last_increase_date,
            'days_since_increase': days_since_increase,
            'icon': self._get_exercise_icon(exercise),
            'category': category_map.get(exercise) if category_map else None
        }

    @staticmethod
    def _get_exercise_icon(exercise_name: str) -> str:
        """
        Returns a FontAwesome icon class based on the exercise name.
        """
        icon_mapping = {
            "fa-legs-dot": ["bein", "adduktor", "abduktor", "glutaeus"],
            "fa-child": ["bauch", "rückenstrec", "rumpf"]
        }
        
        lower_name = exercise_name.lower()
        for icon, keywords in icon_mapping.items():
            if any(k in lower_name for k in keywords):
                return icon
        return "fa-dumbbell"
