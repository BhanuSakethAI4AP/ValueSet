"""
Value Set Management Library
A reusable library for managing value sets with MongoDB

Usage:
    from value_set_lib import ValueSetLibrary

    # Initialize with database
    lib = ValueSetLibrary(database=db)

    # Use functions
    result = await lib.create_value_set(...)
"""

from value_set_lib import (
    ValueSetLibrary,
    create_value_set_document,
    validate_item_structure,
    validate_value_set_structure,
    export_to_json,
    export_to_csv
)

__version__ = "1.0.0"
__author__ = "Your Name"
__all__ = [
    "ValueSetLibrary",
    "create_value_set_document",
    "validate_item_structure",
    "validate_value_set_structure",
    "export_to_json",
    "export_to_csv"
]