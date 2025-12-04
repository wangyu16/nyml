"""NYML Parser - A simple configuration format parser."""

__version__ = "0.1.0"

from .parser import parse_nyml, ParseError, to_mapping, get_all, get_first, get_last
from .parser_v2 import parse_nyml_v2, serialize_nyml_v2, ParseError as ParseErrorV2

__all__ = [
    # V1 exports
    "parse_nyml", "ParseError", "to_mapping", "get_all", "get_first", "get_last",
    # V2 exports
    "parse_nyml_v2", "serialize_nyml_v2", "ParseErrorV2",
]