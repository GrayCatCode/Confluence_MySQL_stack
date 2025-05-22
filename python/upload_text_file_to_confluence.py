import argparse
from   datetime import date
import json
import os
import requests

# ==== CONVERT UPLOAD TEXT TO FORMATTED XHTML ====
def convert_text_to_xhtml(text: str, filename: str) -> str:
    """
    Generates formatted Confluence storage-format XHTML with a heading, text preview,
    and a downloadable attachment link.
    """
    # Short preview only, to avoid long pages in the browser:
    # You would replace `text` in the f-string below with `preview` if you want to show the preview instead.
#   preview = html.escape("\n".join(text.splitlines()[:20]))

    return f"""
<h1>{filename}</h1>

<p>This file has been uploaded automatically to Confluence. You can download the full version below.</p>

<p><b>Preview:</b></p>

<ac:structured-macro ac:name="code">
  <ac:plain-text-body><![CDATA[{text}]]></ac:plain-text-body>
</ac:structured-macro>

<p><b>Download:</b> <ac:link><ri:attachment ri:filename="{filename}"/></ac:link></p>
""".strip()

# ==== FIND OR CREATE CONFLUENCE PAGE ====
def get_page_id_and_version(base_url: str, pat: str, title: str, space_key: str):
    """
    Retrieves the Confluence page ID and version number for a given title and space key.
    If the page does not exist, it returns None.

    base_url:  The base URL of the Confluence server.
    pat:       Personal Access Token for authentication.
    title:     The title of the Confluence page.
    space_key: The space key where the page will be created/updated.

    Returns the page ID and version number if the page exists, otherwise returns None.

    Raises an exception if the request fails.
    """

    # Set the URL for the Confluence API to search for the page:
    url = f"{base_url}/rest/api/content"

    # Set the parameters for the GET request:
    params = {
        "title": title,
        "spaceKey": space_key,
        "expand": "version"
    }

    # Create the headers for the request to include the personal access token for authentication:
    headers_with_pat = {
        "Authorization": f"Bearer {pat}",
        "Content-Type": "application/json"
    } 

    # Make the GET request to Confluence to find the page we're looking for:
    response = requests.get(url, params=params, headers=headers_with_pat)
    response.raise_for_status()

    # Parse the JSON response:
    results = response.json().get("results", [])

    # If the page exists, return its ID and version number:
    if results:
        page = results[0]
        return page["id"], page["version"]["number"]

    return None, None

# ==== CREATE OR UPDATE CONFLUENCE PAGE ====
def create_or_update_page(base_url: str, pat: str, title: str, space_key: str, content: str):
    """
    Creates or updates a Confluence page with the given title and content.
    If a page with the same title exists, it will be updated. Otherwise, a new page will be created.

    base_url:  The base URL of the Confluence server.
    pat:       Personal Access Token for authentication.
    title:     The title of the Confluence page.
    space_key: The space key where the page will be created/updated.
    content:   The content to be added to the page in XHTML format.

    Returns the response from the Confluence API.

    If the page is created, it returns the new page ID.
    If the page is updated, it returns the updated page ID.

    Raises an exception if the request fails.
    """

    # Check if the page already exists:
    # If it does, get the page ID and version number;
    # If it doesn't, create a new page.
    page_id, version = get_page_id_and_version(base_url, pat, title, space_key)

    # Prepare the request body for creating or updating the page:
    body = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": {
            "storage": {
                "value": content,
                "representation": "storage"
            }
        }
    }

    # Creaqte the headers for the request to include the personal access token for authentication:
    headers_with_pat = {
         "Authorization": f"Bearer {pat}",
         "Content-Type": "application/json"
     }

    # If the page exists in Confluence, update it:
    if page_id:

        print(f"Updating page ID {page_id} ...")

        # Update the version number in the request body:
        body["version"] = {"number": version + 1}

        # Set the page ID in the URL:
        url = f"{base_url}/rest/api/content/{page_id}"

        # Make the PUT request to update the page:
        response = requests.put(url, headers=headers_with_pat, data=json.dumps(body))

    else: # The page does not exist, so create a new one:

        print("Creating new page...")

        # Set the URL for creating a new page:
        url = f"{base_url}/rest/api/content"

        # Make the POST request to create the page:
        response = requests.post(url, headers=headers_with_pat, data=json.dumps(body))

    # Check if the request was successful:
    response.raise_for_status()

    # Parse the JSON response and return it:
    return response.json()

