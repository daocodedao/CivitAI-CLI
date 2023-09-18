
# CivitAI-CLI

## Introduction

CivitAI-CLI is a command-line interface tool designed to interact with the CivitAI API, making it easier to fetch, display, and download models hosted on [https://civitai.com](https://civitai.com).

## Table of Contents

- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
  - [Main Menu](#main-menu)
  - [Listing and Filtering Models](#listing-and-filtering-models)
  - [Fetching Models by ID](#fetching-models-by-id)
  - [Downloading Models](#downloading-models)
  - [Changing Display Mode](#changing-display-mode)
  - [Model Types](#model-types)

## Installation

To install and use CivitAI-CLI, clone this repository and ensure you have all the necessary dependencies installed.

```bash
git clone <repo-link>
pip install -r requirements.txt
```

## Environment Variables

Make sure to set the `CIVITAI_API_KEY` environment variable with your API key. If this isn't set, the program will notify you and exit.

```bash
export CIVITAI_API_KEY=your_api_key_here
```

## Usage

### Main Menu

Upon launching the CLI, you'll be presented with various options:
- List and filter models
- Fetch model by ID
- Download model by ID
- Change display mode

### Listing and Filtering Models

You can list and apply multiple filters to the models, such as name, tag, creator's username, model type, sort order, time frame for sorting, and more. You can also save the results to a JSON file for further processing.

### Fetching Models by ID

Enter the model ID to fetch its details. Model details will be displayed in a concise format, showing essential details about the model, including its creator, description, stats, and version information.

### Downloading Models

Enter the model ID of the model you wish to download. You can specify the download directory or use the default directory.

### Changing Display Mode

Toggle between text-only mode and image display mode. In image display mode, a model's thumbnail will be displayed using `imgcat`.

### Model Types

The CLI categorizes models into several types:
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

That's it! Explore the CLI and utilize CivitAI's vast resources efficiently. For any further questions or issues, please refer to the official CivitAI documentation or raise an issue on this repository.
