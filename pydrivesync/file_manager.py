import json

EXAMPLE_INSTRUCTIONS_STRUCTURE = {
    "UPLOAD": [
        {
            "source": "/path/to/file.txt",
            "destination": "GoogleDriveFolderID"
        },
        {
            "source": "/path/to/folder",
            "destination": "GoogleDriveFolderID"
        }
    ],
    "DOWNLOAD": [
        {
            "source": "GoogleDriveFolderID",
            "destination": "/path/to/destination"
        },
        {
            "source": "GoogleDriveFileID",
            "destination": "/path/to/destination"
        }
    ]
}


def read_instructions(file_path='instructions.json'):
    """Reads and loads instructions from a JSON file.

    Args:
        file_path (str, optional): The path to the JSON file containing instructions.
            Defaults to 'instructions.json'.

    Returns:
        dict: A dictionary containing the loaded instructions.
    
    Raises:
        FileNotFoundError: If the specified file path does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
    """
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
        
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None
    
    except json.JSONDecodeError:
        print(f"File '{file_path}' does not contain valid JSON.")
        return None


def create_empty_instructions_file(file_path='instructions.json'):
    """Creates an empty JSON file for instructions if it does not exist.

    Args:
        file_path (str, optional): The path to the JSON file to be created.
            Defaults to 'instructions.json'.

    Returns:
        bool: True if the file is created or already exists, False otherwise.

    Raises:
        FileNotFoundError: If the specified file path is invalid.
        PermissionError: If the user doesn't have permission to write to the specified location.
    """
    try:
        with open(file_path, 'w') as file:
            json.dump(EXAMPLE_INSTRUCTIONS_STRUCTURE, file, indent=4)
        return True
    
    except FileNotFoundError as file_error:
        print(f"File access error: {file_error}")
        return False
    
    except PermissionError as permission_error:
        print(f"Permission denied: {permission_error}")
        return False