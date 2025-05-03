from atlassian import Confluence
import re
import urllib

# Regex pattern to match the page ID if already in URL:
page_id_in_url_regex_pattern = re.compile(r"\?pageId=(\d+)")

# Function that extracts the ID of the Confluence page specified in the `page_url`:
def get_page_id_from_url(confluence, url):
    page_url = urllib.parse.unquote(url) #unquoting url to deal with special characters like '%'
    space, page_title = page_url.split("/")[-2:]

    # If there's a page ID found in the response URL, parse the URL and return it:
    if re.search(page_id_in_url_regex_pattern, page_title):
        return_str = "The ID of the page is: " + re.search(page_id_in_url_pattern, page_title).group(1)
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