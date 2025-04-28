import requests
import json
from requests.auth import HTTPBasicAuth

# set auth token and get the basic auth code
#auth_token = "{TOKEN}"
auth_token = "AndrewPoloni"

#basic_auth = HTTPBasicAuth('{email you use to log in}', auth_token)
basic_auth = HTTPBasicAuth('andrew.poloni@maxar.com', auth_token)

# Set the title and content of the page to create
page_title = 'My New Page'
page_html = '<p>This page was created by Andrew Poloni with Python!</p>'

#parent_page_id = {Parent Page ID}
parent_page_id = 98361
#space_key = '{SPACE KEY}'
space_key = 'AS'

# get the confluence home page url for your organization {confluence_home_page}
#url = '{confluence_home_page}/rest/api/content/'
url = 'http://localhost:8090/rest/api/content/'

# Request Headers
headers = {
    'Content-Type': 'application/json;charset=iso-8859-1',
}

# Request body
data = {
    'type': 'page',
    'title': page_title,
    'ancestors': [{'id':parent_page_id}],
    'space': {'key':space_key},
    'body': {
        'storage':{
            'value': page_html,
            'representation':'storage',
        }
    }
}

# We're ready to call the api
try:

    r = requests.post(url=url, data=json.dumps(data), headers=headers, auth=basic_auth)

    # Consider any status other than 2xx an error
    if not r.status_code // 100 == 2:
        print("Error: Unexpected response {}".format(r))
    else:
        print('Page Created!')

except requests.exceptions.RequestException as e:

    # A serious problem happened, like an SSLError or InvalidURL
    print("Error: {}".format(e))