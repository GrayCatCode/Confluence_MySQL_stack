import html
import json
import os
import requests

# ==== CONFIGURATION ====
CONFLUENCE_BASE_URL = "https://your-confluence-server"
PAT = "your_personal_access_token"
SPACE_KEY = "YOURSPACE"
PAGE_TITLE = "My Uploaded Text File"
TEXT_FILE_PATH = "your_file.txt"  # The file to upload AND attach

# ==== HEADERS ====
HEADERS = {
    "Authorization": f"Bearer {PAT}",
    "Content-Type": "application/json"
}

# ==== CONVERT TEXT TO FORMATTED XHTML ====
def convert_text_to_xhtml(text: str, filename: str) -> str:
    """
    Generates formatted Confluence storage-format XHTML with a heading, text preview,
    and a downloadable attachment link.
    """
    # Short preview only, to avoid long pages
    preview = html.escape("\n".join(text.splitlines()[:20]))

    return f"""
<h1>{filename}</h1>

<p>This file has been uploaded automatically to Confluence. You can download the full version below.</p>

<p><b>Preview:</b></p>

<ac:structured-macro ac:name="code">
  <ac:plain-text-body><![CDATA[{preview}]]></ac:plain-text-body>
</ac:structured-macro>

<p><b>Download:</b> <ac:link><ri:attachment ri:filename="{filename}"/></ac:link></p>
""".strip()

# ==== FIND OR CREATE PAGE ====
def get_page_id_and_version(title: str, space_key: str):
    url = f"{CONFLUENCE_BASE_URL}/rest/api/content"
    params = {
        "title": title,
        "spaceKey": space_key,
        "expand": "version"
    }
    response = requests.get(url, params=params, headers=HEADERS)
    response.raise_for_status()

    results = response.json().get("results", [])

    if results:
        page = results[0]
        return page["id"], page["version"]["number"]

    return None, None

def create_or_update_page(title: str, space_key: str, content: str):
    page_id, version = get_page_id_and_version(title, space_key)

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

    if page_id:

        print(f"Updating page ID {page_id}...")
        body["version"] = {"number": version + 1}
        url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{page_id}"
        response = requests.put(url, headers=HEADERS, data=json.dumps(body))

    else:

        print("Creating new page...")
        url = f"{CONFLUENCE_BASE_URL}/rest/api/content"
        response = requests.post(url, headers=HEADERS, data=json.dumps(body))

    response.raise_for_status()
    return response.json()

# ==== UPLOAD ATTACHMENT ====
def upload_attachment(page_id: str, file_path: str):
    filename = os.path.basename(file_path)
    url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{page_id}/child/attachment"

    headers = { "Authorization": f"Bearer {PAT}" }

    with open(file_path, 'rb') as f:
        files = { 'file': (filename, f), }
        params = { 'minorEdit': 'true' }

        print(f"Uploading attachment: {filename}")
        response = requests.post(url, headers=headers, params=params, files=files)
        response.raise_for_status()
        return response.json()

# ==== MAIN ====
if __name__ == "main":
    try:
        print("Reading file...")
        with open(TEXT_FILE_PATH, 'r', encoding='utf-8') as f:
            text_content = f.read()

        filename = os.path.basename(TEXT_FILE_PATH)
        formatted_xhtml = convert_text_to_xhtml(text_content, filename)

        print("Creating/updating Confluence page...")
        page_info = create_or_update_page(PAGE_TITLE, SPACE_KEY, formatted_xhtml)

        page_id = page_info['id']
        upload_attachment(page_id, TEXT_FILE_PATH)

        print("Success!")
        print(f"View your page at: {CONFLUENCE_BASE_URL}{page_info['_links']['webui']}")

    except Exception as e:
        print(f"Error: {e}")