import os

def list_subdirectories(base_path):
    """Returns a list of subdirectories inside the given path."""
    if not os.path.exists(base_path):
        return []

    try:
        return [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
    except Exception as e:
        return f"Error listing subdirectories: {e}"
