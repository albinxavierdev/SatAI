# ISRO API Data Downloader

This folder contains a Python script to download JSON data from the ISRO API and store it locally for offline use.

## Files

- `download_isro_data.py` - Main Python script to download data
- `requirements.txt` - Python dependencies
- `README.md` - This file

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the download script:
   ```bash
   python download_isro_data.py
   ```

## What it downloads

The script downloads data from all available ISRO API endpoints:

- **spacecrafts.json** - Spacecraft data
- **launchers.json** - Rocket launcher data  
- **customer_satellites.json** - Customer satellite data
- **centres.json** - ISRO center information

## Output

All JSON files are saved in the `db` folder with proper formatting and UTF-8 encoding. The script provides progress feedback and error handling for each endpoint.

## API Source

Data is sourced from the [ISRO API](https://github.com/isro/api) hosted at [isro.vercel.app](https://isro.vercel.app).

## Usage Notes

- The script includes a 1-second delay between requests to be respectful to the API
- All downloads include error handling and validation
- JSON files are formatted with proper indentation for readability
- File sizes and record counts are displayed after successful downloads
