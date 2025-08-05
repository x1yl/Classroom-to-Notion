import os


def create_directory(path):
    try:
        os.makedirs(path, exist_ok=True)
        print(f"Directory '{path}' created successfully")
    except OSError as error:
        print(f"Error creating directory '{path}': {error}")


try:
    create_directory("outputs")
    create_directory("cache")
    print("Setup complete! Directories created successfully.")
except Exception as e:
    print(f"An error occurred: {str(e)}")
    import traceback

    traceback.print_exc()
