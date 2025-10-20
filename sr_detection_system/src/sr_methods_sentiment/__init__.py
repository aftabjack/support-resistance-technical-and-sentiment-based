"""
Sentiment-based S/R Detection Methods
Using options data (OI, volume, max pain)
"""

from .oi_walls import detect_oi_walls

__all__ = ['detect_oi_walls']
