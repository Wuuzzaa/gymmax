import unittest
from unittest.mock import patch
import pandas as pd
from datetime import datetime
from app import app

class TestApp(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client()

    @patch('data_manager.GymDataManager.load_data_with_categories')
    def test_index_route_empty(self, mock_load):
        # Mock empty data
        mock_load.return_value = (pd.DataFrame(columns=['Datum']), {}, [])
        
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'N/A', response.data)

    @patch('data_manager.GymDataManager.load_data_with_categories')
    def test_index_route_with_data(self, mock_load):
        # Mock data
        df = pd.DataFrame({
            'Datum': [datetime(2023, 1, 1)],
            'Beinpresse': [100.0]
        })
        category_map = {'Beinpresse': 'Legs'}
        category_order = ['Legs']
        mock_load.return_value = (df, category_map, category_order)
        
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Beinpresse', response.data)

    @patch('data_manager.GymDataManager.load_data_with_categories')
    def test_index_route_recent_success(self, mock_load):
        # Mock data with increase in the last 7 days
        # Use a fixed date to avoid issues with datetime.now()
        today = datetime(2026, 4, 23, 20, 0, 0)
        df = pd.DataFrame({
            'Datum': [today - pd.Timedelta(days=10), today - pd.Timedelta(days=2)],
            'Beinpresse': [100.0, 110.0]
        })
        category_map = {'Beinpresse': 'Legs'}
        category_order = ['Legs']
        mock_load.return_value = (df, category_map, category_order)
        
        # Patch datetime in data_manager and app to use our fixed 'today'
        # Also patch pd.Timestamp.now() if needed, but app.py uses datetime.now()
        with patch('data_manager.datetime') as mock_dm_datetime:
            mock_dm_datetime.now.return_value = today
            mock_dm_datetime.strftime = datetime.strftime
            with patch('app.datetime') as mock_app_datetime:
                mock_app_datetime.now.return_value = today
                mock_app_datetime.strftime = datetime.strftime
                response = self.client.get('/')
        
        self.assertEqual(response.status_code, 200)
        # Handle potential encoding issues in tests by checking for substrings
        print(f"DEBUG RESPONSE: {response.data[:500]}")
        self.assertTrue(b'Beinpresse' in response.data)
        self.assertTrue(b'110' in response.data)
        self.assertTrue(b'10' in response.data) # diff
        self.assertIn(b'N\xc3\xa4chste Kraftmessungen', response.data) # "Nächste Kraftmessungen" in UTF-8

    @patch('data_manager.GymDataManager.load_data_with_categories')
    def test_index_route_no_recent_success_but_warnings(self, mock_load):
        # Case where no success in 7 days, but urgent measurements exist
        today = datetime(2026, 4, 23, 20, 0, 0)
        df = pd.DataFrame({
            'Datum': [today - pd.Timedelta(days=40)],
            'Beinpresse': [100.0]
        })
        category_map = {'Beinpresse': 'Legs'}
        category_order = ['Legs']
        mock_load.return_value = (df, category_map, category_order)

        with patch('data_manager.datetime') as mock_dm_datetime:
            mock_dm_datetime.now.return_value = today
            mock_dm_datetime.strftime = datetime.strftime
            with patch('app.datetime') as mock_app_datetime:
                mock_app_datetime.now.return_value = today
                mock_app_datetime.strftime = datetime.strftime
                response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'N\xc3\xa4chste Kraftmessungen', response.data)
        self.assertIn(b'Beinpresse', response.data)
        self.assertIn(b'vor 40 Tagen', response.data)
        # Should NOT show recent successes card
        self.assertNotIn(b'Erfolge letzte 7 Tage', response.data)

    @patch('data_manager.GymDataManager.load_data_with_categories')
    def test_details_route_with_trend(self, mock_load):
        # Mock data with at least 3 points for trend
        df = pd.DataFrame({
            'Datum': [datetime(2023, 1, 1), datetime(2023, 1, 10), datetime(2023, 1, 20)],
            'Beinpresse': [100.0, 105.0, 110.0]
        })
        category_map = {'Beinpresse': 'Legs'}
        category_order = ['Legs']
        mock_load.return_value = (df, category_map, category_order)
        
        response = self.client.get('/exercise/Beinpresse')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Beinpresse', response.data)
        # Check if trend and data are mentioned in the response
        self.assertIn(b'Trend-Prognose', response.data)
        self.assertIn(b'Kraftmessung', response.data)

    @patch('data_manager.GymDataManager.load_data_with_categories')
    def test_details_route_not_found(self, mock_load):
        # Mock data
        df = pd.DataFrame({'Datum': [datetime(2023, 1, 1)]})
        mock_load.return_value = (df, {}, [])
        
        response = self.client.get('/exercise/Unknown')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
