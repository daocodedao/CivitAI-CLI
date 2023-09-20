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

import inquirer

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

    def fetch_model_by_id(self, model_id, primaryFileOnly=False):
        url = f"{BASE_URL}/{model_id}"
        params = {}
        if primaryFileOnly:
            params['primaryFileOnly'] = 'true'
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print("Error fetching model:", response.status_code)
            return {}

    def get_model_download_url(self, model_id, version_index=None):
        model_details = self.fetch_model_by_id(model_id)
        model_versions = model_details.get("modelVersions", [])
        
        if not model_versions:
            print("No model versions found for the model.")
            return None

        # If a specific version index is given, fetch that version's download URL.
        if version_index is not None:
            chosen_version = model_versions[version_index]
            download_url = chosen_version.get("downloadUrl")
        else:
            # Default behavior: fetch the first version's download URL.
            download_url = model_versions[0].get("downloadUrl")
            
        if not download_url:
            print("No download URL found for the model version.")
            return None

        return download_url

    def choose_model_version(self, model):
        model_versions = model.get('modelVersions', [])

        if not model_versions:
            print("No model versions found for the model.")
            return []

        print(f"\nModel: {model.get('name', 'Unknown_Model')}")
        print("Available Versions:")

        for idx, version in enumerate(model_versions):
            print(f"{idx + 1}. {version.get('name', 'Unknown_Version')} (Created at: {version.get('createdAt', 'Unknown Date')})")

        print(f"{len(model_versions) + 1}. Download All Versions")

        choice = input("\nEnter the number of the version you want to download (or choose 'Download All Versions'): ")

        try:
            choice = int(choice)
            if choice == len(model_versions) + 1:
                return model_versions
            elif 1 <= choice <= len(model_versions):
                return [model_versions[choice - 1]]
            else:
                print("Invalid choice.")
                return []
        except ValueError:
            print("Invalid input. Please enter a number.")
            return []

    def download_models_with_aria(self, model_ids_str, chosen_versions, output_path):
        model_ids = [int(id.strip()) for id in model_ids_str.split(',')]
        
        for idx, model_id in enumerate(model_ids):
            model_details = self.fetch_model_by_id(model_id)
            model_name = model_details.get('name', 'Unknown_Model')

            # Ensure the model name is file-safe
            safe_model_name = "".join([c for c in model_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()

            # Loop through only the chosen versions
            for version in chosen_versions[idx]:
                version_name = version.get('name', 'Unknown_Version')
                download_url = version.get('downloadUrl')

                # Ensure the version name is file-safe
                safe_version_name = "".join([c for c in version_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()

                # Combine model name and version name for a unique file name
                combined_name = f"{safe_model_name}_{safe_version_name}"

                # Download Model
                if download_url:
                    print(f"Downloading model: {model_name} - Version: {version_name}...")
                    cmd = f'aria2c "{download_url}" --dir="{output_path}" --out="{combined_name}.safetensors" --check-certificate=false --content-disposition-default-utf8=true'
                    subprocess.run(cmd, shell=True)

                # Download Image
                images = version.get('images', [])
                if images:
                    image_url = images[0].get('url')
                    if image_url:
                        print(f"Downloading image for model: {model_name} - Version: {version_name}...")
                        cmd = f'aria2c "{image_url}" --dir="{output_path}" --check-certificate=false --content-disposition-default-utf8=true'
                        subprocess.run(cmd, shell=True)

                        # Rename the image
                        original_image_name = os.path.basename(image_url.split("?")[0])  # Split to handle possible query parameters
                        os.rename(os.path.join(output_path, original_image_name), os.path.join(output_path, f"{combined_name}.jpeg"))

                # Save Metadata directly with desired name
                with open(os.path.join(output_path, f"{combined_name}.json"), "w") as metadata_file:
                    json.dump(version, metadata_file, indent=4)

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
            params['limit'] = int(input("Enter number of results per page (1-100, default 25): ") or 25)
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
            nsfw_input = input("Filter by NSFW? (all/nsfw/sfw, default is sfw): ").lower() or 'sfw'
            if nsfw_input == 'nsfw':
                params['nsfw'] = True
            elif nsfw_input == 'sfw' or not nsfw_input:
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

            # Fetch model details to get the versions
            model_details = self.fetch_model_by_id(model_id)
            versions = model_details.get('modelVersions', [])

            # Prompt user to select which versions to download
            print("Select version(s) by entering the corresponding numbers (separate multiple choices with a comma):")
            for idx, version in enumerate(versions, 1):
                print(f"{idx}. {version.get('name', 'Unknown_Version')}")
            
            selected_indices = input().split(",")
            chosen_versions = [versions[int(idx)-1] for idx in selected_indices]

            default_path = os.path.expanduser("~/downloads")
            output_path = input(f"Enter path to download the model (or press enter, default location is {default_path}): ")
            if not output_path:
                output_path = default_path

            # Call the download_models_with_aria method
            self.download_models_with_aria(str(model_id), [chosen_versions], output_path)

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
            questions = [
                inquirer.List('choice',
                              message="--- Civitai CLI Tool ---",
                              choices=['List and filter models', 'Fetch model by ID', 'Download model by ID', 'Settings', 'Exit'],
                              carousel=True  # for better navigation
                              ),
            ]
            answers = inquirer.prompt(questions)
            choice = answers['choice']

            if choice == 'List and filter models':
                self.list_all_models(self.api_token)

            elif choice == 'Fetch model by ID':
                model_id = int(input("Enter model ID: "))
                model = self.fetch_model_by_id(model_id)
                self.display_model_details(model)

            elif choice == 'Download model by ID':
                model_ids_input = input("Enter model IDs to download (comma separated): ")
                model_ids = [int(id.strip()) for id in model_ids_input.split(",")]
                all_chosen_versions = []

                for model_id in model_ids:
                    if len(model_ids) > 1:
                        model = self.fetch_model_by_id(model_id, primaryFileOnly=True)
                        chosen_versions = [model]
                    else:
                        model = self.fetch_model_by_id(model_id)
                        chosen_versions = self.choose_model_version(model)

                    all_chosen_versions.append(chosen_versions)

                default_path = os.path.expanduser("~/downloads")
                output_path = input(f"Enter path to download the models (or press enter, default location is {default_path}): ")
                if not output_path:
                    output_path = default_path

                self.download_models_with_aria(','.join(map(str, model_ids)), all_chosen_versions, output_path)

            elif choice == 'Settings':
                self.settings_menu()

            elif choice == 'Exit':
                print("Goodbye!")
                exit()

    def settings_menu(self):
        while True:
            questions = [
                inquirer.List('choice',
                              message="--- Settings ---",
                              choices=[
                                  f"Change display mode ({self.display_mode})",
                                  f"Adjust image size (Currently: {self.image_size})",
                                  "Back to main menu"
                              ],
                              carousel=True
                              ),
            ]
            answers = inquirer.prompt(questions)
            choice = answers['choice']

            if 'Change display mode' in choice:
                self.toggle_display_mode()

            elif 'Adjust image size' in choice:
                self.set_image_size_inquirer()

            elif choice == 'Back to main menu':
                return

    def set_image_size_inquirer(self):
        size_choices = ['small', 'medium', 'large']
        questions = [
            inquirer.List('size',
                          message="Choose the image size",
                          choices=size_choices,
                          carousel=True
                          ),
        ]
        answers = inquirer.prompt(questions)
        chosen_size = answers['size']  # 'small', 'medium', or 'large'
        
        self.image_size = self.SIZE_MAPPINGS[chosen_size]
        self.save_settings()  # Assuming you have a save_settings method, if not, you can comment this line out.
        print(f"Image size set to: {self.image_size}")



    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as file:
                    settings = json.load(file)
                    self.display_mode = settings.get('display_mode', 'text')
                    self.image_size = settings.get('image_size', self.SIZE_MAPPINGS['medium'])
            except json.JSONDecodeError:
                print(f"Error decoding {SETTINGS_FILE}. Please ensure it's in valid JSON format.")
            except Exception as e:
                print(f"Error reading from {SETTINGS_FILE}: {e}")



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