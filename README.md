# PyDriveSync

PyDriveSync is a command-line application designed to synchronize files and folders with Google Drive. It offers several features for managing files and folders in a Google Drive account. The application uses the Google Drive API for authentication and interaction with Google Drive.

**Note: This project is currently under development and may not be considered stable. It may contain bugs and security vulnerabilities. Users are advised to use this application with caution.**

## Python Version Support

PyDriveSync is intended to work with Python 3.10, but it is recommended to use Python 3.12 as the application has been developed and tested mainly with this version.

## Dependencies

The following Python packages are required for PyDriveSync to function correctly. You can install them using the provided `requirements.txt` file:

```bash
pip install -r requirements.txt
```

- `google-api-python-client`: The official Python client library for Google APIs, used for interacting with the Google Drive API.

- `google-auth-httplib2`: Provides an httplib2 transport for google-auth.

- `google-auth-oauthlib`: A library for OAuth2 authentication, required for authenticating the application with the user's Google account.

Please ensure these dependencies are installed before running PyDriveSync.
