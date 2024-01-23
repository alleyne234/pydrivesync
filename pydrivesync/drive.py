import os
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload

existing_files_cache = {}


def create_folder(service, folder_name, parent_folder_id=None):
    """Create a folder and return the folder ID.

    Args:
        service (googleapiclient.discovery.Resource): Authenticated Drive API service.
        folder_name (str): Name of the folder to create.
        parent_folder_id (str, optional): ID of the parent folder. Defaults to None (root).
            Should be a string.

    Returns:
        str: Folder ID.

    Raises:
        googleapiclient.errors.HttpError: If the API request encounters an HTTP error.
    """
    try:
        folder_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }

        if parent_folder_id:
            folder_metadata['parents'] = [parent_folder_id]

        folder = (
            service.files()
            .create(body=folder_metadata, fields="id")
            .execute()
        )

        return folder.get("id")
    
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


def download(service, content_id, destination):
    """Downloads a file or folder from Google Drive.

    Args:
        service (googleapiclient.discovery.Resource): Authenticated Drive API service.
        content_id (str): ID of the file or folder on Google Drive to download.
        destination (str): Local path where the file or folder will be saved after downloading.

    Returns:
        bool: True if the download is successful, False otherwise.

    Raises:
        Exception: If any error occurs during the download process.
    """
    try:
        file = (
            service.files()
            .get(fileId=content_id)
            .execute()
        )
        if file['mimeType'] == 'application/vnd.google-apps.folder':
            return download_folder(service, content_id, destination)
        else:
            return download_file(service, content_id, destination)

    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def download_file(service, file_id, destination):
    """Download a file from Google Drive.

    Args:
        service (googleapiclient.discovery.Resource): Authenticated Drive API service.
        file_id (str): ID of the file on Google Drive to download.
        destination (str): Local path where the file will be saved after downloading.

    Returns:
        bool: True if the download is successful, False otherwise.

    Raises:
        googleapiclient.errors.HttpError: If the API request encounters an HTTP error.
    """
    try:
        file_metadata = service.files().get(fileId=file_id).execute()
        file_path = os.path.join(destination, file_metadata['name'])
        request = service.files().get_media(fileId=file_id)

        # Check if file type is not supported for direct download
        unsupported_types = ['application/vnd.google-apps']
        if any(file_metadata['mimeType'].startswith(t) for t in unsupported_types):
            print(f"File '{file_metadata['name']}' is not supported and will not be downloaded.")
            return False
        
        with open(file_path, 'wb') as file:
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"Download {int(status.progress() * 100)}%.")

        print(f"File downloaded to: {file_path}")
        return True

    except HttpError as error:
        print(f"An error occurred: {error}")
        return False


