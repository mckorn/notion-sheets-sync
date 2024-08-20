"""
File Name: main.py
Author: McKenna Corn
Date created: 2024-08-08
Version: 0.2.0

This project synchronizes data between Notion and Google Sheets. 
The script reads data from a Notion database and a Google Sheet, compares the data, and updates the Google Sheet with the new information. 
The script can also add new entries to the Google Sheet.

Credits:
- Notion API tutorial by IndyDevDan (repository): https://indydevdan.com/dev/notion-in-5-minutes
- Google Sheets API usage: https://github.com/aakashadesara/notion-google-sheets-sync
"""

import pickle
import os.path
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# we want a client library (100% test coverage)
from notion_client import Client
import json

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# how notion knows you are a valid user (now you officially validate your notion api)
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
RANGE_NAME = os.getenv("RANGE_NAME")
RANGE = os.getenv("RANGE")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Row in Google Sheets Data
row = {
    "Date": "06-29",
    "Company": "NASA",
    "Position": "Software Engineer",
    "Status": "Applied",
    "Location": "Raleigh, NC",
    "Feferral": "FALSE",
    "Website": "https://www.example.com",
}

# Function to get the data from google sheets
def get_sheet():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("sheets", "v4", credentials=creds)

    sheet = service.spreadsheets()
    result = (
        sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    )
    values = result.get("values", [])

    rows = []
    first_row = values[0]
    for row in values:
        length = len(row)
        row_object = {}
        for i, value in enumerate(row):
            row_object[f"{first_row[i]}"] = value
        if length < 8:
            row_object["Website"] = None

        rows.append(row_object)

    if not values:
        print("No data found.")
        return None
    else:
        rows = rows[1:]
        print("%s rows found in sheet." % len(values))
        return rows

# Function to write data to google sheets
def write_to_sheet(
    row, append, date, type, company, position, status, location, referral, website
):
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("sheets", "v4", credentials=creds)
    
    if append is False:
        # Update the values
        body = {
            "values": [
                [
                    date,
                    type,
                    company,
                    position,
                    status,
                    location,
                    referral,
                    website,
                ]
            ]
        }
        result = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=SPREADSHEET_ID,
                range="2024Cycle!B{}:I{}".format(row, row),
                valueInputOption="USER_ENTERED",  # How to interpret input data
                body=body,
            )
            .execute()
        )
        print(f"{result.get('updatedCells')} cells updated with position {position}")
    else:
        # New row to append
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE,
            valueInputOption="USER_ENTERED",
            responseValueRenderOption="FORMATTED_VALUE",
            insertDataOption="INSERT_ROWS",
            body={
                "values": [
                    [
                        date,
                        type,
                        company,
                        position,
                        status,
                        location,
                        referral,
                        website,
                    ]
                ]
            },
        ).execute()

# Function to write data to google sheets
def write_to_sheet_temp(
    row, append, job
):
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("sheets", "v4", credentials=creds)
    if append is False:
        # Update the values
        body = {
            "values": [
            [
                job['Date'],
                job['Type'],
                job['Company'],
                job['Position'],
                job['Status'],
                job['Location'],
                job['Referral'],
                job['Website'],
            ]
            ]
        }
        result = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=SPREADSHEET_ID,
                range="2024Cycle!B{}:I{}".format(row, row),
                valueInputOption="USER_ENTERED",  # How to interpret input data
                body=body,
            )
            .execute()
        )
        print(f"{result.get('updatedCells')} cells updated with position {job['Position']}")
    else:
        # New row to append
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE,
            valueInputOption="USER_ENTERED",
            responseValueRenderOption="FORMATTED_VALUE",
            insertDataOption="INSERT_ROWS",
            body={
                "values": [
                    [
                        job['Date'],
                        job['Type'],
                        job['Company'],
                        job['Position'],
                        job['Status'],
                        job['Location'],
                        job['Referral'],
                        job['Website'],
                    ]
                ]
            },
        ).execute()

# Compares the rows from Notion and Google Sheets
def compare_rows(r1, r2):
    # print('comparing rows')
    #print(r1) # row from notion
    #print(r2) # row from google sheets

    # extract data from notion
    # ( I had date in here but I don't think it's necessary)
    r1_status = r1["Status"]
    r1_company = r1["Company"]
    r1_position = r1["Position"]
    r1_location = r1["Location"]
    r1_website = r1["Website"]
    r1_referral = r1["Referral"]

    r2_status = r2["Status"]
    r2_company = r2["Company"]
    r2_position = r2["Position"]
    r2_location = r2["Location"]
    r2_website = r2["Website"]
    r2_referral = r2["Referral?"]
    
    # first check if its the same job
    if r1_company == r2_company and r1_position == r2_position:
        # check if the other elements are different
        if r1_status != r2_status or r1_location != r2_location or r1_referral != r2_referral or r1_website != r2_website:
            return 1 # the row is not updated
        return 0 # they are the same row
    else:
        return -1 # different row

# Parses the application status from Notion to a readable format in sheets
def convert_n_to_s_status(status):
    if status == "1st Interview" or status == "2nd Interview" or status == "3rd Interview":
        return "Interview"
    else:
        return status
        
# Parses the referral status from Notion to a readable format in sheets
def convert_n_to_s_boolean(status):
    if status:
        return "TRUE"
    else:
        return "FALSE"

# Function to get block children from Notion
def read_text(client, page_id):
    # block_id is gonna be page (pages are also represented as a block)
    response = client.blocks.children.list(block_id=page_id)
    return response["results"]

