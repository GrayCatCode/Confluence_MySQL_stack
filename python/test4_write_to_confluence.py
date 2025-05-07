# coding: utf-8
import argparse
import getpass
import datetime
import json
import keyring
import requests
import lxml.html

# -----------------------------------------------------------------------------
# Globals

# BASE_URL = "http://your-server/rest/api/content"
# VIEW_URL = "http://your-server/pages/viewpage.action?pageId="
# USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.82 Safari/537.36"

BASE_URL = "http://localhost:8090/rest/api/content"
VIEW_URL = "http://localhost:8090/pages/viewpage.action?pageId="
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.82 Safari/537.36"

def pprint(data):
    print json.dumps(
        data,
        sort_keys=True,
        indent=4,
        separators=(', ', ' : '))


def get_page_ancestors(auth, pageid):
    # Get basic page information plus the ancestors property

    url = '{base}/{pageid}?expand=ancestors'.format(
        base=BASE_URL,
        pageid=pageid)

    r = requests.get(url, auth=auth, headers={'Content-Type': 'application/json', 'USER-AGENT': USER_AGENT})

    r.raise_for_status()

    return r.json()['ancestors']


def get_page_info(auth, page_id):
    url = '{base}/{page_id}'.format(
        base=BASE_URL,
        page_id=page_id)

    r = requests.get(url, auth=auth, headers={'Content-Type': 'application/json', 'USER-AGENT': USER_AGENT})

    r.raise_for_status()

    return r.json()


def convert_db_to_view(auth2, html):
    url = 'http://your-server/rest/api/contentbody/convert/view'

    data2 = {
        'value': html,
        'representation': 'storage'
    }

    r = requests.post(url,
                      data=json.dumps(data2),
                      auth=auth2,
                      headers={'Content-Type': 'application/json'}
                      )
    r.raise_for_status()
    return r.json()


def convert_view_to_db(auth2, html):
    url = 'http://your-server/rest/api/contentbody/convert/storage'

    data2 = {
        'value': html,
        'representation': 'editor'
    }

    r = requests.post(url,
                      data=json.dumps(data2),
                      auth=auth2,
                      headers={'Content-Type': 'application/json'}
                      )
    r.raise_for_status()
    return r.json()


def write_data(auth, html, page_id):
    info = get_page_info(auth, page_id)

    ver = int(info['version']['number']) + 1

    ancestors = get_page_ancestors(auth, page_id)

    anc = ancestors[-1]
    del anc['_links']
    del anc['_expandable']
    del anc['extensions']

    info['title'] = "Team City Change Log"

    data = {
        'id': str(page_id),
        'type': 'page',
        'title': info['title'],
        'version': {'number': ver},
        'ancestors': [anc],
        'body': {
            'storage':
                {
                    'representation': 'storage',
                    'value': str(html),
                }
        }
    }

    data = json.dumps(data)

    url = '{base}/{page_id}'.format(base=BASE_URL, page_id=page_id)

    our_headers = {'Content-Type': 'application/json', 'USER-AGENT': USER_AGENT}

    r = requests.put(
        url,
        data=data,
        auth=auth,
        headers=our_headers
    )

    r.raise_for_status()

    print "Wrote '%s' version %d" % (info['title'], ver)
    print "URL: %s%d" % (VIEW_URL, page_id)

    return ""


def read_data(auth, page_id):
    url = '{base}/{page_id}?expand=body.storage'.format(base=BASE_URL, page_id=page_id)
    r = requests.get(
        url,
        auth=auth,
        headers={'Content-Type': 'application/json', 'USER-AGENT': USER_AGENT}
    )

    r.raise_for_status()

    return r


def patch_html(auth, options):
    json_text = read_data(auth, options.pageid).text
    json2 = json.loads(json_text)
    html_storage_txt = json2['body']['storage']['value']
    html_display_json = convert_db_to_view(auth, html_storage_txt)
    html_display_txt = html_display_json['value'].encode('utf-8')

    # PATCH 
    # new_view_string = custom patching of HTML here,
    return new_view_string


def get_login(username=None):
    if username is None:
        username = getpass.getuser()

    password = keyring.get_password('confluence_script', username)

    if password is None:
        password = getpass.getpass()
        keyring.set_password('confluence_script', username, password)

    return username, password


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-u",
        "--user",
        default=getpass.getuser(),
        help="Specify the username to log into Confluence")

    parser.add_argument(
        "pageid",
        type=int,
        help="Specify the Confluence page id to overwrite")

    options = parser.parse_args()

    auth = get_login(options.user)

    html = patch_html(auth, options)
    html = html.replace('&Acirc;', '')
    write_data(auth, html, options.pageid)
    return

if __name__ == "__main__": main()