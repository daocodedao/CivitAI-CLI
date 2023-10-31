![Banner](assets/banner.png)

## Introduction

**CivitAI-CLI: Streamlined Access to CivitAI Models**

The CivitAI-CLI is a command-line interface tool crafted to enhance user interactions with the [CivitAI API](https://civitai.com). Its primary goal is to simplify the processes of listing, displaying, fetching, and downloading models available on CivitAI.

**Key Features of CivitAI-CLI:**

- **Efficient Interactions**: CivitAI-CLI provides a user-friendly approach, eliminating the complexities of manual API endpoint handling. Easily fetch, list, and download models straight from your terminal.

- **Optimized Visual Experience with `viu`**: The tool leverages `viu` for image rendering, offering improved visual feedback in terminals such as iTerm2 and Kitty. For those on alternative terminals, an ANSI display is available to ensure consistent user experience.

- **Enhanced Functionality with an API Key**: While CivitAI-CLI is versatile without an API key, possessing one grants access to an extended array of features.

**The Genesis of CivitAI-CLI:**

Developed out of a specific need to download models on remote servers via SSH, especially for servers running stable diffusion systems, the CivitAI-CLI addresses this niche requirement, ensuring efficient access to CivitAI's models regardless of the user's location.


CivitAI may house a myriad of models, ranging from the academically serious to the more leisurely. However, the CivitAI-CLI aims to be a tool of choice for anyone seeking a streamlined interface to this platform. 

## Table of Contents

- [Installation](#installation)
- [Installing VIU](#installing-viu)
- [Environment Variables (Optional)](#environment-variables-optional)
- [Usage](#usage)
  - [Main Menu](#main-menu)
  - [Settings Menu](#settings-menu)
  - [Browsing Options](#browsing-options)
  - [Model Types](#model-types)

## Installation

To utilize CivitAI-CLI and ensure a clean environment without dependency conflicts, it's recommended to install it within a Python virtual environment (venv). Here are the steps to clone the repository, set up a venv, and install the necessary dependencies:

### Prerequisites

Ensure you have Python 3.6 or later and `pip` installed on your system. If not, download and install Python from [the official website](https://www.python.org/) and `pip` will be included.

### Clone the Repository

To quickly set up, you can use the following one-liner:

```bash
git clone https://github.com/roadmaus/CivitAI-CLI.git && cd CivitAI-CLI && [[ -x start.sh ]] || chmod +x start.sh && ./start.sh
```

Or you can manually clone it:

```bash
git clone https://github.com/roadmaus/CivitAI-CLI.git
cd CivitAI-CLI
```

### Setup Virtual Environment (venv)

To create and activate a virtual environment:

#### For Windows

```bash
python -m venv myenv
.\myenv\Scripts\activate
```

#### For MacOS/Linux

```bash
python3 -m venv myenv
source myenv/bin/activate
```

**Note:** Ensure your shell is in the directory where `myenv` is created. Also windows support is not tested yet and will likely break.

### Install Dependencies

With the virtual environment activated, install the dependencies:

```bash
pip install -r requirements.txt
```

**To deactivate the virtual environment when you're done:**

```bash
deactivate
```

After setting up and activating your venv, you can use CivitAI-CLI while keeping your Python environment clean and managed.

## Installing VIU

For the most up-to-date installation instructions for `viu`, please refer to the [official repository](https://github.com/atanunq/viu).

## Environment Variables (Optional)

To access additional features, set the `CIVITAI_API_KEY` environment variable with your API key:

```bash
export CIVITAI_API_KEY=your_api_key_here
```

## Usage

Explore the various functionalities provided by CivitAI-CLI:

### Main Menu

```
 > List models
   Fetch model by ID
   Download model by ID
   Scan for missing data
   No interrupted downloads
   Fetch model version by ID
   Fetch model by Hash
   Settings
   Exit
```

### Settings Menu

```
 > Change display mode
   Adjust image size
   Set default query
   Set model version preference
   Set root directory
   Back to main menu
```

### Browsing Options

```
 > Next page
   Previous page
   Jump to page
   Filter this search
   Search Model
   Select to Download
   Initiate Download
   Initiate Background Download
   Select for more Info
   Back to main menu
```

**Model Display Example**

Displayed using text mode:
```
🆔 ID: 157458
🌐 URL: https://civitai.com/models/157458
📛 Name: The Devil (The Cuphead Show) Cartoon Character LoRA
👤 Creator: PlagSoft
🤖 Type: LoCon
🛠️ Base Models: SD 1.5
⭐ Rating: 0
🔞 NSFW: False
🏷️ Tags: character, cartoon, demon, cuphead, character，, devil, 1930s
📦 File Size: 29.67 MB

-- Scans --
🐍 Pickle Scan: Success
🔬 Virus Scan: Success
🗓️ Scanned At: 2023-10-06T03:45:42.181Z

-- Description --
📝 Description: "♪ In case you ain't heard, I'm the Devil! I'm a real low-down, not on the level!" These are the results of my first experiments with a Google Colab LoRA maker. Early versions were made with PixAI and l...
```

**Visual Showcase**

Here's how CivitAI-CLI displays models in the iTerm2 terminal using `viu`:
![Model Display in iTerm2 with viu](assets/example.png)

And here's a display in a standard terminal using the ANSI display:
![Model Display in Standard Terminal with ANSI](assets/ansi_example.png)


## Current State and Functionalities

CivitAI-CLI presently allows users to:

- List and filter models
- Download models
- Fetch model info
- Set a default query and download path (aligns with Automatic1111's webui directory structure)
- Scan for missing metadata (currently it replaces old metadata if not in the same format)
- Switch display mode between Text only or Image
- Adjust image sizes
- Set a content filter for images (options: block, blur, or show)
- Resume interrupted downloads (partially implemented)
- check for updated versions
- install and run it using the one-liner (or install script)

### To-Do

Future updates aim to provide:

- Enhanced model cards for details
- Fetching models by hash
- Improved metadata management
