import glob
import os
import re
from auth import get_authenticated_drive_service
from drive import *
from file_manager import *

folder_download = 'Downloads'
folder_upload = 'Uploads'
folder_instruction = 'Instructions'
folder_token = 'Tokens'


# Function to authenticate the Drive service
def authenticate():
    service = None
    while service is None:
        service = get_authenticated_drive_service()
        if service is None:
            if os.path.exists("Tokens/token.json"):
                retry = input("Authentication failed. Type 'del' to delete 'token.json' and retry or 'quit' to exit.\n")
                if retry.lower() == 'del':
                    os.remove("Tokens/token.json")
            else:
                retry = input("Authentication failed. Press Enter to retry or 'quit' to exit.\n")
            if retry.lower() == 'quit':
                input("Press any key to continue...")
                exit()

    return service


# Function to create necessary folders if they don't exist
def create_folders_if_not_exist(*folders):
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)


def is_valid_folder_name(name):
    invalid_characters = re.compile(r'[<>:"/\\|?*\x00-\x1F]')
    if invalid_characters.search(name) is not None:
        return False
    
    reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                      'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
    if name.upper() in reserved_names:
        return False

    return True


# Option 1 - 'Create folder'
def create_folder_option(service):
    while True:
        folder_name = input("Enter the name of the folder (press Enter to return to the menu)\n")
        if folder_name == "":
            return
        elif is_valid_folder_name(folder_name):
            parent_folder_id = input("Enter the ID of the destination folder (leave empty to create a folder at the root):\n")
            create_folder(service, folder_name, parent_folder_id)
            input("Press any key to continue...")
            break
        else:
            print("Invalid folder name. Please provide a different name.")
    

# Option 2 - 'Display tree structure'
def display_tree_option(service):
    folder_id = input("Enter the folder ID to display its tree structure (press Enter to view the global tree, type 'quit' to return to the menu):\n")
    if folder_id.lower() == 'quit':
        return

    try:
        if folder_id == "":
            display_drive_tree(service)
        else:
            display_drive_tree(service, folder_id)
    except Exception as e:
        print(f"An error occurred: {e}")
    input("Press any key to continue...")


# Option 3 - 'Display folders and files with ID'
def display_drive_items_option(service):
    while True:
        folder_id = input("What is the ID of the folder you are listing? (press Enter to list all items, type 'quit' to return to the menu)\n")
        if folder_id.lower() == 'quit':
            break
        elif folder_id:
            display_drive_items(service, folder_id)
            input("Press any key to continue...")
            break
        else:
            display_drive_items(service)
            input("Press any key to continue...")
            break


# Option 4 - 'Download file or folder and its contents'
def download_option(service):
    while True:
        item_id = input("What's the ID of the file or folder? (type 'quit' to return to the menu)\n")
        if item_id.lower() == 'quit':
            break
        elif item_id:
            try:
                destination = input("What's the path of the destination? (press Enter to use default path)\n")
                if destination:
                    download(service, item_id, destination)
                else:
                    download(service, item_id, download_folder)
                input("Press any key to continue...")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            print("Please provide an ID.")


# Option 5 - 'Upload file or folder and its contents'
def upload_option(service):
    while True:
        items_path = input("What's the path of the file or folder? (type 'quit' to return to the menu)\n")
        if items_path.lower() == 'quit':
            break
        elif items_path:
            if os.path.exists(items_path):
                destination = input("What's the destination? (press Enter to use root path)\n")
                if destination:
                    upload(service, items_path, destination)
                else:
                    upload(service, items_path)
                input("Press any key to continue...")
                break
            else:
                print("An error occurred, the file or folder does not exist or is inaccessible.")
        else:
            print("Please provide a file or folder path.")


# Option 6 - 'Process instructions'
def process_instructions(service):    
    if not os.path.exists(folder_instruction) or not os.path.isdir(folder_instruction):
        input(f"Directory '{folder_instruction}' does not exist or is invalid, press any key to continue.")
        return
    
    instruction_files = glob.glob(os.path.join(folder_instruction, '*.json'))
    if not instruction_files:
        input(f"No instruction files found in '{folder_instruction}', press any key to continue.")
        return
    
    while True:
        print("Available instruction files:")
        for idx, file_path in enumerate(instruction_files):
            print(f"{idx + 1}. {os.path.basename(file_path)}")
        
        choice = input("Enter the number of the instruction file to execute (Press Enter to return to the menu):\n")
        if choice == "":
            return
        
        try:
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(instruction_files):
                chosen_file = instruction_files[choice_index]
                instructions = read_instructions(chosen_file)
                upload_instructions = instructions.get('UPLOAD', [])
                download_instructions = instructions.get('DOWNLOAD', [])
                
                for upload_task in upload_instructions:
                    upload(service, upload_task['source'], upload_task['destination'])
                
                for download_task in download_instructions:
                    download(service, download_task['source'], download_task['destination'])
                
                print("End Uploads and Downloads tasks.")
                input("Press any key to continue...")
                break
            else:
                print("Invalid choice. Please enter a number within the range.")
        except ValueError:
            print("Invalid choice. Please enter a valid number.")


def main():
    service = authenticate()
    create_folders_if_not_exist(folder_download, folder_upload, folder_token, folder_instruction)

    while True:
        os.system('cls')
        print("""
  ____        ____       _           ____                   
 |  _ \ _   _|  _ \ _ __(_)_   _____/ ___| _   _ _ __   ___ 
 | |_) | | | | | | | '__| \ \ / / _ \___ \| | | | '_ \ / __|
 |  __/| |_| | |_| | |  | |\ V /  __/___) | |_| | | | | (__ 
 |_|    \__, |____/|_|  |_| \_/ \___|____/ \__, |_| |_|\___|
        |___/                              |___/            
       _______________________________________________
      |                                               |
      |  1. Create folder                             |
      |  2. Display tree structure                    |
      |  3. Display drive items with ID               |
      |  4. Download file or folder and its contents  |
      |  5. Upload file or folder and its contents    |
      |  6. Process instructions                      |
      |  0. Exit/Quit                                 |
      |_______________________________________________|
              """)
        choice = input("Enter a choice: ")
        
        match choice:
            case '1':
                create_folder_option(service)
            case '2':
                display_tree_option(service)
            case '3':
                display_drive_items_option(service)
            case '4':
                download_option(service)
            case '5':
                upload_option(service)
            case '6':
                process_instructions(service)
            case '0':
                input("Press any key to continue...")
                os.system('cls')
                exit()
            case _:
                input("Not a valid choice, press any key to continue.")

    
if __name__ == '__main__':
    main()