#!/bin/bash

# Confluence server details

# CONFLUENCE_URL=“Your confluence URL”
CONFLUENCE_URL="http://localhost:8090"

# PAGE_URL=“Your confluence page URL”
PAGE_URL="http://localhost:8090/display/TUS/Test+User+Page+1"

USERNAME="testuser"

API_TOKEN="testuser"

#You can either use your user name and API Token or password. Token is better as we can restrict access using that

# Page id will be the page number provided in the url

PAGE_ID=$(echo "${PAGE_URL}" | sed -n 's/.*pageId=\([0-9]*\).*/\1/p')

echo "Page ID: ${PAGE_ID}"

# Since to update the content, you first need to get the existing content and then append the updated content in it

EXISTING_CONTENT=$(curl -s -X GET  -H "Content-Type: application/json" -u "${USERNAME}:${API_TOKEN}" \  "${CONFLUENCE_URL}/rest/api/content/${PAGE_ID}?expand=body.storage" |  jq -r '.body.storage.value')

# New content to update the page with

NEW_CONTENT="This is the updated content for the Confluence page."

# Combine existing and new content

UPDATED_CONTENT="${EXISTING_CONTENT}\n\n${NEW_CONTENT}"

curl -s -X PUT -H "Content-Type: application/json"  -u "${USERNAME}:${API_TOKEN}" -d "{\"type\":\"page\",\"title\":\"Updated Page Title\",\"body\":{\"storage\":{\"value\":\"${UPDATED_CONTENT}\",\"representation\":\"storage\"}}}"  "${CONFLUENCE_URL}/rest/api/content/${PAGE_ID}"

echo "Curl command completed"

exit 0
