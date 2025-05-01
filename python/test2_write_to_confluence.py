import requests

# Confluence API endpoint and credentials
CONFLUENCE_URL = "http://localhost:8090/rest/api"
CONFLUENCE_USERNAME = "testuser"
CONFLUENCE_PASSWORD = "testuser"

# ID of the page to update
PAGE_ID = 98379

# New content for the page
NEW_CONTENT = """
<p>This is the updated content for the page.</p>
"""

# Headers for the API request
headers = {
    "Content-Type": "application/json"
}

# Data to send in the API request
data = {
    "id": PAGE_ID,
    "type": "page",
    "title": "My Page",
    "body": {
        "storage": {
            "value": NEW_CONTENT,
            "representation": "storage"
        }
    }
}

# Make the API request to update the page
response = requests.put(
    f"{CONFLUENCE_URL}/content/{PAGE_ID}",
    auth=(CONFLUENCE_USERNAME, CONFLUENCE_PASSWORD),
    headers=headers,
    json=data
)

# Check the response status code
if response.status_code == 200:
    print("Page updated successfully!")
else:
    print(f"Error updating page: {response.text}")