# ==== UPLOAD ATTACHMENT TO CONFLUENCE PAGE ====
def upload_attachment(base_url: str, pat: str, page_id: str, file_path: str):
    """
    Uploads a file attachment to a Confluence page.

    base_url:  The base URL of the Confluence server.
    pat:       Personal Access Token for authentication.
    page_id:   The ID of the Confluence page to which the attachment will be uploaded.
    file_path: The full path to the file to be uploaded.

    Returns the response from the Confluence API.

    Raises an exception if the request fails.
    """

    # Separate the file name from the full file path:
    filename = os.path.basename(file_path)

    # Set the URL for the Confluence API to upload the attachment to include the page ID:
    attachment_url = f"{base_url}/rest/api/content/{page_id}/child/attachment"

    # Create the headers for the request to include the personal access token for authentication:
    headers_with_pat = {
         "X-Atlassian-Token": "no-check",
         "Authorization": f"Bearer {pat}",
     }

    # Open the target file in binary mode:
    with open(file_path, 'rb') as file_data:

        # Prepare the file data for the request:
        upload_file = { "file": (filename, file_data, "application/octet-stream") }

        print(f"Uploading attachment: {filename}")

        # Make the POST request to upload the attachment:
        response = requests.post(attachment_url, headers=headers_with_pat, files=upload_file)

        # Check if the request was successful:
        response.raise_for_status()

        # Parse the JSON response and return it:
        return response.json()

#================================================================================================
# Main method:
#================================================================================================
def main():
# ==== MAIN ====

    # Create the argument parser:
    # This will allow the user to specify the parameters required to upload a text file to Confluence.
    #
    # The parameters include:
    #
    # - Confluence base URL
    # - personal access token for authentication
    # - Confluence space key,
    # - Confluence page title
    # - path to the text file to be uploaded
    #
    parser = argparse.ArgumentParser(description="Parameters required to upload a text file to Confluence.")

    # Positional argument for the Confluence base URL:
    parser.add_argument("--confluence_base_url",
                        "-u",
                        required=True,
                        help="The base URL of the Confluence server (http(s)://hostname:port_no).")

    # Positional argument for the personal access token:
    parser.add_argument("--personal_access_token",
                        "-p",
                        required=True,
                        help="User personal access token for Confluence.")

    # Positional argument for the space key:
    parser.add_argument("--space_key",
                        "-k",
                        required=True,
                        help="The Confluence space key where the page will be created/updated.")

    # Positional argument for the page title:
    parser.add_argument("--page_title",
                        "-t",
                        required=True,
                        help="The title of the Confluence page to create/update.")

    # Positional argument for the text file path:
    parser.add_argument("--text_file",
                        "-f",
                        required=True,
                        help="Full path to the text file to upload to Confluence.")

    # Parse the command-line arguments:
    args = parser.parse_args()

    # Do the magic:
    # Read the text file, convert it to XHTML, and create/update the Confluence page.
    try:
        print("Reading file: " + args.text_file)

        # Read the text file to be written to Confluence:
        with open(args.text_file, 'r', encoding='utf-8') as f:
            text_content = f.read()

        filename = os.path.basename(args.text_file)

        # Convert the text file content to XHTML:
        formatted_xhtml = convert_text_to_xhtml(text_content, filename)

        print("Creating/updating Confluence page...")

        # Get the current date to use to create the Confluence page title:
        today = date.today()
        day = today.day
        month = today.month
        month_name = today.strftime("%b")
        year = today.year

        print("Today's date is: " + str(day) + " " + str(month_name) + " " + str(year))
        
        # Create or update the Confluence page with the formatted XHTML:
        page_info = create_or_update_page(args.confluence_base_url, args.personal_access_token, args.page_title, args.space_key, formatted_xhtml)

        page_id = page_info['id']

        # Upload the file as an attachment to the same Confluence page:
        upload_attachment(args.confluence_base_url, args.personal_access_token, page_id, args.text_file)

        # Print the URL where the page can be viewed:
        print("Success!")
        print(f"View your page at: {args.confluence_base_url}{page_info['_links']['webui']}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
   main()