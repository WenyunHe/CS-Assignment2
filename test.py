import unittest
from unittest.mock import patch, Mock
from app import app, fetch_store_news, CompetitorNews

class TestFetchStoreNews(unittest.TestCase):
    @patch('app.feedparser.parse')
    @patch('app.requests.head')
    def test_fetch_store_news(self, requests_head_mock, feedparser_parse_mock):
        sample_feed_data = {
            'entries': [
                {'title': 'Test News 1', 'link': 'https://example.com/news1'},
                {'title': 'Test News 2', 'link': 'https://example.com/news2'}
            ]
        }
        requests_head_mock.return_value.headers.get.side_effect = ['https://example.com/news1', 'https://example.com/news2']
        feedparser_parse_mock.return_value = Mock(entries=sample_feed_data['entries'])

        with app.app_context():
            news_data = fetch_store_news('test')
        
        self.assertEqual(len(news_data), 2)
        self.assertEqual(news_data[0]['title'], 'Test News 1')
        self.assertEqual(news_data[1]['title'], 'Test News 2')
        self.assertEqual(news_data[0]['url'], 'https://example.com/news1')
        self.assertEqual(news_data[1]['url'], 'https://example.com/news2')

if __name__ == '__main__':
    unittest.main()

