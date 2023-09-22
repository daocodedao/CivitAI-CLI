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
import signal
import sys

BASE_URL = "https://civitai.com/api/v1/models"
MAX_LINE_WIDTH = 80
SETTINGS_FILE = "civitai_settings.json"

class CivitaiCLI:
    SIZE_MAPPINGS = {
        'small': '30x25',
        'medium': '60x50',
        'large': '120x100'
    }
    BASE_URL = "https://civitai.com/api/v1/models"
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
        self.saved_models = None 

    def toggle_display_mode(self):
        self.display_mode = "images" if self.display_mode == "text" else "text"
        print(f"Switched display mode to {self.display_mode}.")
        self.save_settings()  

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
            "nsfw": kwargs.get("nsfw"),
            # Corrected the key to "baseModel"
            "baseModel": kwargs.get("base_model")
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
        url = f"{self.BASE_URL}/{model_id}"
        params = {}
        if primaryFileOnly:
            params['primaryFileOnly'] = 'true'
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print("Error fetching model:", response.status_code)
            print(response.text)  # Print the full error message from the server
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

    BASE_MODELS = ["None", "SD 1.4", "SD 1.5", "SD 2.0", "SD 2.0 768", "SD 2.1", "SD 2.1 768", "SDXL 0.9", "SDXL 1.0", "Other"]

    def prompt_for_limit(self):
        questions = [
            inquirer.Text('limit',
                          message="Enter number of results per page (1-100, default 25)",
                          validate=lambda _, x: x.isdigit() and 1 <= int(x) <= 100,
                          default="25")
        ]
        return inquirer.prompt(questions)['limit']

    def prompt_for_basic_filters(self):
        questions = [
            inquirer.Text('query', message="Filter by name (leave blank for none): "),
            inquirer.Text('tag', message="Filter by tag (leave blank for none): "),
            inquirer.Text('username', message="Filter by creator username (leave blank for none): ")
        ]
        return inquirer.prompt(questions)

    def prompt_for_type_filter(self):
        questions = [
            inquirer.Checkbox('types',
                              message="Select type(s) to filter by",
                              choices=self.MODEL_TYPES)
        ]
        return inquirer.prompt(questions)['types']

    def prompt_for_sorting(self):
        sort_order_choices = ["Highest Rated", "Most Downloaded", "Newest"]
        period_choices = ["AllTime", "Year", "Month", "Week", "Day"]

        questions = [
            inquirer.List('sort',
                          message="Choose a sort order",
                          choices=sort_order_choices,
                          default=sort_order_choices[0]),
            inquirer.List('period',
                          message="Choose a time frame for sorting",
                          choices=period_choices,
                          default=period_choices[0])
        ]
        return inquirer.prompt(questions)

    def prompt_for_nsfw_filter(self):
        nsfw_choices = ["all", "nsfw", "sfw"]
        questions = [
            inquirer.List('nsfw',
                          message="Filter by NSFW?",
                          choices=nsfw_choices,
                          default="sfw")
        ]
        return inquirer.prompt(questions)['nsfw']

    def prompt_for_base_model(self):
        questions = [
            inquirer.List('base_model',
                          message="Select a base model to filter by (or None to skip)",
                          choices=self.BASE_MODELS)
        ]
        base_model = inquirer.prompt(questions)['base_model']
        return None if base_model == "None" else base_model

    def print_orange_line(self):
        # ANSI escape code for bright orange (may appear as yellow in some terminals)
        ORANGE = '\033[93m'
        # ANSI escape code to reset to default
        RESET = '\033[0m'
        
        print(ORANGE + '-' * 250 + RESET)

    def list_all_models(self, api_token=None, resume=False):
        fetching_page = False
        while True:
            # Initialize params dictionary
            params = {}

            # If it's the first page or not resuming, prompt for filters and parameters
            if self.current_page == 1 and not resume and not fetching_page:
                params['limit'] = self.prompt_for_limit()
                params.update(self.prompt_for_basic_filters())

                # Ask if user wants to filter by type
                if inquirer.confirm("Filter by type?", default=False):
                    params['types'] = self.prompt_for_type_filter()

                params.update(self.prompt_for_sorting())
                params['nsfw'] = self.prompt_for_nsfw_filter()
                
                # Include prompt for base model filtering here
                self.current_base_model = self.prompt_for_base_model()
                if self.current_base_model:
                    params['baseModel'] = self.current_base_model

                # Clean up params
                params = {k: v for k, v in params.items() if v is not None and v != ""}

                # Store current params
                self.current_params = params
            else:
                # If resuming, use the stored parameters
                params = self.current_params

            # Set the page parameter
            params['page'] = self.current_page

            # Fetch models using the parameters
            models = self.fetch_all_models(**params)
            self.saved_models = models

            # Post-process filtering based on baseModel if specified
            if self.current_base_model:
                models = [model for model in models if model.get('modelVersions') and model['modelVersions'][0].get('baseModel') == self.current_base_model]

            # Inform the user about the current page
            self.print_orange_line()
            print(f"Displaying page {self.current_page} of models:")
            for model in models:

                self.display_model_details(model)
            self.print_orange_line()
            # Show current page right above the prompt
            print(f"\nCurrently on page {self.current_page}.\n")

            # Ask user for the next action
            actions = ["Next page", "Previous page", "Jump to page", "Download selected models", "Filter again", "Exit"]
            next_action = inquirer.list_input("Choose an action:", choices=actions)

            # Handle next action based on user input
            if next_action == "Filter again":
                self.current_page = 1
                continue
            elif next_action == "Next page":
                self.current_page += 1
                continue
            elif next_action == "Previous page":
                if self.current_page > 1:
                    self.current_page -= 1
                else:
                    print("You're already on the first page.")
                    resume = True
                continue

            elif next_action == "Jump to page":
                desired_page = int(input("Enter the page number to jump to: "))
                self.current_page = desired_page
                fetching_page = True  # Set flag
                continue

            elif next_action == "Download selected models":
                # Use inquirer to select models for download
                model_choices = [{'name': f"{model['name']} (ID: {model['id']})", 'value': model['id']} for model in models]
                selected_models_dicts = inquirer.checkbox("Select models to download:", choices=model_choices)
                for model_dict in selected_models_dicts:
                    model_id = model_dict['value']
                    self.download_model(model_id)  # Use the provided download_model method

                print("Download completed. Returning to browsing...")
                resume = True  # Set resume to True to continue browsing from the last state
            else:  # Exit
                break

    def get_model_save_path(self, model_type):
        relative_save_path = self.MODEL_SAVE_PATHS.get(model_type, "models/Other")
        absolute_save_path = os.path.join(self.download_path, relative_save_path)
        os.makedirs(absolute_save_path, exist_ok=True)
        return absolute_save_path

    def download_file(self, url, save_path):
        cmd = ["wget", url, "--content-disposition", "-P", save_path]
        try:
            subprocess.check_call(cmd)

            # Fetch only headers initially
            response = requests.get(url, stream=True)
            cd_header = response.headers.get('content-disposition')
            
            if cd_header:
                extracted_name = re.findall("filename=(.+)", cd_header)[0]
                return extracted_name.strip("\"")  # Remove any quotes around the filename
            else:
                print("Content-Dispostion Header missing or empty.")
                return None
        except subprocess.CalledProcessError:
            print(f"Error downloading {url}")
            return None

    def download_images(self, image_urls, save_path, base_name):
        if not image_urls:
            return
        
        url = image_urls[0]  # Only get the first image
        try:
            response = requests.get(url)
            response.raise_for_status()
            extension = os.path.splitext(url)[1]
            image_save_path = os.path.join(save_path, f"{base_name}.jpeg")

            with open(image_save_path, 'wb') as f:
                f.write(response.content)
                    
            print(f"Downloaded image to {image_save_path}")
        except requests.RequestException as e:
            print(f"Error downloading image {url}: {e}")

    def save_model_info(self, model_details, save_path, base_name):
        try:
            info_file_path = os.path.join(save_path, f"{base_name}.json")
            
            with open(info_file_path, "w") as f:
                json.dump(model_details, f, indent=4)
                
            print(f"Saved model information to {info_file_path}")
        except Exception as e:
            print(f"An error occurred while saving model information: {e}")

    def prompt_for_versions(self, model_versions, existing_files):
        version_choices = [
            {
                'name': version['name'],
                'value': version['id'],
                'disabled': f"{version['name']}.safetensors" in existing_files
            } for version in model_versions
        ]
        questions = [
            inquirer.Checkbox(
                'selected_versions',
                message="Select versions to download",
                choices=version_choices,
                carousel=True
            ),
        ]
        answers = inquirer.prompt(questions)
        return [version['value'] for version in answers['selected_versions']]

    def download_model(self, model_id):
        model_details = self.fetch_model_by_id(model_id)
        model_name = model_details.get('name', 'unknown')
        model_versions = model_details.get('modelVersions', [])
        model_download_path = self.get_model_save_path(model_details.get('type', 'default'))
        existing_files = set(os.listdir(model_download_path))

        selected_version_ids = self.prompt_for_versions(model_versions, existing_files) if len(model_versions) > 1 else [model_versions[0]['id']]

        for version_id in selected_version_ids:
            version_detail = next((v for v in model_versions if v['id'] == version_id), None)
            if version_detail is None:
                print(f"Version ID {version_id} not found.")
                continue

            model_download_url = version_detail['downloadUrl']
            original_file_name = self.download_file(model_download_url, model_download_path)
            if original_file_name:
                base_name, _ = os.path.splitext(original_file_name)

                # Download images and save model information
                image_urls = [image['url'] for image in version_detail.get('images', [])]
                self.download_images(image_urls, model_download_path, base_name)  # Passing base_name
                self.save_model_info(model_details, model_download_path, base_name)  # Passing base_name

                print(f"Downloaded to {original_file_name} in {model_download_path}")

            else:
                print("Download failed.")

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
        try:
            with open(SETTINGS_FILE, 'w') as file:
                json.dump(settings, file)
        except Exception as e:
            print(f"Error writing to {SETTINGS_FILE}: {e}")

    def graceful_shutdown(self, signal_received, frame):
        # Here, you can add any cleanup logic if necessary
        print("\nCTRL+C detected. Exiting gracefully...")
        sys.exit(0)

    def run(self):
        self.main_menu()

if __name__ == '__main__':
    cli = CivitaiCLI()
    
    # Set up signal handling for graceful shutdown
    signal.signal(signal.SIGINT, cli.graceful_shutdown)

    cli.run()