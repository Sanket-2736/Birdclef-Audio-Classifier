"""
JSON serialization utilities for numpy types and complex data structures.
"""

import numpy as np
import math
import json


def to_jsonable(obj):
    """
    Recursively convert Python/NumPy objects to JSON-serializable types.
    
    Handles:
    - numpy arrays -> lists
    - numpy scalars (float32, int64, bool_) -> Python native types
    - NaN/Inf floats -> 0.0
    - dicts -> recursively converted
    - lists/tuples -> recursively converted
    - anything else -> returned as-is
    """
    if isinstance(obj, np.ndarray):
        # Convert numpy array to list, then recursively handle elements
        return to_jsonable(obj.tolist())
    
    elif isinstance(obj, np.generic):
        # Handles numpy scalars: int64, float32, bool_, etc.
        # Convert to Python native type
        item = obj.item()
        # Recursively handle in case item() returns another numpy type
        return to_jsonable(item)
    
    elif isinstance(obj, float):
        # Handle NaN and Inf
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return obj
    
    elif isinstance(obj, dict):
        # Recursively handle dict values
        return {k: to_jsonable(v) for k, v in obj.items()}
    
    elif isinstance(obj, (list, tuple)):
        # Recursively handle list/tuple elements
        return [to_jsonable(item) for item in obj]
    
    else:
        # Return as-is (str, int, bool, None, etc.)
        return obj


def safe_float(value, default=0.0):
    """
    Safely convert a value to float, handling None and non-numeric values.
    """
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    """
    Safely convert a value to int, handling None and non-numeric values.
    """
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_str(value, default=""):
    """
    Safely convert a value to string, handling None.
    """
    if value is None:
        return default
    return str(value)[:255]  # Limit to common VARCHAR(255) limit
