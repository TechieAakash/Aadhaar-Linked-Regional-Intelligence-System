"""
ALRIS - Utility Functions
==========================
Common utilities shared across ALRIS modules.
"""

import json
import numpy as np


class NumpyJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles numpy types.
    """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)


def save_json(data, filepath):
    """
    Save data to JSON file, handling numpy types.
    
    Args:
        data: Dict or list to save
        filepath: Path to JSON file
    """
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, cls=NumpyJSONEncoder)


def convert_to_native_types(obj):
    """
    Recursively convert numpy types to native Python types.
    
    Args:
        obj: Object to convert (dict, list, or scalar)
        
    Returns:
        Object with all numpy types converted to native Python types
    """
    import pandas as pd
    from datetime import datetime
    
    if isinstance(obj, dict):
        return {k: convert_to_native_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native_types(item) for item in obj]
    elif isinstance(obj, (pd.Timestamp, datetime)):
        return str(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif pd.isna(obj):
        return None
    else:
        return obj
