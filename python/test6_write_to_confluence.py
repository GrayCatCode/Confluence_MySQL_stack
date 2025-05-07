import html
import json
import requests

# ==== CONFIGURATION ====
# CONFLUENCE_BASE_URL = "https://your-confluence-server"  # No /wiki or /rest
# SPACE_KEY = "YOURSPACE"
# PAGE_TITLE = "My Uploaded Text File"
# TEXT_FILE_PATH = "your_file.txt"
# PAT = "your_personal_access_token"  # Personal Access Token for Confluence Server

CONFLUENCE_BASE_URL = "http://localhost:8090"  # No /wiki or /rest
SPACE_KEY = "TUS"
PAGE_TITLE = "Test User Page 1"
TEXT_FILE_PATH = "/Users/andrewpoloni/Git_repos/Confluence_MySQL_stack/python/Lorem_ipsum.txt"
PAT = "MjA1ODczMzA4OTA2OhMelDOf91qGExdua3d2rqZk/b+5"

# ==== FUNCTIONS ====
def read_and_convert_to_storage_format(path: str) -> str:
   """
   Reads a plain-text file and converts it to Confluence storage format XHTML
   wrapped in a code macro to preserve formatting.
   """
   with open(path, 'r', encoding='utf-8') as f:
      raw_text = f.read()

   escaped = html.escape(raw_text)

   xhtml = f"""
<ac:structured-macro ac:name="code">
<ac:plain-text-body><![CDATA[{escaped}]]></ac:plain-text-body>
</ac:structured-macro>
""".strip()

   return xhtml

def get_page_id_and_version(title: str, space_key: str, headers: dict):
   url = f"{CONFLUENCE_BASE_URL}/rest/api/content"
   params = {
      "title": title,
      "spaceKey": space_key,
      "expand": "version"
   }
   response = requests.get(url, params=params, headers=headers)
   response.raise_for_status()

   results = response.json().get("results", [])

   if results:
      page = results[0]
      return page["id"], page["version"]["number"]

   return None, None

def create_or_update_confluence_page(title: str, space_key: str, content: str, headers: dict):
   page_id, version = get_page_id_and_version(title, space_key, headers)

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

      print(f"Updating existing page (ID: {page_id})...")
      body["version"] = {"number": version + 1}
      url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{page_id}"
      response = requests.put(url, headers=headers, data=json.dumps(body))

   else:

      print("Creating a new page...")
      url = f"{CONFLUENCE_BASE_URL}/rest/api/content/"
      response = requests.post(url, headers=headers, data=json.dumps(body))

   response.raise_for_status()
   print("Page successfully published.")

   return response.json()

#================================================================================================
# Main method:
#================================================================================================
def main():

   try:

      print("Converting text file...")
      storage_format_content = read_and_convert_to_storage_format(TEXT_FILE_PATH)

      headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {PAT}"
      }

      print("Uploading to Confluence Server...")
      result = create_or_update_confluence_page(PAGE_TITLE, SPACE_KEY, storage_format_content, headers)

      print("Done! View your page at:")
      print(f"{CONFLUENCE_BASE_URL}{result['_links']['webui']}")

   except Exception as e:

      print(f"Error: {e}")

if __name__ == "__main__":
   main()
