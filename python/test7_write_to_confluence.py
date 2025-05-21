import argparse
import html
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

    base_url: The base URL of the Confluence server.
    pat: Personal Access Token for authentication.
    title: The title of the Confluence page.
    space_key: The space key where the page will be created/updated.

    Returns the page ID and version number if the page exists, otherwise returns None.

    Raises an exception if the request fails.
    """

    url = f"{base_url}/rest/api/content"

    params = {
        "title": title,
        "spaceKey": space_key,
        "expand": "version"
    }

    headers_with_pat = {
        "Authorization": f"Bearer {pat}",
        "Content-Type": "application/json"
    } 

    response = requests.get(url, params=params, headers=headers_with_pat)
    response.raise_for_status()

    results = response.json().get("results", [])

    if results:
        page = results[0]
        return page["id"], page["version"]["number"]

    return None, None

# ==== CREATE OR UPDATE CONFLUENCE PAGE ====
def create_or_update_page(base_url: str, pat: str, title: str, space_key: str, content: str):
    """
    Creates or updates a Confluence page with the given title and content.
    If a page with the same title exists, it will be updated. Otherwise, a new page will be created.

    base_url: The base URL of the Confluence server.
    pat: Personal Access Token for authentication.
    title: The title of the Confluence page.
    space_key: The space key where the page will be created/updated.
    content: The content to be added to the page in XHTML format.

    Returns the response from the Confluence API.

    If the page is created, it returns the new page ID.
    If the page is updated, it returns the updated page ID.

    Raises an exception if the request fails.
    """

    # Check if the page already exists:
    # If it does, get the page ID and version number;
    # If it doesn't, create a new page.
    page_id, version = get_page_id_and_version(base_url, pat, title, space_key)

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

    headers_with_pat = {
         "Authorization": f"Bearer {pat}",
         "Content-Type": "application/json"
     }

    if page_id:

        print(f"Updating page ID {page_id}...")
        body["version"] = {"number": version + 1}
        url = f"{base_url}/rest/api/content/{page_id}"
        response = requests.put(url, headers=headers_with_pat, data=json.dumps(body))

    else:

        print("Creating new page...")
        url = f"{base_url}/rest/api/content"
        response = requests.post(url, headers=headers_with_pat, data=json.dumps(body))

    response.raise_for_status()
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

    filename = os.path.basename(file_path)

    attachment_url = f"{base_url}/rest/api/content/{page_id}/child/attachment"

    headers_with_pat = {
         "X-Atlassian-Token": "no-check",
         "Authorization": f"Bearer {pat}",
     }

    with open(file_path, 'rb') as file_data:

        upload_file = { "file": (filename, file_data, "application/octet-stream") }

        print(f"Uploading attachment: {filename}")

        response = requests.post(attachment_url, headers=headers_with_pat, files=upload_file)
        response.raise_for_status()
        return response.json()

#================================================================================================
# Main method:
#================================================================================================
def main():
# ==== MAIN ====

    # Create the argument parser:
    # This will allow the user to specify the parameters required to upload a text file to Confluence.
    # The parameters include the Confluence base URL, personal access token, space key,
    # page title, and the text file path.
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
                        help="The space key where the page will be created/updated.")

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

        # Create or update the Confluence page with the formatted XHTML:
        page_info = create_or_update_page(args.confluence_base_url, args.personal_access_token, args.page_title, args.space_key, formatted_xhtml)

        page_id = page_info['id']

        # Upload the file as an attachment to the same Confluence page:
        upload_attachment(args.confluence_base_url, args.personal_access_token, page_id, args.text_file)

        print("Success!")
        print(f"View your page at: {args.confluence_base_url}{page_info['_links']['webui']}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
   main()