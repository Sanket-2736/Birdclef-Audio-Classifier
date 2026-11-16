
"""
JSON serialization utilities for numpy types and complex data structures.
"""

import numpy as np
import math
import json


print("[DEBUG] Initializing JSON serialization utilities...")


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

    print(f"[DEBUG] to_jsonable() called | Type: {type(obj).__name__}")

    if isinstance(obj, np.ndarray):

        print(f"[DEBUG] NumPy array detected | Shape: {obj.shape} | Dtype: {obj.dtype}")
        print("[DEBUG] Converting NumPy array to Python list...")

        result = to_jsonable(obj.tolist())

        print("[SUCCESS] NumPy array converted successfully.")

        return result

    elif isinstance(obj, np.generic):

        print(f"[DEBUG] NumPy scalar detected | Type: {type(obj).__name__}")
        print(f"[DEBUG] NumPy scalar value: {obj}")

        # Handles numpy scalars: int64, float32, bool_, etc.
        # Convert to Python native type
        item = obj.item()

        print(f"[DEBUG] Converted NumPy scalar to Python type: {type(item).__name__}")

        # Recursively handle in case item() returns another numpy type
        return to_jsonable(item)

    elif isinstance(obj, float):

        print(f"[DEBUG] Python float detected | Value: {obj}")

        # Handle NaN and Inf
        if math.isnan(obj) or math.isinf(obj):

            print(f"[WARNING] Non-finite float detected: {obj}")
            print("[DEBUG] Replacing non-finite float with 0.0")

            return 0.0

        print("[DEBUG] Float is valid. Returning original value.")

        return obj

    elif isinstance(obj, dict):

        print(f"[DEBUG] Dictionary detected | Number of keys: {len(obj)}")
        print(f"[DEBUG] Dictionary keys: {list(obj.keys())}")

        # Recursively handle dict values
        result = {}

        for k, v in obj.items():

            print(f"[DEBUG] Processing dictionary key: {k}")
            print(f"[DEBUG] Value type: {type(v).__name__}")

            result[k] = to_jsonable(v)

        print("[SUCCESS] Dictionary conversion completed.")

        return result

    elif isinstance(obj, (list, tuple)):

        print(f"[DEBUG] List/Tuple detected | Length: {len(obj)}")
        print(f"[DEBUG] Collection type: {type(obj).__name__}")

        # Recursively handle list/tuple elements
        result = []

        for index, item in enumerate(obj):

            print(f"[DEBUG] Processing collection element at index: {index}")
            print(f"[DEBUG] Element type: {type(item).__name__}")

            result.append(to_jsonable(item))

        print("[SUCCESS] List/Tuple conversion completed.")

        return result

    else:

        # Return as-is (str, int, bool, None, etc.)
        print(
            f"[DEBUG] No conversion required | "
            f"Type: {type(obj).__name__}"
        )

        return obj


def safe_float(value, default=0.0):
    """
    Safely convert a value to float, handling None and non-numeric values.
    """

    print("\n[DEBUG] safe_float() called")
    print(f"[DEBUG] Input value: {value}")
    print(f"[DEBUG] Input type: {type(value).__name__}")
    print(f"[DEBUG] Default value: {default}")

    if value is None:

        print("[WARNING] Input is None. Returning default value.")
        return default

    try:

        result = float(value)

        print(f"[SUCCESS] Float conversion successful: {result}")

        return result

    except (TypeError, ValueError) as e:

        print("[ERROR] Float conversion failed.")
        print(f"[ERROR] Exception type: {type(e).__name__}")
        print(f"[ERROR] Exception message: {str(e)}")
        print(f"[DEBUG] Returning default value: {default}")

        return default


def safe_int(value, default=0):
    """
    Safely convert a value to int, handling None and non-numeric values.
    """

    print("\n[DEBUG] safe_int() called")
    print(f"[DEBUG] Input value: {value}")
    print(f"[DEBUG] Input type: {type(value).__name__}")
    print(f"[DEBUG] Default value: {default}")

    if value is None:

        print("[WARNING] Input is None. Returning default value.")
        return default

    try:

        result = int(value)

        print(f"[SUCCESS] Integer conversion successful: {result}")

        return result

    except (TypeError, ValueError) as e:

        print("[ERROR] Integer conversion failed.")
        print(f"[ERROR] Exception type: {type(e).__name__}")
        print(f"[ERROR] Exception message: {str(e)}")
        print(f"[DEBUG] Returning default value: {default}")

        return default


def safe_str(value, default=""):
    """
    Safely convert a value to string, handling None.
    """

    print("\n[DEBUG] safe_str() called")
    print(f"[DEBUG] Input type: {type(value).__name__}")
    print(f"[DEBUG] Default value: {default}")

    if value is None:

        print("[WARNING] Input is None. Returning default string.")
        return default

    result = str(value)[:255]

    print(f"[DEBUG] Converted string: {result}")
    print(f"[DEBUG] Original string length: {len(str(value))}")
    print(f"[DEBUG] Final string length: {len(result)}")

    if len(str(value)) > 255:
        print("[WARNING] String exceeded 255 characters and was truncated.")

    print("[SUCCESS] String conversion completed.")

    return result  # Limit to common VARCHAR(255) limit


print("[SUCCESS] JSON serialization utilities loaded successfully.")
