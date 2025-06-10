#!/usr/bin/env python3
"""
HTS TariffBot Setup Script
This script sets up the HTS TariffBot environment and downloads necessary data.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a shell command with error handling"""
    print(f"\n{'='*50}")
    print(f"🔄 {description}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False

# def check_python_version():
#     """Check if Python version is compatible"""
#     version = sys.version_info
#     if version.major < 3 or (version.major == 3 and version.minor < 8):
#         print("❌ Python 3.8+ is required")
#         return False
#     print(f"✅ Python {version.major}.{version.minor} is compatible")
#     return True

def create_directories():
    """Create necessary directories"""
    directories = ["data", "data/vector_db"]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")

def install_ollama():
    """Check and install Ollama if needed"""
    print("\n🤖 Checking Ollama installation...")
    
    # Check if Ollama is installed
    try:
        result = subprocess.run("ollama --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama is already installed")
            return True
    except:
        pass
    
    print("📥 Ollama not found. Please install Ollama:")
    print("1. Visit: https://ollama.ai")
    print("2. Download and install Ollama for your platform")
    print("3. Run: ollama pull llama2:7b")
    print("4. Run: ollama serve")
    
    return False

def setup_environment():
    """Setup the complete environment"""
    print("🚀 Setting up HTS TariffBot Environment")
    print("="*50)
    
    # # Check Python version
    # if not check_python_version():
    #     return False
    
    # Create directories
    create_directories()
    
    # # Install Python dependencies
    # if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
    #     return False
    
    # Check Ollama
    if not install_ollama():
        print("\n⚠️  Ollama setup required. Please install Ollama and pull models.")
        print("After Ollama setup, run: python data_ingestion.py")
        return False
    
    # Download HTS data
    print("\n📥 Downloading HTS data...")
    try:
        from data_ingestion import HTSDataIngestion
        ingestion = HTSDataIngestion()
        pdf_path, csv_files = ingestion.run_ingestion()
        print(f"✅ Downloaded {len(csv_files)} CSV files and PDF")
    except Exception as e:
        print(f"⚠️  Error downloading data: {e}")
        print("You can manually run: python data_ingestion.py")
    
    print("\n🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Ensure Ollama is running: ollama serve")
    print("2. Pull the model: ollama pull llama2:7b")
    print("3. Run the app: streamlit run app.py")
    
    return True

if __name__ == "__main__":
    setup_environment()