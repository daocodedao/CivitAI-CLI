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
import re

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
        # Initialize download path to current working directory by default
        self.download_path = os.getcwd()
        # Load settings which might override the defaults
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
            print(response.text)  # <-- Add this to print the full error message from the server
            return {}


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

        model_image_url = model['modelVersions'][0]['images'][0]['url'] if 'modelVersions' in model and model['modelVersions'] and 'images' in model['modelVersions'][0] and model['modelVersions'][0]['images'] else None

        desired_image_width, desired_image_height = map(int, self.image_size.split('x'))

        if self.display_mode == "images" and model_image_url:
            os.system(f'imgcat --width={desired_image_width} --height={desired_image_height} {model_image_url}')

        description_html = model.get('description', '') or ''
        description_text = BeautifulSoup(description_html, "html.parser").get_text()

        description_lines = self.split_text_into_lines(description_text, MAX_LINE_WIDTH)
        short_description = "\n".join(description_lines[:4])
        if len(description_lines) > 4:
            short_description += '...'

        print(f"Description: {short_description}")
        print(f"Tags: {', '.join(model['tags'])}")
        print(f"Downloads: {model['stats']['downloadCount']} | Favorites: {model['stats']['favoriteCount']} | Rating: {model['stats']['rating']} from {model['stats']['ratingCount']} ratings")
        if model.get('modelVersions'):
            latest_version = model['modelVersions'][0]
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

    MODEL_SAVE_PATHS = {
        "Checkpoint": "models/Stable-diffusion",
        "TextualInversion": "models/hypernetworks",
        "Hypernetwork": "models/hypernetworks",
        "AestheticGradient": "extensions/stable-diffusion-webui-aesthetic-gradients/aesthetic_embeddings",
        "LORA": "models/Lora",
        "LoCon": "models/Lora",
        "Controlnet": "models/Controlnet",
        "Upscaler": "models/ESRGAN",
        "MotionModule": "models/MotionModule",
        "VAE": "models/VAE",
        "Poses": "models/Poses",
        "Wildcards": "models/Wildcards",
        "Workflows": "models/Workflows",
        "Other": "models/Other"
    }

    def list_all_models(self, api_token=None):
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

            params = {k: v for k, v in params.items() if v is not None}
            
            self.current_params = params

        else:
            params = self.current_params

        headers = {}
        if api_token:
            headers['Authorization'] = f"Bearer {api_token}"

        params['page'] = self.current_page
        models = self.fetch_all_models(**params)
        
        temp_file_path = "/tmp/civitai_results.json"
        with open(temp_file_path, 'w') as file:
            json.dump(models, file, indent=4)

        print(f"Results saved to: {temp_file_path}")

        if self.current_base_model:
            models = [model for model in models if model.get('modelVersions') and model['modelVersions'][0].get('baseModel') == self.current_base_model]

        for model in models:
            self.display_model_details(model)

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
            model_choices = [{'name': f"{model['name']} (ID: {model['id']})", 'value': model['id']} for model in models]
            
            questions = [
                inquirer.Checkbox('selected_models',
                                  message="Select models to download",
                                  choices=model_choices,
                                  carousel=True
                                  ),
            ]
            answers = inquirer.prompt(questions)
            selected_model_ids = answers['selected_models']
            
            for model_entry in selected_model_ids:
                model_id = model_entry['value']
                self.download_model(model_id)

    def get_model_save_path(self, model_type):
        # Get the save path based on the model type
        relative_save_path = self.MODEL_SAVE_PATHS.get(model_type, "models/Other")
        
        # Join the base download path with the relative save path
        absolute_save_path = os.path.join(self.download_path, relative_save_path)
        
        # Create the directory if it doesn't exist
        os.makedirs(absolute_save_path, exist_ok=True)
        
        return absolute_save_path

    def download_model(self, model_id):
        print(f"Model ID to be downloaded: {model_id}")
        # Fetch model details from the API
        model_details = self.fetch_model_by_id(model_id)
        
        # Define model_name here so it's available throughout the function
        model_name = model_details['name']


        # Extract model versions and prompt user to select a version
        model_versions = model_details.get('modelVersions', [])
        version_choices = [{'name': f"[ ] {version['name']}", 'value': version['id']} for version in model_versions]
        
        questions = [
            inquirer.Checkbox('selected_versions',
                              message="Select versions to download",
                              choices=version_choices,
                              carousel=True
                              ),
        ]
        answers = inquirer.prompt(questions)
        selected_version_dicts = answers['selected_versions']

        # Extract version IDs from the selected dictionaries
        selected_version_ids = [version_dict['value'] for version_dict in selected_version_dicts]

        # Handle each of the selected version IDs
        for version_id in selected_version_ids:
            selected_version = next((version for version in model_versions if version['id'] == version_id), None)
            if not selected_version:
                print(f"Error: Version ID {version_id} not found in the model details.")
                continue

            # Check if downloadUrl exists in the selected version
            if 'downloadUrl' not in selected_version:
                print(f"Error: The selected version '{selected_version['name']}' does not have a download URL.")
                continue

            # Set the download URLs
            model_download_url = selected_version['downloadUrl']
            image_url = selected_version['images'][0]['url'] if selected_version['images'] else None

            # 1. Download model file
            model_download_path = self.get_model_save_path(model_details['type'])
            response = requests.get(model_download_url, stream=True)
            response.raise_for_status()
            cd_header = response.headers.get('content-disposition')
            fname = re.findall("filename=(.+)", cd_header)[0] if cd_header else f"{model_name}.safetensors"
            model_file_path = os.path.join(model_download_path, fname)
            with open(model_file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            
            # Rename the model file using the version name to maintain uniqueness
            desired_model_name = f"{selected_version['name']}.safetensors"
            os.rename(model_file_path, os.path.join(model_download_path, desired_model_name))
            
                    
            # 2. Download image
            if image_url:
                response = requests.get(image_url, stream=True)
                response.raise_for_status()
                cd_header = response.headers.get('content-disposition')
                fname = re.findall("filename=(.+)", cd_header)[0] if cd_header else f"{selected_version['name']}.jpeg"
                image_file_path = os.path.join(model_download_path, fname)
                with open(image_file_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)

            # 3. Fetch and save metadata
            response = requests.get(f"https://civitai.com/api/v1/model-versions/{version_id}")
            metadata = response.json()
            metadata_save_path = os.path.join(model_download_path, f"{selected_version['name']}.json")
            with open(metadata_save_path, 'w') as file:
                json.dump(metadata, file, indent=4)
                
            print(f"Downloaded {selected_version['name']} to {model_download_path}")



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
                pass

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
                                  f"Set default download path (Currently: {self.download_path})",
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
            elif 'Set default download path' in choice:
                self.set_default_download_path()
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
        chosen_size = answers['size']
        
        self.image_size = self.SIZE_MAPPINGS[chosen_size]
        self.save_settings()
        print(f"Image size set to: {self.image_size}")

    def set_default_download_path(self):
        questions = [
            inquirer.Text('path',
                          message="Enter the default download path"),
        ]
        answers = inquirer.prompt(questions)
        self.download_path = answers['path']
        self.save_settings()
        print(f"Default download path set to: {self.download_path}")

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as file:
                    settings = json.load(file)
                    self.display_mode = settings.get('display_mode', 'text')
                    self.image_size = settings.get('image_size', self.SIZE_MAPPINGS['medium'])
                    self.download_path = settings.get('download_path', os.getcwd())  # default to current directory
            except json.JSONDecodeError:
                print(f"Error decoding {SETTINGS_FILE}. Please ensure it's in valid JSON format.")
            except Exception as e:
                print(f"Error reading from {SETTINGS_FILE}: {e}")

    def save_settings(self):
        settings = {
            'display_mode': self.display_mode,
            'image_size': self.image_size,
            'download_path': self.download_path
        }
        with open(SETTINGS_FILE, 'w') as file:
            json.dump(settings, file)

    def run(self):
        self.main_menu()

if __name__ == '__main__':
    cli = CivitaiCLI()
    cli.run()
