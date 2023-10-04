![Banner](banner.png)

# CivitAI-CLI

## Introduction

CivitAI-CLI is a command-line interface tool designed to interact with the CivitAI API, allowing users to efficiently fetch, display, list, and download models hosted on [CivitAI](https://civitai.com). Utilizing `viu` for image rendering, it provides an enhanced user experience in terminals like iTerm2 and Kitty, with a fallback to ANSI display in others. While the tool offers several features without an API key, having one unlocks additional functionalities.

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

To install and use CivitAI-CLI, clone this repository and ensure you have all the necessary dependencies installed.

```bash
git clone https://github.com/roadmaus/CivitAI-CLI.git
pip install -r requirements.txt
```

## Installing VIU

### From Source (Recommended)

```bash
git clone https://github.com/atanunq/viu.git
cd viu/
cargo install --path .
```

Or without cloning:

```bash
cargo install viu
```

### Binary

Precompiled binary available on the [release page](https://github.com/atanunq/viu/releases). GPG fingerprint: `B195BADA40BEF20E4907A5AC628280A0217A7B0F`.

### Packages

**MacOS**

```bash
brew install viu
```

**Arch Linux**

```bash
pacman -S viu
```

**NetBSD**

Available in graphics/viu.

## Environment Variables (Optional)

To unlock additional features, set the `CIVITAI_API_KEY` environment variable with your API key.

```bash
export CIVITAI_API_KEY=your_api_key_here
```

## Usage

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

### Model Types

Models in the CLI are categorized into several types, including but not limited to:
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

Explore CivitAI-CLI and harness the capabilities of CivitAI's extensive resources. For further inquiries or issues, refer to the official CivitAI documentation or raise an issue on this repository.
