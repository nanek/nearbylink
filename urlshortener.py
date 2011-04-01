import httplib2
import sys

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import AccessTokenCredentials
from oauth2client.tools import run

GOOGLE_DEVELOPER_KEY = "DEVELOPER_KEY_HERE"

def shorten(longurl, credentials):
  #credentials = run(FLOW, storage)

  http = httplib2.Http()
  http = credentials.authorize(http)

  # Build the url shortener service
  service = build("urlshortener", "v1", http=http,
            developerKey=GOOGLE_DEVELOPER_KEY)
  url = service.url()

  # Create a shortened URL by inserting the URL into the url collection.
  body = {"longUrl": longurl }
  resp = url.insert(body=body).execute()

  shortUrl = resp['id']
  return shortUrl
