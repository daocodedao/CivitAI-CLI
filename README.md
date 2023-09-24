![Banner](banner.png)
# CivitAI-CLI

## Introduction

CivitAI-CLI is a command-line interface tool designed to interact with the CivitAI API. It allows users to efficiently fetch, display, list, and download models hosted on [CivitAI](https://civitai.com). While the tool offers several features without an API key, having one unlocks additional functionalities.

## Table of Contents

- [Installation](#installation)
- [Environment Variables (Optional)](#environment-variables-optional)
- [Usage](#usage)
  - [Main Menu](#main-menu)
  - [Listing and Filtering Models](#listing-and-filtering-models)
  - [Fetching Models by ID](#fetching-models-by-id)
  - [Downloading Models](#downloading-models)
  - [Changing Display Mode](#changing-display-mode)
  - [Settings Menu](#settings-menu)
  - [Graceful Shutdown](#graceful-shutdown)
  - [Model Types](#model-types)

## Installation

To install and use CivitAI-CLI, clone this repository and ensure you have all the necessary dependencies installed. Installing `imgcat` is also recommended for optimal functionality ([imgcat GitHub](https://github.com/eddieantonio/imgcat.git)).

```bash
git clone https://github.com/roadmaus/CivitAI-CLI.git
pip install -r requirements.txt
```

## Environment Variables (Optional)

Setting the `CIVITAI_API_KEY` environment variable with your API key is optional but recommended to unlock additional features. Without it, the program will still run, but with a gentle reminder of enhanced functionality with the API key.

```bash
export CIVITAI_API_KEY=your_api_key_here
```

## Usage

### Main Menu

Upon launching the CLI, you'll be presented with various options:
- List and filter models
- Fetch model by ID
- Download model by ID
- Access settings menu
- Exit application

### Listing and Filtering Models

List and apply multiple filters to the models based on criteria such as name, tag, creator's username, model type, sort order, time frame for sorting, and more. Results can also be saved to a JSON file for further processing.

### Fetching Models by ID

Enter the model ID to fetch its details. Model details will be displayed in a concise format, showcasing essential information such as the creator, description, stats, and version.

### Downloading Models

Specify the model ID to download the desired model. The download directory can be user-specified or defaulted. Related images can also be downloaded.


### Settings Menu

Navigate through the settings menu to configure user preferences, including default version choice, NSFW filter, image size, and download path. The CLI will save and load your settings for future sessions.


### Model Types

The CLI categorizes models into several types, including but not limited to:
- Checkpoint
- TextualInversion
- Hypernetwork
- AestheticGradient
- LORA
- LoCon
- Controlnet
- Upscaler
- MotionModule
- VAE
- Poses
- Wildcards
- Workflows
- Other

Explore CivitAI-CLI and make the most out of CivitAI's extensive resources. For further inquiries or issues, refer to the official CivitAI documentation or raise an issue on this repository.
