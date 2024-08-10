import pickle
import os.path
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# we want a client library (100% test coverage)
from notion_client import Client
from pprint import pprint

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# how notion knows you are a valid user (now you officially validate your notion api)
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
RANGE_NAME = os.getenv('RANGE_NAME') 
NOTION_TOKEN = os.getenv('NOTION_TOKEN')  
NOTION_PAGE_ID = os.getenv('NOTION_PAGE_ID')

# Function to get the data from google sheets
def get_sheet():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
        return None
    else:
        print('%s rows found.' % len(values))
        return values

# Function to create a paragraph block for each string in the array
def write_p_block(text):
    return {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": text
                            }
                        }
                    ]
                   
                }
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
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": text
                            }
                        }
                    ]
                   
                }
            }
        ]
    )

def main():
    data = get_sheet()
    print('success !!!!!!!!!!!!!!!!')
    headers = " ".join(data[0])
    print(headers)
    
    client = Client(auth=NOTION_TOKEN)
    
    write_text(client, NOTION_PAGE_ID, headers)
    
    # gets the main information about the page you are working on 
    # page_response = client.pages.retrieve(NOTION_PAGE_ID)
    # pprint(page_response, indent=2)
    
if __name__ == '__main__':
    main()