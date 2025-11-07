"""NYML Parser - A simple configuration format parser."""

__version__ = "0.1.0"

from .parser import parse_nyml, ParseError

__all__ = ["parse_nyml", "ParseError"]