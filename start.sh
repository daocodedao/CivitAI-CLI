#!/bin/bash


# Function to detect OS
detect_os() {
  if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "linux"
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "macos"
  elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "windows"
  else
    echo "unknown"
  fi
}


# Detect the OS
OS=$(detect_os)


# Check if Python is installed
if ! python --version >/dev/null 2>&1 && ! python3 --version >/dev/null 2>&1; then
  OS=$(detect_os)
  echo "Python is not installed. Please install it first."
  exit 1
fi

# Check if virtualenv is installed, install it if not
if ! virtualenv --version >/dev/null 2>&1; then
  pip install virtualenv || pip3 install virtualenv || exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "myenv" ]; then
  virtualenv myenv || exit 1
fi

# Activate virtual environment
OS=$(detect_os)
if [[ "$OS" == "windows" ]]; then
  source myenv/Scripts/activate || exit 1
else
  source myenv/bin/activate || exit 1
fi

# Install Python Dependencies if not already installed
if ! pip freeze | grep -q -f requirements.txt; then
  pip install -r requirements.txt || exit 1
fi

# Source Rust environment variables
source "$HOME/.cargo/env"

# Check for Rust, install if not present
if ! rustc --version >/dev/null 2>&1; then
  #echo "Debug: Installing Rust."
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y || exit 1
fi


#echo "Debug: Checking for VIU."
# Install VIU if not present
if ! cargo install --list | grep -q 'viu'; then
  git clone https://github.com/atanunq/viu.git || exit 1
  cd viu/ || exit 1
  cargo install --path . || exit 1
  cd ..
fi

#echo "Debug: Running main.py."
# Run the main program
python main.py || python3 main.py || exit 1

sleep 1

# Clear terminal depending on the OS
if [[ "$OS" == "linux" || "$OS" == "macos" ]]; then
  clear
elif [[ "$OS" == "windows" ]]; then
  cls
fi
