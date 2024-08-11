import pickle
import os.path
import requests
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# we want a client library (100% test coverage)
from notion_client import Client
import json
from pprint import pprint

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# how notion knows you are a valid user (now you officially validate your notion api)
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
RANGE_NAME = os.getenv("RANGE_NAME")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")


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
        return values


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
    # return response['results'][0]['paragraph']['text'][0]['text']['content']
    return response["results"]

def read_database(client, database_id):
    dbs = []
    response = client.databases.retrieve(database_id)
    
    block_id = response["id"]
    title = response["title"]
    db_title = title[0]["plain_text"]
    block_description = response["description"]
    properties = response["properties"]
    print('3')
    print(properties)
    print('4')
    
    for row in properties:
        if not properties:
            return
        
        r = {
            "title": db_title,
            "name": row[0],
        }
        dbs.append(r)
    return dbs

def safe_get(data, dot_chained_keys):
    '''
        {'a': {'b': [{'c': 1}]}}
        safe_get(data, 'a.b.0.c') -> 1
    '''
    keys = dot_chained_keys.split('.')
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
        languages = safe_get(row, 'properties.Languages.multi_select.0.name') 
        interview_stage = safe_get(row, 'properties.Status.status.name') 
        location = safe_get(row, 'properties.Location.select.name')
        company = safe_get(row, 'properties.Name.rollup.array.0.title.0.plain_text')
        website = safe_get(row, 'properties.Website.rich_text.0.plain_text')
        date = safe_get(row, 'properties.Date.date.start')
        position = safe_get(row, 'properties.Position.title.0.plain_text')
        
        if not position:
            continue
        
        rows.append({
            "languages": languages,
            "interview_stage": interview_stage,
            "location": location,
            "company": company,
            "website": website,
            "date": date,
            "position": position
        })
        
    write_dict_to_file_json(rows, 'rows.json')
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


def main():
    client = Client(auth=NOTION_TOKEN)
    content = read_text(client, NOTION_PAGE_ID)
    write_dict_to_file_json(content, 'content.json')

    data = get_sheet()
    # print("success !!!!!!!!!!!!!!!!")
    
    db_info = client.databases.retrieve("d671d978-b0cd-4f82-9d54-d6e6960cc3ae")
    write_dict_to_file_json(db_info, 'db_info.json')
    db_rows = client.databases.query("d671d978-b0cd-4f82-9d54-d6e6960cc3ae")
    write_dict_to_file_json(db_rows, 'db_rows.json')
    
    # Languages, Interview Stage, Location, Company, Website, Date, Position
    db = get_database(client, db_rows)
    
    # Date, Type, Company, Position, Status, Location, Referral?, Website 
    print(data)
    
    # TODO now that you have information from both sides, you need to make it so that you can update the notion database with the google sheets information
    # based on when the user puts a new row in the google sheets
    
    # 1. Trigger function when user updates a row on their google sheets
    # 2. Take that new information and update the notion database with the new information
      
    # page_response = client.pages.retrieve(NOTION_PAGE_ID)
    # pprint(page_response, indent=2)


if __name__ == "__main__":
    main()
