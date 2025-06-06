from atlassian import Confluence
import json
import os
import re
import requests
import urllib

# Regex pattern to match the Confluence page ID if already in URL:
page_id_in_url_regex_pattern = re.compile(r"\?pageId=(\d+)")

#================================================================================================
# Function that extracts the ID of the Confluence page specified in the `page_url`:
#================================================================================================
def get_page_id_from_url(confluence, url):
    """ Extracts the page ID from the given URL or retrieves it using the Confluence API. """
    page_url = urllib.parse.unquote(url) #unquoting url to deal with special characters like '%'
    space, page_title = page_url.split("/")[-2:]

    # If there's a page ID found in the response URL, parse the URL and return it:
    if re.search(page_id_in_url_regex_pattern, page_title):
        return_str = "The ID of the page is: " + re.search(page_id_in_url_regex_pattern, page_title).group(1)
        return return_str
    
    # No page ID was found in the response URL:
    else:
        page_title = page_title.replace("+", " ")
        return_str = "The ID the page at \"" + str(page_title) + "\" is: " + confluence.get_page_id(space, page_title)
        return return_str

#================================================================================================
# Function that reads the content of an unstructured text file:
#================================================================================================
def read_text_file(file_path):
    """Reads the content of an unstructured text file in its entirety."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.readlines()

#================================================================================================
# Function that reads the content of an unstructured text file:
#================================================================================================
def read_text_file_by_line(file_path):
    """Reads the content of an unstructured text file line-by-line."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with open(file_path, 'r', encoding='utf-8') as file:
#       return file.readlines()

        # Initialize the string used for the page HTML:
        file_content = ''

        # Read the first line of the file:
        line = file.readline()

        # Loop through all the rest of the lines in the file:
        while line:

            # Add the last line read to the string:
            file_content += line
            # Read the next line of the file:
            line = file.readline()

        # After the entire file is read into a string, close the file:
        file.close()

        # Search the string for carriage returns and replace them with HTML line breaks:
        file_content = re.sub('\n', '<br>', file_content)            

        # Return the read file as a continuous string:
        return file_content

#================================================================================================
# Method which takes text content and applies format for Confluence's `storage` format:
#================================================================================================
def format_for_confluence(content):
    """
    Formats the content into Confluence Storage Format.
    Assumes sections are separated by blank lines.
    """
    confluence_content = "<ac:structured-macro ac:name=\"section\">\n"
    for line in content:
        line = line.strip()
        if not line:
            # Close the current section and start a new one
            confluence_content += "</ac:structured-macro>\n<ac:structured-macro ac:name=\"section\">\n"
        else:
            # Wrap each line in a paragraph tag
            confluence_content += f"<p>{line}</p>\n"
    confluence_content += "</ac:structured-macro>"  # Close the last section
    return confluence_content

#================================================================================================
# Method which writes formatted output to a file on the local filesystem:
#================================================================================================
def save_to_file(output_path, content):
    """ Saves the formatted content to a file designated by the output path. """
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(content)
        print(f"Content saved to {output_path} ...")

#================================================================================================
# Method which wraps text in the appropriate tags for Confluence XHTML `storage` format:
#================================================================================================
def wrap_in_confluence_format(text):
    # Wrap in <pre> tags to preserve formatting (like code block):
    return f"<ac:structured-macro ac:name='code'><ac:plain-text-body><![CDATA[{text}]]></ac:plain-text-body></ac:structured-macro>"

#================================================================================================
# Main method:
#================================================================================================
def main():
    """ Main method to execute the script. """
#   from getpass import getpass
#   user = input('Login: ')
#   pwd = getpass('Password: ')
    user = 'testuser'
    pwd = 'testuser'

#   Define the URL of the page that we're trying to get the ID for:
#   page_url = "https://confluence.som.yale.edu/display/SC/Finding+the+Page+ID+of+a+Confluence+Page"
    page_url = "http://localhost:8090/display/TUS/Test+User+Page+1"

   # Get the base Confluence URL and login credentials:
    confluence = Confluence(
#           url='https://confluence.som.yale.edu/',
            url='http://localhost:8090/',
            username=user,
            password=pwd)

    # Print either the Confluence page ID or the space code and page_title of the page:
    print(get_page_id_from_url(confluence, page_url))

    #------------------------------------------------------------------------
    # Write a new page to Confluence with the existing page ID as the parent:
    #------------------------------------------------------------------------

    # Set the title and content of the page to create
    page_title = 'My New HTML Page'
#   page_html = '<p>This page was created by Andrew Poloni with Python v3.13.3.</p>'
#   page_html = read_text_file_by_line('/Users/andrewpoloni/Git_repos/Confluence_MySQL_stack/python/lorem_ipsum_html_cropped.html')
#   page_html = read_text_file('/Users/andrewpoloni/Git_repos/Confluence_MySQL_stack/python/Lorem_ipsum_formatted_for_confluence.xml')
    page_html = read_text_file('/Users/andrewpoloni/Git_repos/Confluence_MySQL_stack/python/Lorem_ipsum.txt')
#   formatted_page_html = wrap_in_confluence_format(page_html)
    formatted_page_html = format_for_confluence(page_html)
    save_to_file('/Users/andrewpoloni/Git_repos/Confluence_MySQL_stack/python/Lorem_ipsum_formatted_for_confluence.xhtml', formatted_page_html)

    #parent_page_id = {Parent Page ID}
    parent_page_id = 98383

    #space_key = '{SPACE KEY}'
    space_key = 'TUS'

    # get the confluence home page url for your organization {confluence_home_page}
    #url = '{confluence_home_page}/rest/api/content/'
    url = 'http://localhost:8090/rest/api/content/'

    # Request Headers
    request_headers = { 'Content-Type': 'application/json;charset=iso-8859-1', }

    # Request body
    upload_data = {
        'type': 'page',
        'title': page_title,
        'ancestors': [{'id':parent_page_id}],
        'space': {'key':space_key},
        'body':
        {
            'storage':
            {
                'value': formatted_page_html,
                'representation': 'storage',
            }
        }
    }

    # We're ready to call the API:
    print("Attempt to call the Confluence API and write a new page ...")

    try:

        # Set the request headers with the username and password of the user
        # who has permissions to write the page to the target space in Confluence:
        #basic_auth = HTTPBasicAuth('{email you use to log in}', auth_token)
        basic_auth = requests.auth.HTTPBasicAuth(user, pwd)

        # Send the request to the target Confluence instance via HTTP POST:
#       response = requests.post(url=url, data=json.dumps(data), headers=headers, auth=basic_auth)
        response = requests.post(url=url, data=json.dumps(upload_data), headers=request_headers, auth=basic_auth)

        # Check the response received back from Confluence;
        # consider any HTTP status code other than 2xx an error:
        if not response.status_code // 100 == 2:
            print("Error: Unexpected response {}".format(response))
        else:
            print('The page was created in Confluence!')

    except requests.exceptions.RequestException as e:

        # A serious problem happened, like an SSLError or InvalidURL
        print("An exception was thrown: {}".format(e))

#================================================================================================
# Main method hook:
#================================================================================================
if __name__ == "__main__":
    main()