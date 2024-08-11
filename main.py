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

    if not values:
        print("No data found.")
        return None
    else:
        print("%s rows found." % len(values))

# Function to write data to google sheets
def write_to_sheet(date, type, company, position, status, location, referral, website):
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
    formatted_date = date[-5:]
    
    # status
    if status == 'Applied':
        formatted_stat = 'Applied'
    elif status == 'Coding Test':
        formatted_stat = 'Coding Challenge'
    elif status == 'Declined':
        formatted_stat = 'Rejected'
    elif status == 'Not Applied':
        formatted_stat = 'Need to Apply'
    elif status == 'Waitlisted':
        formatted_stat = 'Waitlisted'
    else:
        formatted_stat = 'Interview'
        

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


def find_empty_row(values):
    count = 0
    for i, element in enumerate(values):
        print(f"Index: {i}, Element: {element}, Current Count: {count}")
        if not element:
            count += 1
            if count == 8:
                print(f"Found 8 consecutive empty elements starting at index {i - 7}")
                return i - 7
        else:
            count = 0


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


def get_database(client, content):
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

    write_dict_to_file_json(rows, "rows.json")
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
    client = Client(auth=NOTION_TOKEN)
    content = read_text(client, NOTION_PAGE_ID)
    write_dict_to_file_json(content, "content.json")

    data = get_sheet()
    write_dict_to_file_json(data, 'sheet.json')
    print("success !!!!!!!!!!!!!!!!")
    #row_index = find_empty_row(data)
    #print(row_index)

    # db_info = client.databases.retrieve("d671d978-b0cd-4f82-9d54-d6e6960cc3ae")
    db_rows = client.databases.query(NOTION_DATABASE_ID)
    write_dict_to_file_json(db_rows, 'db_rows.json')

    # Languages, Stage, Location, Company, Website, Date, Position
    db = get_database(client, db_rows)
    last_row = db[10]
    status = last_row["status"]
    location = last_row["location"]
    company = last_row["company"]
    website = last_row["website"]
    date = last_row["date"]
    position = last_row["position"]
    referral = last_row["referral"]

    # print(languages, status, location, company, website, date, position)
    write_to_sheet(date, row["type"], company, position, status, location, referral, website)

    # Date, Type, Company, Position, Status, Location, Referral?, Website
    # sht = write_to_database(client, "d671d978-b0cd-4f82-9d54-d6e6960cc3ae", "Python", "Not Applied", "Remote", "Google", "https://www.google.com", "2021-09-01", "Software Engineer")
    # print("success !!!!!!!!!!!!!!!!")

    # TODO now that you have information from both sides, you need to make it so that you can update the notion database with the google sheets information
    # based on when the user puts a new row in the google sheets

    # 1. Test writing on both notion and sheets again (notion dosen't allow using rollover on databases so its sheets for now)
    # 2. Trigger function when user updates a row on their google sheets (now notion)
    # 3. Take that new information and update the notion database with the new information (now sheets)

    # page_response = client.pages.retrieve(NOTION_PAGE_ID)
    # pprint(page_response, indent=2)


if __name__ == "__main__":
    main()
