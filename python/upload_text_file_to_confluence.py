import argparse
from   atlassian import Confluence
from   datetime  import date
from   datetime  import datetime
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

# ==== GET THE parent PAGE ID (VERIFY PAGE EXISTS) ====
def get_parent_page_id(base_url: str, pat: str, title: str, space_key: str):
    """
    Checks if a Confluence page with the given title and space key exists.
    If it does not exist, raises an exception.

    base_url:  The base URL of the Confluence server.
    pat:       Personal Access Token for authentication.
    title:     The title of the Confluence page.
    space_key: The space key where the page should exist.

    Raises an exception if the page does not exist.
    """

    # Set the URL for the Confluence API to search for the page:
    url = f"{base_url}/rest/api/content"

    # Set the parameters for the GET request:
    params = {
        "title": title,
        "spaceKey": space_key
    }

    # Create the headers for the request to include the personal access token for authentication:
    headers_with_pat = {
        "Authorization": f"Bearer {pat}",
        "Content-Type": "application/json"
    }

    # Make the GET request to Confluence to try to find the page we're looking for:
    response = requests.get(url, params=params, headers=headers_with_pat)

    # Check if the request was successful:
    response.raise_for_status()

    # Parse the JSON response:
    results = response.json().get("results", [])

    # If the page does not exist, raise an exception:
    if not results:

        raise Exception(f"The specified parent page '{title}' does not exist in space '{space_key}'.")

    else:

        print(f"The specified parent page '{title}' exists in space '{space_key}'.")

        # Return the ID of the parent page:
        return results[0]["id"]

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
def create_or_update_page(confluence: Confluence, pat: str, parent_page_id: str, title: str, space_key: str, content: str):
    """
    Creates or updates a Confluence page with the given title and content.
    If a page with the same title exists, it will be updated. Otherwise, a new page will be created.

    confluence_obj:  The Confluence object to interact with the Confluence API.
    pat:             Personal Access Token for authentication.
    title:           The title of the Confluence page.
    space_key:       The space key where the page will be created/updated.
    content:         The content to be added to the page in XHTML format.

    Returns the response from the Confluence API.

    If the page is created, it returns the new page ID.
    If the page is updated, it returns the updated page ID.

    Raises an exception if the request fails.
    """

    # Check if the page already exists:
    # If it does, get the page ID and version number;
    # If it doesn't, create a new page.
#   page_id, version = get_page_id_and_version(base_url, pat, title, space_key)

    # Prepare the request body for creating or updating the page:
    body = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "ancestors": [{"id": parent_page_id}],
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

    username = "test-user1"
    password = "P@$$w0rd"
    pw_auth = (username, password)

    print("- Creating new page...")

    post_data = json.dumps(body)

    # Make the POST request to create the page:
#   response = requests.post(url, headers=headers_with_pat, data=post_data)
#   response = requests.post(url, auth=pw_auth, data=post_data)

    confluence.update_or_create_page(space_key=space_key, title=title, body=content, parent_id=parent_page_id)

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

        print(f"- Uploading attachment: {filename}")

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
    # - Confluence space key
    # - Confluence parent page title
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

    # Positional argument for the parent page title:
    parser.add_argument("--parent_page_title",
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
        # Creata a Confluence object to interact with the Confluence API:
        print("========================================================================")
        print("- Using Confluence base URL: " + args.confluence_base_url)
        print("------------------------------------------------------------------------")

        aether_confluence_instance = Confluence(
            url=args.confluence_base_url,
            token=args.personal_access_token)

        # Check for the specified parent page and verify that it exists; if it doesn't,
        # we're not going to be able to create a chile page under it with the uploaded text file.
#       parent_page_id = get_parent_page_id(args.confluence_base_url, args.personal_access_token, args.parent_page_title, args.space_key)

        parent_page_id = aether_confluence_instance.get_page_by_title(
            space=args.space_key,
            title=args.parent_page_title)

        if not parent_page_id:

            # If the parent page ID is not found, raise an exception and quit:
            raise Exception(f"The specified parent page '{args.parent_page_title}' does not exist in space '{args.space_key}'.")

        else:
            print(f"- Confluence page found; parent page ID is '{parent_page_id['id']}'.")
            print("------------------------------------------------------------------------")

        # Print the text file to be uploaded:
        if not os.path.isfile(args.text_file):

            # If the text file does not exist, raise an exception and quit:
            raise Exception(f"- The specified text file to be uploaded '{args.text_file}' does not exist.")
            print("========================================================================")

        elif not os.access(args.text_file, os.R_OK):

            # If the text file is not readable, raise an exception and quit:
            raise Exception(f"- The specified text file to be uploaded '{args.text_file}' is not readable.")
            print("========================================================================")

        elif not os.path.getsize(args.text_file):

            # If the text file is empty, raise an exception and quit:
            raise Exception(f"- The specified text file to be uploaded '{args.text_file}' is empty.")
            print("========================================================================")

        else:
            print(f"- Reading upload file: ")
            print(f"- {args.text_file}")
            print("------------------------------------------------------------------------")

        # Read the text file to be written to Confluence:
        with open(args.text_file, 'r', encoding='utf-8') as f:
            text_content = f.read()

        filename = os.path.basename(args.text_file)

        # Convert the text file content to XHTML:
        formatted_xhtml = convert_text_to_xhtml(text_content, filename)

        # Get the current date to use to create the Confluence page title:
        today = date.today()
        day = today.day
        month_name = today.strftime("%b")
        year = today.year

        # Get the current time to use to create the Confluence page title:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S %p")

#       print("Today's date is: " + str(day) + " " + str(month_name) + " " + str(year))
#       print("Current time is: " + str(current_time))

        upload_page_title= f"{day} {month_name} {year} {current_time}"

        print(f"- Creating/updating Confluence page \"{upload_page_title}\" ...")
        print(f"- under parent page ID {parent_page_id['id']}, ...")
        print(f"- title \"{parent_page_id['title']}\", ...")
        print(f"- in space: {args.space_key}")
        print("------------------------------------------------------------------------")

        # Create or update the Confluence page with the formatted XHTML:
        aether_confluence_instance.update_or_create(
            parent_id=parent_page_id['id'],
            title=upload_page_title,
            body=formatted_xhtml,
            representation="storage",
            full_width=False)

#       page_id = page_info['id']

        upload_page_id = aether_confluence_instance.get_page_by_title(
            space=args.space_key,
            title=upload_page_title)

        print("Attaching file to the page...")

        # Upload the file as an attachment to the same Confluence page:
#       upload_attachment(args.confluence_base_url, args.personal_access_token, page_id, args.text_file)
        aether_confluence_instance.attach_file(
            page_id=upload_page_id['id'],
            filename=args.text_file,
            name=filename,
            title=filename,
            space=args.space_key,
            comment="Uploaded via cron job script.")

        upload_page_properties = aether_confluence_instance.get_page_by_id(page_id=upload_page_id['id'])

        # Print the URL where the page can be viewed:
        print("------------------------------------------------------------------------")
        print(f"- Success!  View the page at: ")
        print(f"- {args.confluence_base_url}{upload_page_properties['_links']['webui']}")
        print("========================================================================")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
   main()