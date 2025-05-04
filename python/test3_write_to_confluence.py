import requests.auth
from atlassian import Confluence
import json
import re
import requests
import urllib

# Regex pattern to match the page ID if already in URL:
page_id_in_url_regex_pattern = re.compile(r"\?pageId=(\d+)")

# Function that extracts the ID of the Confluence page specified in the `page_url`:
def get_page_id_from_url(confluence, url):
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

# Main method:
if __name__ == "__main__":
    from getpass import getpass
    user = input('Login: ')
    pwd = getpass('Password: ')

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
    page_title = 'My New Page'
    page_html = '<p>This page was created by Andrew Poloni with Python v3.13.3.</p>'

    #parent_page_id = {Parent Page ID}
    parent_page_id = 98383

    #space_key = '{SPACE KEY}'
    space_key = 'TUS'

    # get the confluence home page url for your organization {confluence_home_page}
    #url = '{confluence_home_page}/rest/api/content/'
    url = 'http://localhost:8090/rest/api/content/'

    # Request Headers
    headers = { 'Content-Type': 'application/json;charset=iso-8859-1', }

    # Request body
    data = {
        'type': 'page',
        'title': page_title,
        'ancestors': [{'id':parent_page_id}],
        'space': {'key':space_key},
        'body':
        {
            'storage':
            {
                'value': page_html,
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
        response = requests.post(url=url, data=json.dumps(data), headers=headers, auth=basic_auth)

        # Check the response received back from Confluence;
        # consider any HTTP status code other than 2xx an error:
        if not response.status_code // 100 == 2:
            print("Error: Unexpected response {}".format(response))
        else:
            print('The page was created in Confluence!')

    except requests.exceptions.RequestException as e:

        # A serious problem happened, like an SSLError or InvalidURL
        print("An exception was thrown: {}".format(e))