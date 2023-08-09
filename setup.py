import json
from pathlib import Path

config_file = "config.json"
file_path = Path("downloads")  # Define the file_path variable

def setup_menu():
    while True:
        print("\n                         Setup Menu")
        print("                         -=-=--=-=-\n")
        print("                    1. Connection Speed")
        print("                    2. Maximum Retries")
        print("                    3. Return to Main\n\n")
        choice = input("Enter your choice (1-3): ").strip()
        if choice == '1':
            internet_options_menu()
        elif choice == '2':
            max_retries_menu()
        elif choice == '3':
            return
        else:
            print("Invalid choice. Please try again.")

def internet_options_menu():
    config = load_config()
    chunk_sizes = {1: 1024000, 2: 4096000, 3: 8192000, 4: 16384000, 5: 40960000}
    print("\n                    Connection Menu")
    print("                        -=-=--=-=-\n")
    print("            1. Slow  ~1MBit/s (Chunk Size  1024KB)")
    print("            2. Okay  ~5MBit/s (Chunk Size  4096KB)")
    print("            3. Good ~10MBit/s (Chunk Size  8192KB)")
    print("            4. Fast ~25MBit/s (Chunk Size 20480KB)")
    print("            5. Uber ~50MBit/s (Chunk Size 40960KB)\n\n")
    connection_choice = input("Enter your connection speed (1-5): ").strip()
    if connection_choice.isdigit() and int(connection_choice) in chunk_sizes:
        config["chunk"] = chunk_sizes[int(connection_choice)]
        save_config(config)
        print("Connection speed updated successfully.")
    else:
        print("Invalid choice. Please try again.")

def max_retries_menu():
    config = load_config()
    print("\n                     Retries Menu")
    print("                        -=-=--=-=-\n")
    current_retries = config.get("retries", 100)
    print(f"                Current Maximum Retries: {current_retries}\n\n")
    retries = input("Enter the number of maximum retries (or 'b' to back): ").strip()
    if retries.lower() != 'b':
        try:
            retries = int(retries)
            config["retries"] = retries
            save_config(config)
            print("Maximum retries updated successfully.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def load_config():
    try:
        if Path(config_file).exists():
            with open(config_file, "r") as file:
                config = json.load(file)
            # Check for missing files and remove them
            filenames = []
            urls = []
            for i in range(1, 10):
                filename_key = f"filename_{i}"
                filename = config.get(filename_key, "Empty")
                if filename != "Empty" and not (file_path / filename).exists():
                    config[filename_key] = "Empty"
                    config[f"url_{i}"] = ""
                else:
                    filenames.append((filename, config.get(f"url_{i}", "")))
            # Sort the filenames and urls, pushing "Empty" entries to the bottom
            filenames = [item for item in filenames if item[0] != "Empty"] + [item for item in filenames if item[0] == "Empty"]
            for i in range(1, 10):
                config[f"filename_{i}"] = filenames[i - 1][0] if i - 1 < len(filenames) else "Empty"
                config[f"url_{i}"] = filenames[i - 1][1] if i - 1 < len(filenames) else ""
            save_config(config)  # Save the updated config
            return config
        else:
            config = {}
            for i in range(1, 10):
                config[f"filename_{i}"] = "Empty"
                config[f"url_{i}"] = ""
            return config
    except json.JSONDecodeError:
        print("Error reading configuration file. Using default settings.")
        return {}

def save_config(config):
    try:
        with open(config_file, "w") as file:
            json.dump(config, file, indent=4)
    except Exception as e:
        print(f"Error saving configuration: {str(e)}")
