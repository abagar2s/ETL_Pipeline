import subprocess
import os

def run_bat_file(bat_file_path):
    """
    Function to run a specific .bat file.
    
    Args:
    - bat_file_path (str): The full path to the .bat file to execute.
    
    Returns:
    - output (str): The output from the .bat file execution.
    """
    try:
        # Check if the .bat file exists
        if not os.path.exists(bat_file_path):
            raise FileNotFoundError(f"The file {bat_file_path} does not exist.")

        # Run the .bat file and capture the output
        result = subprocess.run(bat_file_path, shell=True, capture_output=True, text=True)

        # Print the output
        print("Output from .bat file:")
        print(result.stdout)

        # Print any errors
        if result.stderr:
            print("Errors during execution:")
            print(result.stderr)

        # Return the output for further use
        return result.stdout

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Specify the path to your .bat file
bat_file_path = r"C:\Users\ayman\Desktop\Projects\ETL_Pipeline\run_fetch_weather.bat"

# Run the .bat file
output = run_bat_file(bat_file_path)
