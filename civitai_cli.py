import argparse
import os
import requests
import json
import tempfile
import subprocess
from bs4 import BeautifulSoup
from html import unescape
from tqdm import tqdm
from termcolor import colored

BASE_URL = "https://civitai.com/api/v1/models"
MAX_LINE_WIDTH = 80
SETTINGS_FILE = "civitai_settings.json"

class CivitaiCLI:
    SIZE_MAPPINGS = {
        'small': '30x25',
        'medium': '60x50',
        'large': '120x100'
    }

    def __init__(self):
        self.api_token = os.environ.get("CIVITAI_API_KEY")
        if not self.api_token:
            print("Please set the CIVITAI_API_KEY environment variable with your API key.")
            exit()
        self.current_params = {}
        self.current_base_model = None
        self.current_page = 1
        self.display_mode = "text"
        self.image_size = self.SIZE_MAPPINGS['medium']
        self.load_settings()
        
    def toggle_display_mode(self):
        self.display_mode = "images" if self.display_mode == "text" else "text"
        print(f"Switched display mode to {self.display_mode}.")

    def construct_url(self, params):
        return f"{BASE_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

    def fetch_all_models(self, **kwargs):
        params = {
            "limit": kwargs.get("limit", 100),
            "page": kwargs.get("page"),
            "query": kwargs.get("query"),
            "tag": kwargs.get("tag"),
            "username": kwargs.get("username"),
            "sort": kwargs.get("sort"),
            "period": kwargs.get("period"),
            "rating": kwargs.get("rating"),
            "favorites": kwargs.get("favorites"),
            "hidden": kwargs.get("hidden"),
            "primaryFileOnly": kwargs.get("primaryFileOnly"),
            "allowNoCredit": kwargs.get("allowNoCredit"),
            "allowDerivatives": kwargs.get("allowDerivatives"),
            "allowDifferentLicenses": kwargs.get("allowDifferentLicenses"),
            "nsfw": kwargs.get("nsfw")
        }
        if "types" in kwargs:
            params["types"] = kwargs["types"]

        # Remove None values and empty strings
        params = {k: v for k, v in params.items() if v is not None and v != ""}

        # Construct and print the URL for debugging
        constructed_url = self.construct_url(params)
        print("Constructed URL:", constructed_url)

        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            return response.json().get('items', [])
        else:
            print("Error fetching models:", response.status_code)
            return []

    def fetch_model_by_id(self, model_id):
        response = requests.get(f"{BASE_URL}/{model_id}")
        if response.status_code == 200:
            return response.json()
        else:
            print("Error fetching model:", response.status_code)
            return {}

    def get_model_download_url(self, model_id):
        model_details = self.fetch_model_by_id(model_id)
        model_versions = model_details.get("modelVersions", [])
        if not model_versions:
            print("No model versions found for the model.")
            return None

        download_url = model_versions[0].get("downloadUrl")
        if not download_url:
            print("No download URL found for the model version.")
            return None

        return download_url

    def download_models_with_aria(self, model_ids, output_path):
        for model_id in model_ids:
            model_details = self.fetch_model_by_id(model_id)
            model_name = model_details.get('name', 'Unknown_Model')

            # Loop through all model versions
            for version in model_details.get('modelVersions', []):
                version_name = version.get('name', 'Unknown_Version')
                download_url = version.get('downloadUrl')

                if download_url:
                    print(f"Downloading model: {model_name} - Version: {version_name}...")
                    cmd = f'aria2c "{download_url}" --dir="{output_path}" --check-certificate=false --content-disposition-default-utf8=true'
                    subprocess.run(cmd, shell=True)

        print("All downloads completed!")
    # 3. Display and Formatting

    def split_text_into_lines(self, text, max_width):
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) <= max_width:
                current_line.append(word)
                current_length += len(word) + 1  # +1 for space
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word) + 1

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def display_model_details(self, model):
        print("\n" + "-"*40)
        print(f"ID: {model['id']} | Name: {model['name']} | Type: {model['type']}")
        print(f"Creator: {model['creator']['username']} | Avatar URL: {model['creator']['image']}")

        # Retrieve model image URL
        model_image_url = model['modelVersions'][0]['images'][0]['url'] if 'modelVersions' in model and model['modelVersions'] and 'images' in model['modelVersions'][0] and model['modelVersions'][0]['images'] else None

        # Parse the image_size attribute
        desired_image_width, desired_image_height = map(int, self.image_size.split('x'))

        # Display model image using imgcat with user-defined size
        if self.display_mode == "images" and model_image_url:
            os.system(f'imgcat --width={desired_image_width} --height={desired_image_height} {model_image_url}')

        # Ensure that a default value is used if description is missing or None
        description_html = model.get('description', '') or ''
        description_text = BeautifulSoup(description_html, "html.parser").get_text()

        # Splitting by lines based on MAX_LINE_WIDTH
        description_lines = self.split_text_into_lines(description_text, MAX_LINE_WIDTH)
        short_description = "\n".join(description_lines[:4])
        if len(description_lines) > 4:
            short_description += '...'

        print(f"Description: {short_description}")
        print(f"Tags: {', '.join(model['tags'])}")
        print(f"Downloads: {model['stats']['downloadCount']} | Favorites: {model['stats']['favoriteCount']} | Rating: {model['stats']['rating']} from {model['stats']['ratingCount']} ratings")
        if model.get('modelVersions'):
            latest_version = model['modelVersions'][0]  # Assuming the first one is the latest
            print(f"\nVersion ID: {latest_version['id']} | Name: {latest_version['name']} | Base Model: {latest_version['baseModel']} | Type: {latest_version['baseModelType']}")
            if latest_version.get('files'):
                primary_file = None
                for f in latest_version['files']:
                    if f.get('primary'):
                        primary_file = f
                        break
                if not primary_file:
                    primary_file = latest_version['files'][0]
                print(f"Primary File: {primary_file['name']} | Size: {primary_file['sizeKB']} KB | Download URL: {primary_file['downloadUrl']}")
        print("-"*40 + "\n")

    def save_to_temp_json(self, data):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w+t') as temp:
            json.dump(data, temp, indent=4)
            temp.seek(0)
            return temp.name


    MODEL_TYPES = [
        "Checkpoint",
        "TextualInversion",
        "Hypernetwork",
        "AestheticGradient",
        "LORA",
        "LoCon",
        "Controlnet",
        "Upscaler",
        "MotionModule",
        "VAE",
        "Poses",
        "Wildcards",
        "Workflows",
        "Other"
    ]


    def list_all_models(self, api_token=None):
        # Interactive filtering preferences
        params = {}
        if self.current_page == 1:
            params['limit'] = int(input("Enter number of results per page (1-100, default 100): ") or 100)
            params['query'] = input("Filter by name (leave blank for none): ")
            params['tag'] = input("Filter by tag (leave blank for none): ")
            params['username'] = input("Filter by creator username (leave blank for none): ")

            filter_by_type = input("Filter by type? (y/n) default is n: ").lower()
            if filter_by_type == 'y' or filter_by_type == 'yes':
                print("Select type(s) by entering the corresponding numbers (separate multiple choices with a comma):")
                for idx, model_type in enumerate(self.MODEL_TYPES, 1):
                    print(f"{idx}. {model_type}")
                selected_indices = input().split(",")
                params['types'] = [self.MODEL_TYPES[int(idx)-1] for idx in selected_indices]

            params['sort'] = input("Sort order (Highest Rated, Most Downloaded, Newest, leave blank for default): ")
            params['period'] = input("Time frame for sorting (AllTime, Year, Month, Week, Day, leave blank for default): ")
            rating_input = input("Filter by rating (leave blank for any): ")
            params['rating'] = float(rating_input) if rating_input else None
            nsfw_input = input("Filter by NSFW? (all/nsfw/sfw, default is all): ").lower()
            if nsfw_input == 'nsfw':
                params['nsfw'] = True
            elif nsfw_input == 'sfw':
                params['nsfw'] = False
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            # Save the current params
            self.current_params = params

        else:
            # Use saved params for fetching models from subsequent pages
            params = self.current_params

        headers = {}
        if api_token:
            headers['Authorization'] = f"Bearer {api_token}"

        # Add the current page to the params
        params['page'] = self.current_page

        # Fetch and display models
        models = self.fetch_all_models(**params)
        
        # Save to a temporary JSON file
        temp_file_path = "/tmp/civitai_results.json"
        with open(temp_file_path, 'w') as file:
            json.dump(models, file, indent=4)

        print(f"Results saved to: {temp_file_path}")

        if self.current_base_model:
            # If a base model has been selected before, filter the models again
            models = [model for model in models if model.get('modelVersions') and model['modelVersions'][0].get('baseModel') == self.current_base_model]

        for model in models:
            self.display_model_details(model)

        # If it's the first page, ask to filter by base model
        if self.current_page == 1:
            filter_by_base_model = input("Do you want to filter by base model? (y/n): ").lower()
            if filter_by_base_model == 'y':
                print("Select a base model:")
                print("1. SD 1.5")
                print("2. SDXL 1.0")
                print("3. SDXL 0.9")
                choice = input("Enter your choice: ")

                base_model_map = {
                    "1": "SD 1.5",
                    "2": "SDXL 1.0",
                    "3": "SDXL 0.9"
                }

                base_model_selected = base_model_map.get(choice)
                if base_model_selected:
                    self.current_base_model = base_model_selected
                    filtered_models = [model for model in models if model.get('modelVersions') and model['modelVersions'][0].get('baseModel') == base_model_selected]
                    if filtered_models:
                        for model in filtered_models:
                            self.display_model_details(model)
                    else:
                        print(f"No models found for base model: {base_model_selected}")
                else:
                    print("Invalid choice.")

        action_prompt = f"Do you want to filter again or look on the next page? (y/n/{self.current_page + 1}/d): "
        action = input(action_prompt).lower()

        if action == 'n':
            self.current_page = 1
            return
        elif action == str(self.current_page + 1):
            self.current_page += 1
            self.list_all_models(api_token)
        elif action == 'd':
            model_id = int(input("Enter model ID you want to download: "))
            default_path = os.path.expanduser("~/downloads")
            output_path = input(f"Enter path to download the model (or press enter, default location is {default_path}): ")
            if not output_path:
                output_path = default_path
            self.download_models_with_aria([model_id], output_path)
            # After downloading, prompt the user for the next action again
            action = input(action_prompt).lower()
            if action == str(self.current_page + 1):
                self.current_page += 1
                self.list_all_models(api_token)
            elif action == 'n':
                self.current_page = 1
        else:
            print("Invalid choice. Please try again.")


    def main_menu(self):
        while True:
            print("\n--- Civitai CLI Tool ---")
            print("1. " + colored("List and filter models", 'cyan'))
            print("2. " + colored("Fetch model by ID", 'cyan'))
            print("3. " + colored("Download model by ID", 'cyan'))
            print("4. " + colored("Settings", 'cyan'))
            print("5. " + colored("Exit", 'yellow'))
            choice = input("Enter your choice: ")

            if choice == '1':
                self.list_all_models(self.api_token)

            elif choice == '2':
                model_id = int(input("Enter model ID: "))
                model = self.fetch_model_by_id(model_id)
                self.display_model_details(model)

            elif choice == '3':
                model_ids_input = input("Enter model IDs to download (comma separated): ")
                model_ids = [int(id.strip()) for id in model_ids_input.split(",")]
                default_path = os.path.expanduser("~/downloads")
                output_path = input(f"Enter path to download the models (or press enter, default location is {default_path}): ")
                if not output_path:
                    output_path = default_path
                self.download_models_with_aria(model_ids, output_path)

            elif choice == '4':
                self.settings_menu()

            elif choice == '5':
                print("Goodbye!")
                exit()

            else:
                print("Invalid choice. Please try again.")

    def settings_menu(self):
        while True:
            print("\n--- Settings ---")
            print("1. Change display mode (" + colored(f"{self.display_mode}", 'cyan') + ")")
            size_options = ", ".join([f"{key} ({colored(val, 'cyan')}) - '{initial}'" for key, val, initial in zip(self.SIZE_MAPPINGS.keys(), self.SIZE_MAPPINGS.values(), ['s', 'm', 'l'])])
            print(f"2. Adjust image size (Currently: {colored(self.image_size, 'green')}) - Options: {size_options}")
            print("3. " + colored("Back to main menu", 'yellow'))
            choice = input("Enter your choice: ")


            if choice == '1':
                self.toggle_display_mode()

            elif choice == "2":
                self.set_image_size() 

            elif choice == '3':
                return

            else:
                print("Invalid choice. Please try again.")


    def set_image_size(self):
        size_choices = {
            's': 'small',
            'm': 'medium',
            'l': 'large'
        }
        choice = input("Enter desired image size (" + colored("s", 'cyan') + " for small, " + colored("m", 'cyan') + " for medium, " + colored("l", 'cyan') + " for large): ").lower()

        if choice in size_choices:
            self.image_size = self.SIZE_MAPPINGS[size_choices[choice]]
            # Assuming you have a save_settings method, if not, you can comment this line out.
            self.save_settings()  
            print(f"Image size set to: {self.image_size}")
        else:
            print("Invalid choice. Please choose a valid image size.")



    def load_settings(self):
        size_mappings = {
            'small': '30x25',
            'medium': '60x50',
            'large': '120x100'
        }
        
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as file:
                settings = json.load(file)
                self.display_mode = settings.get('display_mode', 'text')  # default to 'text'
                self.image_size = settings.get('image_size', self.SIZE_MAPPINGS['medium'])


    def save_settings(self):
        settings = {
            'display_mode': self.display_mode,
            'image_size': self.image_size
        }
        with open(SETTINGS_FILE, 'w') as file:
            json.dump(settings, file)


    def run(self):
        self.main_menu()

if __name__ == '__main__':
    cli = CivitaiCLI()
    cli.run()
