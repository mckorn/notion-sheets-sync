import pickle
import os.path
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# we want a client library (100% test coverage)
from notion_client import Client
import json
from pprint import pprint

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
    "date": "29-06",
    "type": "Job",
    "company": "NASA",
    "position": "Software Engineer",
    "status": "Applied",
    "location": "Raleigh, NC",
    "referral": 'FALSE',
    "website": "https://www.example.com",
}


# Functions for Google Sheets data connection

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
            row_object["Website"] = ''
        
        rows.append(row_object)

    if not values:
        print("No data found.")
        return None
    else:
        rows = rows[1:]
        print("%s rows found." % len(values))
        return rows

# Function to write data to google sheets
def write_to_sheet(row, date, type, company, position, status, location, referral, website):
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
    
    
    # format the data
    
    # date
    formatted_date = date[5:] # gets the last 5 elements of the date
    
    # status
    formatted_stat = convert_n_to_s_status(status)
    
    if row != 0:
        # Update the values
        body = {
            'values': [
                [formatted_date, type, company, position, formatted_stat, location, referral, website]
            ]
        }
        result = service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range='2024Cycle!B{}:I{}'.format(row, row),
            valueInputOption='USER_ENTERED',  # How to interpret input data
            body=body
        ).execute()
        print(f"{result.get('updatedCells')} cells updated.")
    else:
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE,
            valueInputOption="USER_ENTERED",
            responseValueRenderOption="FORMATTED_VALUE",
            insertDataOption="INSERT_ROWS",
            body={
                "values": [
                    [formatted_date, type, company, position, formatted_stat, location, referral, website]
                ]
            },
        ).execute()
    print("super success !!!!!!!!!!!!!!!!")

def compare_rows(r1, r2):
    print('print rows')
    print(r1) # row from notion
    print(r2) # row from google sheets
    
    # extract data from notion
    r1_status = r1["status"]
    r1_company = r1["company"]
    r1_position = r1["position"]    
    r1_location = r1["location"]
    r1_website = r1["website"]
    r1_date = r1["date"]
    r1_referral = r1["referral"]  
    
    r2_status = r2["Status"]
    r2_company = r2["Company"]
    r2_position = r2["Position"]
    r2_location = r2["Location"]
    r2_website = r2["Website"]
    r2_date = r2["Date"]
    r2_referral = r2["Referral?"] 

        
    
    # first check if its the same job
    if r1_company == r2["Company"] and r1_position == r2["Position"]:
        print("same job")
        # check if the status is different
        if r1_status != r2_status or r1_location != r2_location:
            return 1
        return 0
    else:
        print("different job")
        return -1

def convert_n_to_s_status(status):
    if status == 'Applied':
        return 'Applied'
    if status == 'Coding Challenge':
        return 'Coding Challenge'
    elif status == 'Rejected':
        return 'Rejected'
    elif status == 'Need to Apply':
        return 'Need to Apply'
    elif status == 'Waitlisted':
        return 'Waitlisted'
    else:
        return 'Interview'

# Function to create a paragraph block for each string in the array
def write_p_block(text):
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }

def write_text(client, page_id, text):
    # block_id is gonna be page (pages are also represented as a block)
    client.blocks.children.append(
        block_id=page_id,
        children=[
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                },
            }
        ],
    )

def read_text(client, page_id):
    # block_id is gonna be page (pages are also represented as a block)
    response = client.blocks.children.list(block_id=page_id)
    return response["results"]

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

def create_simple_blocks_from_content(client, content):
    p_blocks = []

    for block in content:
        block_id = block["id"]
        block_type = block["type"]
        has_children = block["has_children"]
        rich_text = block[block_type]["rich_text"]

        # if we don't have any text
        if not rich_text:
            return

        p_block = {
            "id": block_id,
            "type": block_type,
            "text": rich_text[0]["plain_text"],
        }

        if has_children:
            nested_children = read_text(client, block_id)
            # recursive call for this block
            p_block["children"] = create_simple_blocks_from_content(
                client, nested_children
            )

        p_blocks.append(p_block)

    return p_blocks

