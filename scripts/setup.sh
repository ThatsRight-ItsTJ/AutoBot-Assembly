#!/bin/bash

# AutoBot Assembly System Setup Script
# This script installs all required dependencies and sets up the development environment

set -e  # Exit on any error

echo "🤖 AutoBot Assembly System Setup"
echo "================================="

# Check if running on supported OS
if [[ "$OSTYPE" != "linux-gnu"* ]] && [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script supports Linux and macOS only"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install package managers
install_package_managers() {
    echo "📦 Checking package managers..."
    
    # Check for package manager on Linux
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if ! command_exists apt && ! command_exists yum && ! command_exists pacman; then
            echo "❌ No supported package manager found (apt, yum, or pacman)"
            exit 1
        fi
    fi
    
    # Check for Homebrew on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if ! command_exists brew; then
            echo "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
    fi
}

# Function to install Python dependencies
install_python_deps() {
    echo "🐍 Installing Python dependencies..."
    
    # Check Python version
    if ! command_exists python3; then
        echo "❌ Python 3 is required but not installed"
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    required_version="3.9"
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
        echo "❌ Python 3.9+ is required, found $python_version"
        exit 1
    fi
    
    # Install pip if not available
    if ! command_exists pip3; then
        echo "Installing pip..."
        curl https://bootstrap.pypa.io/get-pip.py | python3
    fi
    
    # Install Python packages
    echo "Installing Python packages from requirements.txt..."
    pip3 install -r requirements.txt
    
    echo "✅ Python dependencies installed"
}

# Function to install Ruby and github-linguist
install_ruby_deps() {
    echo "💎 Installing Ruby dependencies..."
    
    if ! command_exists ruby; then
        echo "Installing Ruby..."
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            if command_exists apt; then
                sudo apt update && sudo apt install -y ruby-full
            elif command_exists yum; then
                sudo yum install -y ruby ruby-devel
            elif command_exists pacman; then
                sudo pacman -S ruby
            fi
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew install ruby
        fi
    fi
    
    # Install github-linguist
    echo "Installing github-linguist gem..."
    gem install github-linguist
    
    echo "✅ Ruby dependencies installed"
}

# Function to install Rust and ast-grep
install_rust_deps() {
    echo "🦀 Installing Rust dependencies..."
    
    if ! command_exists cargo; then
        echo "Installing Rust..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        source $HOME/.cargo/env
    fi
    
    # Install ast-grep
    echo "Installing ast-grep..."
    cargo install ast-grep
    
    echo "✅ Rust dependencies installed"
}

# Function to install Node.js dependencies (optional)
install_node_deps() {
    echo "📦 Installing Node.js dependencies (optional)..."
    
    if ! command_exists node; then
        echo "Node.js not found. Installing..."
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
            sudo apt-get install -y nodejs
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew install node
        fi
    fi
    
    if command_exists npm; then
        echo "Installing ESLint for JavaScript analysis..."
        npm install -g eslint @eslint/js
    fi
    
    echo "✅ Node.js dependencies installed"
}

# Function to install Docker
install_docker() {
    echo "🐳 Installing Docker..."
    
    if ! command_exists docker; then
        echo "Installing Docker..."
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            curl -fsSL https://get.docker.com -o get-docker.sh
            sh get-docker.sh
            sudo usermod -aG docker $USER
            echo "⚠️  Please log out and back in for Docker permissions to take effect"
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            echo "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
            echo "This script cannot automatically install Docker Desktop on macOS"
            return
        fi
    fi
    
    # Pull required Docker images
    echo "Pulling required Docker images..."
    docker pull oxsecurity/megalinter:v7
    docker pull redis:alpine
    
    echo "✅ Docker setup complete"
}

# Function to clone required repositories
clone_repositories() {
    echo "📂 Cloning required repositories..."
    
    mkdir -p external_repos
    cd external_repos
    
    # Clone GitHub-File-Seek (core integration)
    if [ ! -d "GitHub-File-Seek" ]; then
        echo "Cloning GitHub-File-Seek..."
        git clone https://github.com/ThatsRight-ItsTJ/GitHub-File-Seek.git
    fi
    
    # Clone reference repositories
    if [ ! -d "linguist" ]; then
        echo "Cloning github-linguist for patterns..."
        git clone https://github.com/github/linguist.git
    fi
    
    if [ ! -d "licensee" ]; then
        echo "Cloning licensee for license detection..."
        git clone https://github.com/licensee/licensee.git
    fi
    
    if [ ! -d "awesome" ]; then
        echo "Cloning awesome lists..."
        git clone https://github.com/sindresorhus/awesome.git
    fi
    
    cd ..
    echo "✅ Repositories cloned"
}

# Function to setup environment
setup_environment() {
    echo "⚙️  Setting up environment..."
    
    # Copy environment template
    if [ ! -f ".env" ]; then
        cp .env.example .env
        echo "📝 Created .env file from template"
        echo "⚠️  Please edit .env file with your API keys:"
        echo "   - GITHUB_TOKEN: Get from https://github.com/settings/tokens"
        echo "   - LIBRARIES_IO_API_KEY: Get from https://libraries.io/account"
    fi
    
    # Make scripts executable
    chmod +x scripts/*.sh
    
    # Create necessary directories
    mkdir -p logs cache temp
    
    echo "✅ Environment setup complete"
}

# Function to test installation
test_installation() {
    echo "🧪 Testing installation..."
    
    # Test Python imports
    python3 -c "
import asyncio
import aiohttp
import github
import docker
print('✅ Python dependencies OK')
"
    
    # Test external tools
    if command_exists docker; then
        docker --version
        echo "✅ Docker OK"
    fi
    
    if command_exists ruby && gem list | grep -q github-linguist; then
        echo "✅ GitHub Linguist OK"
    fi
    
    if command_exists ast-grep; then
        ast-grep --version
        echo "✅ AST-grep OK"
    fi
    
    echo "✅ Installation test complete"
}

# Main installation flow
main() {
    echo "Starting AutoBot Assembly System setup..."
    
    install_package_managers
    install_python_deps
    install_ruby_deps
    install_rust_deps
    install_node_deps
    install_docker
    clone_repositories
    setup_environment
    test_installation
    
    echo ""
    echo "🎉 Setup Complete!"
    echo "=================="
    echo ""
    echo "Next steps:"
    echo "1. Edit .env file with your API keys"
    echo "2. Test the system: python3 scripts/test_workflow.py"
    echo "3. Read the documentation in README.md"
    echo ""
    echo "For GitHub-File-Seek integration:"
    echo "1. cd external_repos/GitHub-File-Seek"
    echo "2. Follow their setup instructions"
    echo ""
}

# Run main function
main "$@"