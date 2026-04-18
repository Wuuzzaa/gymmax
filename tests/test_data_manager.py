import unittest
import pandas as pd
from datetime import datetime
from data_manager import GymDataManager

class TestGymDataManager(unittest.TestCase):
    def setUp(self):
        # We don't need a real file for these unit tests as we pass DataFrames directly
        self.data_manager = GymDataManager('dummy.xlsx')
        
    def test_get_exercise_icon(self):
        self.assertEqual(self.data_manager._get_exercise_icon("Beinpresse"), "fa-legs-dot")
        self.assertEqual(self.data_manager._get_exercise_icon("Bauchmaschine"), "fa-child")
        self.assertEqual(self.data_manager._get_exercise_icon("Bankdrücken"), "fa-dumbbell")

    def test_get_all_stats_empty(self):
        df = pd.DataFrame(columns=['Datum'])
        stats = self.data_manager.get_all_stats(df)
        self.assertEqual(stats, [])

    def test_get_all_stats_with_data(self):
        # Create a dummy DataFrame
        dates = [datetime(2023, 1, 1), datetime(2023, 1, 10)]
        data = {
            'Datum': dates,
            'Exercise1': [50.0, 55.0],
            'Exercise2': [20.0, 20.0]
        }
        df = pd.DataFrame(data)
        category_map = {'Exercise1': 'Upper Body', 'Exercise2': 'Lower Body'}
        
        stats = self.data_manager.get_all_stats(df, category_map)
        
        self.assertEqual(len(stats), 2)
        
        # Check Exercise1 (increased)
        ex1_stat = next(s for s in stats if s['name'] == 'Exercise1')
        self.assertEqual(ex1_stat['current_max'], 55.0)
        self.assertEqual(ex1_stat['diff'], 5.0)
        self.assertEqual(ex1_stat['total_increase_pct'], 10.0)  # (55-50)/50 * 100
        self.assertEqual(ex1_stat['quarter_increase_pct'], 10.0) # Within 90 days
        self.assertEqual(ex1_stat['category'], 'Upper Body')
        self.assertIsNotNone(ex1_stat['last_increase_date'])
        self.assertIn('measurement_status', ex1_stat)
        
        # Check Exercise2 (no increase)
        ex2_stat = next(s for s in stats if s['name'] == 'Exercise2')
        self.assertEqual(ex2_stat['current_max'], 20.0)
        self.assertEqual(ex2_stat['diff'], 0.0)
        self.assertEqual(ex2_stat['total_increase_pct'], 0.0)
        self.assertIsNone(ex2_stat['last_increase_date'])
        self.assertIn('measurement_status', ex2_stat)

    def test_measurement_status(self):
        # Create a dummy DataFrame with old date
        old_date = datetime.now() - pd.Timedelta(days=30)
        data = {'Datum': [old_date], 'Exercise': [50.0]}
        df = pd.DataFrame(data)
        
        stats = self.data_manager.get_exercise_stats(df, 'Exercise')
        self.assertEqual(stats['measurement_status'], 'urgent')
        
        recent_date = datetime.now() - pd.Timedelta(days=5)
        data_recent = {'Datum': [recent_date], 'Exercise': [50.0]}
        df_recent = pd.DataFrame(data_recent)
        stats_recent = self.data_manager.get_exercise_stats(df_recent, 'Exercise')
        self.assertEqual(stats_recent['measurement_status'], 'ok')

if __name__ == '__main__':
    unittest.main()