def write_dict_to_file_json(content, file_name):
    json_str = json.dumps(content)

    with open(file_name, "w") as f:
        f.write(json_str)

def get_database(content):
    rows = []
    for row in content["results"]:
        languages = safe_get(row, "properties.Languages.multi_select.0.name")
        interview_stage = safe_get(row, "properties.Status.status.name")
        location = safe_get(row, "properties.Location.select.name")
        company = safe_get(row, "properties.Name.rollup.array.0.title.0.plain_text")
        website = safe_get(row, "properties.Website.rich_text.0.plain_text")
        date = safe_get(row, "properties.Date.date.start")
        position = safe_get(row, "properties.Position.title.0.plain_text")
        referral = safe_get(row, "properties.Referral.checkbox")

        if not position:
            continue

        rows.append(
            {
                "languages": languages,
                "status": interview_stage,
                "location": location,
                "company": company,
                "website": website,
                "date": date,
                "position": position,
                "referral": referral,
            }
        )
    return rows

def create_default_database(client):
    # Define the default database properties
    properties = {
        "Name": {"type": "title", "title": {}},
        "Description": {"type": "rich_text", "rich_text": {}},
        "Status": {
            "type": "select",
            "select": {
                "options": [
                    {"name": "To Do"},
                    {"name": "In Progress"},
                    {"name": "Done"},
                ]
            },
        },
    }

    # Create the database
    database = client.databases.create(
        parent={"type": "page_id", "page_id": NOTION_PAGE_ID},
        title=[{"type": "text", "text": {"content": "Default Database"}}],
        properties=properties,
    )

    return database

def write_to_database(
    client, database_id, languages, status, location, company, website, date, position
):
    client.pages.create(
        **{
            "parent": {"database_id": database_id},
            # tell notion exactly where and what type we need to populate
            "properties": {
                "Languages": {"multi_select": [{"name": languages}]},
                "Status": {"status": {"name": status}},
                "Location": {"select": {"name": location}},
                "Company": {
                    "rollup": {"array": [{"title": [{"plain_text": company}]}]}
                },
                "Website": {"rich_text": [{"plain_text": website}]},
                "Date": {"date": {"start": date}},
                "Position": {"title": [{"plain_text": position}]},
            },
        }
    )

def main():
    # 1. Get the data from Notion
    client = Client(auth=NOTION_TOKEN)
    content = read_text(client, NOTION_PAGE_ID)
    write_dict_to_file_json(content, "content.json")
    # db_info = client.databases.retrieve("NOTION_DATABASE_ID")
    # page_response = client.pages.retrieve(NOTION_PAGE_ID)
    # pprint(page_response, indent=2)
    db_rows = client.databases.query(NOTION_DATABASE_ID)
    write_dict_to_file_json(db_rows, 'db_rows.json')
    simplified_rows = get_database(db_rows)
    write_dict_to_file_json(simplified_rows, "rows.json")

    # 2. Get the data from Google Sheets
    data = get_sheet()
    write_dict_to_file_json(data, 'sheet.json')
    print("success !!!!!!!!!!!!!!!!")
    
    # 3. Take that new information and update the sheets database with the new information 
    i=2
    j=-3
    result = compare_rows(simplified_rows[j], data[i])
    if result == 0:
        print("rows are the same")  
    elif result == 1:
        print("rows are same but behind")  
        # take google sheets and overwrite it if notion row is different  
        write_to_sheet(i+3, simplified_rows[j]["date"], data[j]["Type"], simplified_rows[j]["company"], simplified_rows[j]["position"], simplified_rows[j]["status"], simplified_rows[j]["location"], simplified_rows[j]["referral"], simplified_rows[j]["website"])
    else:
        print("rows are different")
    
    
    
    
    # date = "2021-6-29"
    # print(date[-5:]) # ending start, including 5th character
    # print(date[5:]) # ending start, excluding 5th character
    # print(date[:-5]) # beginning start, excluding 5th character
    # print(date[:5]) # beginning start, including 5th character
    # negative version will always be the smaller one
 


if __name__ == "__main__":
    main()
