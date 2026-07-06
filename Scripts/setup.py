#!/usr/bin/env python3
"""
Setup script for College Assistant - initializes all required dependencies and data
"""

import os
import sys
import json
from pathlib import Path

# Fix encoding issues in Windows console
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


def setup_environment():
    """Check and setup Python environment"""
    print("=" * 60)
    print("College Assistant - Setup")
    print("=" * 60)
    print(f"Python Version: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    print()

def check_and_install_dependencies():
    """Check for required packages and install if missing"""
    print("📦 Checking dependencies...")
    required_packages = [
        'flask',
        'openai',
        'faiss-cpu',
        'sentence-transformers',
        'torch',
        'chardet',
    ]
    
    import subprocess
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✓ {package} is installed")
        except ImportError:
            print(f"  ✗ {package} is missing, installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"  ✓ {package} installed successfully")
    print()

def check_data_files():
    """Check if data files exist"""
    print("📂 Checking data files...")
    
    data_files = [
        "../output/notice_dataset.json",
        "../output/dbgi_structured.json",
    ]
    
    for file in data_files:
        full_path = os.path.join(os.path.dirname(__file__), file)
        if os.path.exists(full_path):
            # Get file size
            size = os.path.getsize(full_path) / 1024  # KB
            print(f"  ✓ {file} ({size:.1f} KB)")
        else:
            print(f"  ✗ {file} NOT FOUND")
    print()

def check_vector_db():
    """Check if FAISS index exists"""
    print("🔍 Checking Vector Database...")
    
    index_path = "../vector_db/notice_index.faiss"
    full_path = os.path.join(os.path.dirname(__file__), index_path)
    
    if os.path.exists(full_path):
        size = os.path.getsize(full_path) / (1024 * 1024)  # MB
        print(f"  ✓ FAISS Index exists ({size:.2f} MB)")
    else:
        print(f"  ✗ FAISS Index NOT FOUND - will be created on first run")
    print()

def check_web_files():
    """Check if web assets exist"""
    print("🌐 Checking web files...")
    
    web_files = [
        "templates/index.html",
        "static/app.js",
        "static/styles.css",
    ]
    
    for file in web_files:
        full_path = os.path.join(os.path.dirname(__file__), file)
        if os.path.exists(full_path):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} NOT FOUND")
    print()

def main():
    """Run all setup checks"""
    try:
        setup_environment()
        check_and_install_dependencies()
        check_data_files()
        check_vector_db()
        check_web_files()
        
        print("=" * 60)
        print("✅ Setup check complete!")
        print("=" * 60)
        print()
        print("To run the application:")
        print("  python app.py")
        print()
        print("Then open: http://localhost:5000")
        print()
        print("Configuration:")
        print("  - Optional: Set OPENAI_API_KEY environment variable for GPT support")
        print("  - Without OpenAI key, the system will use local RAG responses")
        print()
        
    except Exception as e:
        print(f"❌ Setup error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
