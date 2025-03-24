import os
import zipfile


def zipper(base_path, selected_subdirs, output_zip):
    """Creates a zip file containing selected subdirectories."""
    if not selected_subdirs:
        return None

    try:
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for subdir in selected_subdirs:
                full_path = os.path.join(base_path, subdir)
                if not os.path.exists(full_path):
                    continue
                for root, _, files in os.walk(full_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(
                            file_path, base_path))
        return output_zip
    except Exception as e:
        return f"Error zipping subdirectories: {e}"
