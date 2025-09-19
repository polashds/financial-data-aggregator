
import unittest
from src.sentiment_analyzer import SentimentAnalyzer

class TestSentimentAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = SentimentAnalyzer()
    
    def test_positive_sentiment(self):
        text = "This is a great company with excellent products and amazing growth potential."
        result = self.analyzer.analyze_text(text)
        self.assertEqual(result['sentiment'], 'positive')
    
    def test_negative_sentiment(self):
        text = "This company is facing serious challenges and declining sales."
        result = self.analyzer.analyze_text(text)
        self.assertEqual(result['sentiment'], 'negative')
    
    def test_neutral_sentiment(self):
        text = "The company reported its quarterly results."
        result = self.analyzer.analyze_text(text)
        self.assertEqual(result['sentiment'], 'neutral')

if __name__ == '__main__':
    unittest.main()