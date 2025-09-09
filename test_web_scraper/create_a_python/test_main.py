#!/usr/bin/env python3
"""
Tests for the news headline scraper.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
from main import NewsHeadlineScraper

class TestNewsHeadlineScraper(unittest.TestCase):
    """Test cases for NewsHeadlineScraper."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scraper = NewsHeadlineScraper()
    
    def test_scraper_initialization(self):
        """Test scraper initializes correctly."""
        self.assertIsNotNone(self.scraper.session)
        self.assertTrue(len(self.scraper.news_sources) > 0)
    
    @patch('requests.Session.get')
    def test_scrape_headlines_success(self, mock_get):
        """Test successful headline scraping."""
        # Mock response
        mock_response = MagicMock()
        mock_response.content = '<html><h2 class="headline">Test Headline</h2></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        source = {
            'name': 'Test Source',
            'url': 'https://test.com',
            'headline_selector': 'h2.headline'
        }
        
        headlines = self.scraper.scrape_headlines(source)
        self.assertEqual(len(headlines), 1)
        self.assertEqual(headlines[0], 'Test Headline')
    
    def test_save_to_json(self):
        """Test JSON saving functionality."""
        test_data = {
            'timestamp': '2023-01-01T00:00:00',
            'sources': []
        }
        
        filename = 'test_output.json'
        self.scraper.save_to_json(test_data, filename)
        
        # Verify file was created and contains correct data
        with open(filename, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data['timestamp'], test_data['timestamp'])
        
        # Clean up
        import os
        os.remove(filename)

if __name__ == '__main__':
    unittest.main()