def download_folder(service, folder_id, destination):
    """Downloads a folder and its contents from Google Drive.

    Args:
        service (googleapiclient.discovery.Resource): Authenticated Drive API service.
        folder_id (str): ID of the folder on Google Drive to download.
        destination (str): Local path where the folder and its contents will be saved after downloading.

    Returns:
        bool: True if the download is successful, False otherwise.

    Raises:
        googleapiclient.errors.HttpError: If the API request encounters an HTTP error.
    """
    try:
        folder = service.files().get(fileId=folder_id).execute()
        folder_name = folder['name']
        folder_path = os.path.join(destination, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        results = service.files().list(
            q=f"'{folder_id}' in parents",
            fields="files(id, name, mimeType)"
        ).execute()
        items = results.get('files', [])

        for item in items:
            item_id = item['id']
            item_mimetype = item['mimeType']

            if item_mimetype == 'application/vnd.google-apps.folder':
                download_folder(service, item_id, folder_path)
            else:
                download_file(service, item_id, folder_path)

        print(f"Folder downloaded to: {folder_path}")
        return True

    except HttpError as error:
        print(f"An error occurred: {error}")
        return False


def update_existing_files_cache(service, parent_folder_id=None):
    """Updates the cache of existing files and their metadata within the specified Google Drive folder.

    Args:
        service (googleapiclient.discovery.Resource): Authenticated Drive API service.
        parent_folder_id (str, optional): ID of the parent folder in Google Drive to fetch files from.
            Defaults to None, which fetches files from the root folder.

    Note:
        This function retrieves the list of files and their metadata from the specified folder in Google Drive
        and updates the existing cache. The cache holds information about existing files to facilitate quick
        checks for file existence during file operations.

    Returns:
        None
    """
    query = f"'{parent_folder_id}' in parents" if parent_folder_id else "'root' in parents"
    response = service.files().list(q=query, spaces='drive', fields='files(id, name, mimeType, parents)').execute()
    files = response.get('files', [])

    for file in files:
        existing_files_cache[file['name']] = {'id': file['id'], 'mimeType': file['mimeType'], 'parents': file.get('parents', [])}


def upload(service, path, destination_parent_id=None):
    """Uploads a file or folder to Google Drive.

    Args:
        service (googleapiclient.discovery.Resource): Authenticated Drive API service.
        path (str): Local path of the file or folder to be uploaded.
        destination_parent_id (str, optional): The ID of the destination folder on Google Drive. Defaults to None.

    Returns:
        str: ID of the uploaded file/folder on Google Drive, or None if the upload fails.

    Raises:
        FileNotFoundError: If the specified path doesn't exist.
        IsADirectoryError: If the specified path is a directory and uploading folders is not supported.
        Exception: For any other error during the upload process.
    """
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Error: '{path}' does not exist.")
        
        if os.path.isfile(path):
            return upload_file(service, path, destination_parent_id)
        elif os.path.isdir(path):
            return upload_folder(service, path, destination_parent_id)
        else:
            raise IsADirectoryError(f"Error: '{path}' is neither a file nor a folder.")
        
    except FileNotFoundError as file_error:
        print(f"File access error: {file_error}")
        return None

    except IsADirectoryError as dir_error:
        print(f"Directory error: {dir_error}")
        return None

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def check_file_exists(service, file_name, destination_parent_id=None):
    if file_name in existing_files_cache:
        for parent_id in existing_files_cache[file_name]['parents']:
            if parent_id == destination_parent_id:
                print(f"The file '{file_name}' already exists in this location.")
                return existing_files_cache[file_name]['id']
    
    # Vérification directe sur le Drive distant
    query = f"name='{file_name}' and trashed=false"
    if destination_parent_id:
        query += f" and '{destination_parent_id}' in parents"
    response = service.files().list(q=query, spaces='drive', fields='files(id)').execute()
    files = response.get('files', [])
    if files:
        print(f"The file '{file_name}' already exists in this location.")
        existing_files_cache[file_name] = {'id': files[0]['id'], 'parents': [destination_parent_id]}
        return files[0]['id']
    
    return None


def upload_file(service, file_path, destination_parent_id=None):
    """Upload a file and return its file ID.

    Args:
        service (googleapiclient.discovery.Resource): Authenticated Drive API service.
        file_path (str): The local file path of the file to be uploaded.
        destination_parent_id (str): The ID of the destination folder on Google Drive.

    Returns:
        str: File ID if successfully uploaded, None otherwise.

    Raises:
        googleapiclient.errors.HttpError: If the API request encounters an error.
    """
    try:
        file_name = os.path.basename(file_path)
        existing_file_id = check_file_exists(service, file_name, destination_parent_id)
        if existing_file_id:
            return existing_file_id

        file_metadata = {"name": file_name}

        if destination_parent_id:
            file_metadata["parents"] = [destination_parent_id]

        media = MediaFileUpload(file_path)
        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id, parents")
            .execute()
        )
        update_existing_files_cache(service, destination_parent_id)
        return file.get("id")

    except HttpError as error:
        print(f"An HTTP error occurred: {error}")
        return None


def upload_folder(service, folder_path, destination_parent_id=None):
    """Uploads a folder and its contents to Google Drive.

    Args:
        service (googleapiclient.discovery.Resource): Authenticated Drive API service.
        folder_path (str): Local path of the folder to be uploaded.
        destination_parent_id (str, optional): The ID of the destination folder on Google Drive. Defaults to None.

    Returns:
        str: ID of the uploaded folder on Google Drive, or None if the upload fails.

    Raises:
        googleapiclient.errors.HttpError: If the API request encounters an HTTP error.
    """
    try:
        # Retrieve the name of the last folder in the path if it ends with "/"
        folder_name = os.path.basename(os.path.dirname(folder_path)) if folder_path.endswith('/') else os.path.basename(folder_path)
        
        if folder_path.endswith('/'):
            # If it ends with "/", don't create a new folder but directly use the parent
            folder_name = os.path.basename(os.path.dirname(folder_path))
            uploaded_folder_id = destination_parent_id
        else:
            # Check if the item already exists in the parent
            existing_items = search_items(service, destination_parent_id)
            existing_items_info = {
                item['name']: {'id': item['id'], 'is_folder': item['mimeType'] == 'application/vnd.google-apps.folder'}
                for item in existing_items
            }

            if folder_name in existing_items_info and existing_items_info[folder_name]['is_folder']:
                uploaded_folder_id = existing_items_info[folder_name]['id']
            else:
                # If the item doesn't exist, create a new folder
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }

                if destination_parent_id:
                    folder_metadata['parents'] = [destination_parent_id]

                folder = (
                    service.files()
                    .create(body=folder_metadata, fields='id')
                    .execute()
                )
                uploaded_folder_id = folder.get('id')

        # Traverse through the items in the local folder
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                upload_file(service, item_path, uploaded_folder_id)
            elif os.path.isdir(item_path):
                upload_folder(service, item_path, uploaded_folder_id)

        return uploaded_folder_id
    
    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
        return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def get_parent(service, item_id):
    """Retrieves the parent ID of a file/folder in Google Drive.

    Args:
        service (googleapiclient.discovery.Resource): Authenticated Drive API service.
        item_id (str): ID of the file/folder in Google Drive.

    Returns:
        str: ID of the parent folder, or None if the parent is the root folder.

    Raises:
        googleapiclient.errors.HttpError: If the API request encounters an HTTP error.
    """
    try:
        response = (
            service.files()
            .get(fileId=item_id, fields="parents")
            .execute()
        )
        parents = response.get("parents", [])

        return parents[0] if parents else None

    except HttpError as error:
        print(f"An error occurred while retrieving parent: {error}")
        return None


