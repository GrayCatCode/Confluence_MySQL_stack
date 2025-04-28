#! /bin/bash

curl -i -X POST \
     -H "Authorization:Bearer $JIRATUTORIAL_AUTH" \
     -H "Content-Type:application/json" \
     -H "X-Atlassian-Token:no-check" \
     "http://localhost:8090/confluence/rest/api/space/ds"
     -d '{ "space": { "key": "$SPACE_KEY" },
           "type": "page",
           "title": "This page created from a BASh shell script!",
           "body": { "storage": { "value": "This is my page content",
                                  "representation": "wiki" } } }'
