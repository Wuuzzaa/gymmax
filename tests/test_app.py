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
        self.assertIn(b'90d:', response.data)
        self.assertIn(b'Gesamt:', response.data)

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
