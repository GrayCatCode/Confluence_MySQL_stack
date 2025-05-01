from atlassian import Confluence
import re
import urllib

# regex pattern to match pageId if already in url
page_id_in_url_pattern = re.compile(r"\?pageId=(\d+)")

def get_page_id_from_url(confluence, url):
    page_url = urllib.parse.unquote(url) #unquoting url to deal with special characters like '%'
    space, title = page_url.split("/")[-2:]

    if re.search(page_id_in_url_pattern, title):
        return re.search(page_id_in_url_pattern, title).group(1)
    
    else:
        title = title.replace("+", " ")
        return confluence.get_page_id(space, title)



if __name__ == "__main__":
    from getpass import getpass
    user = input('Login: ')
    pwd = getpass('Password: ')

    page_url = "https://confluence.som.yale.edu/display/SC/Finding+the+Page+ID+of+a+Confluence+Page"

    confluence = Confluence(
            url='https://confluence.som.yale.edu/',
            username=user,
            password=pwd)

    print(get_page_id_from_url(confluence, page_url))