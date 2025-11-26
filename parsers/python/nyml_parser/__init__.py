"""NYML Parser - A simple configuration format parser."""

__version__ = "0.1.0"

from .parser import parse_nyml, ParseError, to_mapping, get_all, get_first, get_last

__all__ = ["parse_nyml", "ParseError", "to_mapping", "get_all", "get_first", "get_last"]