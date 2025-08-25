#!/usr/bin/env python3
"""
ISRO API Data Downloader

This script downloads JSON data from all ISRO API endpoints and stores them
in the db folder for local use.
"""

import requests
import json
import os
from pathlib import Path
import time

# Base URL for ISRO API
BASE_URL = "https://isro.vercel.app"

# API endpoints to download
API_ENDPOINTS = [
    "/api/spacecrafts",
    "/api/launchers", 
    "/api/customer_satellites",
    "/api/centres"
]

def download_json_data(endpoint, output_dir):
    """
    Download JSON data from a specific API endpoint and save it to a file.
    
    Args:
        endpoint (str): The API endpoint path
        output_dir (Path): Directory to save the JSON file
    """
    url = f"{BASE_URL}{endpoint}"
    filename = endpoint.replace("/api/", "") + ".json"
    filepath = output_dir / filename
    
    try:
        print(f"Downloading {endpoint}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Parse JSON to validate it's valid
        data = response.json()
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved {filename} ({len(data)} records)")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Error downloading {endpoint}: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing JSON from {endpoint}: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error with {endpoint}: {e}")
        return False

def main():
    """Main function to download all ISRO API data."""
    # Create output directory
    output_dir = Path(".")
    output_dir.mkdir(exist_ok=True)
    
    print("🚀 ISRO API Data Downloader")
    print("=" * 40)
    print(f"Output directory: {output_dir.absolute()}")
    print()
    
    # Download data from each endpoint
    successful_downloads = 0
    total_endpoints = len(API_ENDPOINTS)
    
    for endpoint in API_ENDPOINTS:
        if download_json_data(endpoint, output_dir):
            successful_downloads += 1
        
        # Add a small delay between requests to be respectful
        time.sleep(1)
    
    print()
    print("=" * 40)
    print(f"Download complete: {successful_downloads}/{total_endpoints} endpoints successful")
    
    if successful_downloads == total_endpoints:
        print("🎉 All data downloaded successfully!")
    else:
        print("⚠️  Some downloads failed. Check the error messages above.")
    
    # List downloaded files
    print("\nDownloaded files:")
    for file in output_dir.glob("*.json"):
        file_size = file.stat().st_size
        print(f"  • {file.name} ({file_size:,} bytes)")

if __name__ == "__main__":
    main()
