"""
Base scraper class for political data collection
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

class BaseScraper:
    """Base class for all scrapers"""

    NAME = "base"
    DESCRIPTION = "Generic scraper"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; DPoliticaBot/1.0; +https://github.com/your-org/dpolitica)'
        })

    def scrape(self, url):
        """Main scrape method - override in subclasses"""
        raise NotImplementedError

    def parse_candidate_name(self, text):
        """Extract candidate name from text"""
        patterns = [
            r'\b(candidato|candidata)\s+([A-ZÁÉÍÓÚ][a-z]+)\s+([A-ZÁÉÍÓÚ][a-z]+)',
            r'\b([A-ZÁÉÍÓÚ][a-z]+)\s+([A-ZÁÉÍÓÚ][a-z]+)\s+(?:es|será)\s+candidato',
            r'([A-Z][a-z]+)\s+([A-Z][a-z]+)\s+para\s+(?:elecciones|presidencia)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return None

    def clean_text(self, text):
        """Clean extracted text"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text

    def get_html(self, url):
        """Fetch HTML from URL"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def to_datetime(self):
        """Get current timestamp"""
        return datetime.utcnow()