# Function to parse data from Notion (Source: IndyDevDan)
def safe_get(data, dot_chained_keys):
    """
    {'a': {'b': [{'c': 1}]}}
    safe_get(data, 'a.b.0.c') -> 1
    """
    keys = dot_chained_keys.split(".")
    for key in keys:
        try:
            if isinstance(data, list):
                data = data[int(key)]
            else:
                data = data[key]
        except (KeyError, TypeError, IndexError):
            return None
    return data

# Function to write data to a file 
def write_dict_to_file_json(content, file_name):
    if not os.path.exists("data"):
        os.makedirs("data")
        
    file_path = os.path.join("data", file_name)
    
    json_str = json.dumps(content)

    with open(file_path, "w") as f:
        f.write(json_str)

# Gets the content from the Notion database and puts it in object form
def get_database(content):
    rows = []
    for row in content["results"]:
        #languages = safe_get(row, "properties.Languages.multi_select.0.name")
        interview_stage = safe_get(row, "properties.Status.status.name")
        location = safe_get(row, "properties.Location.select.name")
        company = safe_get(row, "properties.Name.rollup.array.0.title.0.plain_text")
        website = safe_get(row, "properties.Website.rich_text.0.plain_text")
        date = safe_get(row, "properties.Date.date.start")
        position = safe_get(row, "properties.Position.title.0.plain_text")
        referral = safe_get(row, "properties.Referral.checkbox")

        if not position:
            print('error')
            continue
        
        # format data
        ref = convert_n_to_s_boolean(referral)
        
        status = convert_n_to_s_status(interview_stage)
        
        if date:
            formatted_date = date[5:]  # gets the last 5 elements of the date
        else:
            formatted_date = None
            
        if not location:
            location = ''
        
        rows.append(
            {
                "Date": formatted_date,
                "Type": "Job",
                "Company": company,
                "Position": position,
                "Status": status,
                "Location": location,
                "Referral": ref,
                "Website": website,
            }
        )
    return rows

def main():
    # 0. Ask the user if they want to refresh the sheet or just add recent entries (so there is no delay after executing script)
    choice = input(
        "do you want to refresh your sheet or just add recent entries? (r/a): "
    )

    # 1. Get the data from Notion
    client = Client(auth=NOTION_TOKEN)
    content = read_text(client, NOTION_PAGE_ID)
    write_dict_to_file_json(content, "content.json")
    db_rows = client.databases.query(NOTION_DATABASE_ID, sorts=[{"property": "Date", "direction": "descending"}])
    write_dict_to_file_json(db_rows, "db_rows.json")
    simplified_rows = get_database(db_rows)
    write_dict_to_file_json(simplified_rows, "rows.json")

    # 2. Get the data from Google Sheets
    data = get_sheet()
    write_dict_to_file_json(data, "sheet.json")

    i = 0
    j = -1
    needsUpdate = False
    if choice == "r":
        # 3a. Take that new information and update the sheets database with the new information
        for row in simplified_rows:
            try:
                result = compare_rows(simplified_rows[j], data[i])
            except IndexError:
                print("you have a new row to add that is not on the list, try appending")
                return
            if result == 0:
                # rows are the same
                i += 1
                j -= 1
                continue
            elif result == 1:
                needsUpdate = True
                # take google sheets and overwrite it if the notion row is different
                write_to_sheet_temp(
                    i + 3,
                    False,
                    simplified_rows[j]
                )
            else:
                needsUpdate = True
                # iterate down the sheet until we find the same job
                original_i = i
                r = -1
                i += 1
                # check to see if this is a notion exclusive row
                while r == -1 and i < len(data):
                    # iterate down the sheet until we find the same job
                    r = compare_rows(simplified_rows[j], data[i])
                    i += 1

                # analyze the results from compare rows
                if r == -1:
                    #print("job not found in google sheets")
                    # one last check... up
                    i = original_i
                    while r == -1 and i >= 0:
                        r = compare_rows(simplified_rows[j], data[i])
                        i -= 1
                        
                    if r == 1 or r == 0:
                        write_to_sheet_temp(
                            i + 4, # this is 4 because of the extra i missing when exiting the while loop
                            False,
                            simplified_rows[j]
                        )
                        i = original_i
                        i += 1
                        j -= 1
                        continue
                        
                    write_to_sheet_temp(
                        -1,
                        True,
                        simplified_rows[j]
                    )
                    i = original_i
                    i += 1
                    j -= 1
                    continue
                elif r == 1:
                    #print("job found in google sheets but needs updating")
                    write_to_sheet_temp(
                        i + 2, # this is 2 because of the extra i when exiting the while loop
                        False,
                        simplified_rows[j]
                    )
                else:
                    print('found the same job and it is up to date')

                i = original_i
                
            i += 1
            j -= 1
    elif choice == "a":
        needsUpdate = True
        # 3b. or just add your new row to the google sheets
        result = compare_rows(simplified_rows[0], data[-1])
        if (result == 0):  # checking the most recent rows
            print("there is no new row for you to add")
        else:
            print("updating rows")
            if (result == 1):
                row_num = len(data) + 3 # the length is title row + # of rows so we need to add 1
                write_to_sheet_temp(row_num, False, simplified_rows[0])
            else:
                write_to_sheet_temp(-1, True, simplified_rows[0])
            
            # TODO implement so that it goes up the list until it finds a job that is already in the sheet and start adding from there
    else:
        print("invalid input, choose again")

    if needsUpdate is False:
        print("your sheet is up to date!") 
    # date = "2021-6-29"
    # print(date[-5:]) # ending start, including 5th character
    # print(date[5:]) # ending start, excluding 5th character
    # print(date[:-5]) # beginning start, excluding 5th character
    # print(date[:5]) # beginning start, including 5th character
    # negative version will always be the smaller one

if __name__ == "__main__":
    main()