def display_drive_tree(service, destination_parent_id=None, indent=""):
    """
    Recursively displays the folder and file structure of Google Drive starting from a specified folder.

    Args:
        service (googleapiclient.discovery.Resource): Authenticated Drive API service.
        destination_parent_id (str, optional): ID of the Google Drive folder to start displaying.
            Defaults to None (root folder).
        indent (str, optional): Indentation string for folder structure visualization.
            Defaults to an empty string.

    Raises:
        googleapiclient.errors.HttpError: If the API request encounters an HTTP error.
    """
    try:
        if destination_parent_id is None:
            destination_parent_id = 'root'

        response = service.files().list(
            q=f"'{destination_parent_id}' in parents",
            spaces='drive',
            fields='files(id, name, mimeType)'
        ).execute()
        files = response.get('files', [])

        for file in files:
            file_name = file.get('name')
            file_id = file.get('id')
            print(f"{indent}+--{file_name}")
            if file.get('mimeType') == 'application/vnd.google-apps.folder':
                display_drive_tree(service, file_id, indent + '|  ')

    except HttpError as error:
        print(f"An error occurred while displaying drive tree: {error}")


def display_drive_items(service, destination_parent_id=None):
    os.system('cls')
    try:
        if destination_parent_id is None:
            query = None
        else:
            query = f"'{destination_parent_id}' in parents"

        page_token = None
        items = []

        while True:
            response = service.files().list(
                q=query, spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, parents)',
                pageToken=page_token
            ).execute()
            files = response.get('files', [])
            items.extend(files)
            page_token = response.get('nextPageToken', None)
            
            if page_token is None:
                break

        list_folders = []
        list_files = []

        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                list_folders.append(item)
            else:
                list_files.append(item)

        sorted_folders = sorted(list_folders, key=lambda x: x['name'].casefold())
        sorted_files = sorted(list_files, key=lambda x: x['name'].casefold())

        print(" __________________________________________________________________________________________________ ")
        print("|                    List of Folders                     |                   ID                    |")
        print("|________________________________________________________|_________________________________________|")
        for folder in sorted_folders:
            print(f"| {truncate_name(folder['name'], 54).ljust(54)} |    {truncate_name(folder['id'], 33).ljust(33)}    |")

        print("|________________________________________________________|_________________________________________|")
        print("|                     List of Files                      |                   ID                    |")
        print("|________________________________________________________|_________________________________________|")
        for file in sorted_files:
            print(f"| {truncate_name(file['name'], 54).ljust(54)} |    {truncate_name(file['id'], 33).ljust(33)}    |")
        
        print("|________________________________________________________|_________________________________________|")

    except HttpError as error:
        print(f"An error occurred: {error}")


def truncate_name(name, max_length=50):
    if len(name) > max_length:
        return name[:max_length-3] + "..."
    return name


def search_items(service, destination_parent_id=None):
    """Searches for files and folders in Google Drive from a specified folder.

    Args:
        service (googleapiclient.discovery.Resource): Authenticated Drive API service.
        destination_parent_id (str, optional): ID of the Google Drive folder to start searching.
            Defaults to None (root folder).

    Returns:
        list: List of dictionaries containing details of files and folders found in the specified folder.

    Raises:
        googleapiclient.errors.HttpError: If the API request encounters an HTTP error.
        Exception: For any other unexpected errors.
    """
    try:
        if destination_parent_id is None:
            destination_parent_id = 'root'

        query = f"'{destination_parent_id}' in parents"
        response = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType, parents)'
        ).execute()
        files = response.get('files', [])

        return files

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []