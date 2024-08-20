# Notion to Google Sheets Sync

**Author:** McKenna Corn  
**Date Created:** August 8, 2024  
**Version:** 0.2.0

## Overview

This project is a Python script designed to synchronize data between a Notion database and Google Sheets. It compares data from both platforms and updates the Google Sheet accordingly with any new or modified entries. Additionally, it can append new rows if the information does not yet exist in the Google Sheet.

## Features

- **Data Syncing:** Automatically syncs Notion database content with Google Sheets.
- **Data Comparison:** Compares existing rows in Google Sheets and updates them if discrepancies are found.
- **New Entry Addition:** Adds new entries from Notion to Google Sheets if they don’t exist already.

## Getting Started

### Prerequisites

- **Python 3.6+**  
- **Required Libraries:**  
  - `notion_client`
  - `google-auth-oauthlib`
  - `google-auth-httplib2`
  - `google-auth`
  - `google-api-python-client`
  - `dotenv`

You can install the dependencies using the following command:

```bash
pip install notion-client google-auth-oauthlib google-auth-httplib2 google-auth google-api-python-client python-dotenv
```

### Setup

1. Clone this repository and navigate to the project directory.

2. Create a `.env` file and configure the following environment variables:

```env
SPREADSHEET_ID=your_google_sheet_id
RANGE_NAME=your_sheet_range_name
RANGE=your_sheet_range
NOTION_TOKEN=your_notion_integration_token
NOTION_PAGE_ID=your_notion_page_id
NOTION_DATABASE_ID=your_notion_database_id
```

3. Obtain your Google Sheets API credentials:
   - Follow the [Google Sheets API Quickstart Guide](https://developers.google.com/sheets/api/quickstart/python) to set up and download the `credentials.json` file.
   - Place the `credentials.json` file in the root directory of the project.

4. Run the script:

```bash
python main.py
```

### Usage

When running the script, you will be prompted to choose between refreshing the entire sheet or just adding recent entries:

- **Refresh:** Compares and updates the Google Sheet with all entries from Notion.
- **Add:** Only appends recent entries that are missing in the Google Sheet.

### Example Data Structure

A typical row in Google Sheets contains:

- Date
- Company
- Position
- Status
- Location
- Referral
- Website

## How It Works

1. **Data Fetching:** The script retrieves data from both Google Sheets and the Notion database using the respective APIs.

2. **Data Comparison:** It compares the rows based on the `Company` and `Position` fields to identify differences between the two sources.

3. **Sheet Update:** Based on the comparison, it either updates existing rows in Google Sheets or appends new entries.

4. **Status Mapping:** Notion's status fields (e.g., "1st Interview", "2nd Interview") are normalized to simpler labels like "Interview" for easier tracking in Google Sheets.

## Credits

- Notion API tutorial by [IndyDevDan](https://indydevdan.com/dev/notion-in-5-minutes)
- Google Sheets API usage inspired by [aakashadesara/notion-google-sheets-sync](https://github.com/aakashadesara/notion-google-sheets-sync)

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

---

This README provides clear instructions and an overview of the project while including credits and usage examples.