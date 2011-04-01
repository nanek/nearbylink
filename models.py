import logging
import urlparse

from google.appengine.ext import db
from google.appengine.api import users
from oauth2client.appengine import CredentialsProperty

import main

GEOLINK_BASE_URL = "http://nearbylink.appspot.com/"
GEOLINK_CODES = ["{postal_code}", "{continent}", "{latitude}", "{longitude}", "{country_code}", "{region}", "{state}", "{state_code}", "{city}", "{postal_code}", "{time_zone}", "{area_code}"]

LIST_STATES = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware",
  "District of Columbia", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
  "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
  "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico",
  "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island",
  "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
  "West Virginia", "Wisconsin", "Wyoming"]
LIST_STATE_CODES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", 
  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

class GeoLink(db.Model):
    url = db.StringProperty()
    user = db.UserProperty()
    shortlink = db.StringProperty()
    linkmap = db.TextProperty()
    linkmap_key = db.StringProperty()
    created_on = db.DateTimeProperty(auto_now_add=True)

    @property
    def geolink(self):
      if self.shortlink is None:
        return GEOLINK_BASE_URL + 'l/' + str(self.key())
      else:
        return self.shortlink

    @property
    def infolink(self):
      return GEOLINK_BASE_URL + 'i/' + str(self.key())
   
    def linkmap_find(self, code_value):
      value = None
      lines = self.linkmap.split('\n')
      for line in lines:
        parts = line.split('|')
        if parts[0].rstrip().lower()==code_value.lower():
          value = parts[1].rstrip()
        if parts[1].rstrip().lower()==code_value.lower():
          value = parts[0].rstrip()
      return value

    def validate(self):
      isValidInput = False
      if self.url:
        #validate input url
        link_code_count = 0
        for code in GEOLINK_CODES:
          link_code_start = self.url.find(code)
          if link_code_start != -1:
            link_code_count += 1
        if link_code_count == 0:
          raise main.ValidationError("link must use at least 1 code")
        else:
          if GeoLink.validateURL(self.url):
            isValidInput = True
      elif self.linkmap:
        #validate input linkmap and linkmap_key
        if self.linkmap and self.linkmap_key:
          valid_codes = None
          if self.linkmap_key == "state_code":
            valid_codes = LIST_STATE_CODES
          elif self.linkmap_key == "state":
            valid_codes = LIST_STATES
          else:
            raise main.ValidationError("Invalid code for map")
          lines = self.linkmap.split('\n')
          for line in lines:
            parts = line.split('|')
            if len(parts) !=2:
              raise main.ValidationError("Each line must have a code and a URL seperated by |")
            if parts[0].rstrip().upper() in valid_codes:
              GeoLink.validateURL(parts[1])
            elif parts[1].rstrip().upper() in valid_codes:
              GeoLink.validateURL(parts[0])
            else:
              raise main.ValidationError("Missing or invalid code value")
          isValidInput = True
      else:
        raise main.ValidationError("Must enter link or linkmap")
      return isValidInput

    @classmethod
    def validateURL(cls, url):
      #TODO: throw exception instead of catching
      parts = None
      try:
        parts = urlparse.urlparse(url)
      except Exception, e:
        logging.error(e)
        raise main.ValidationError("URL is not valid")
      if not all([parts.scheme, parts.netloc]):
        raise main.ValidationError("URL not complete")
      if parts.scheme not in ['http', 'https']:
        raise main.ValidationError("URL missing scheme (http or https)")
      return True

class Credentials(db.Model):
  credentials = CredentialsProperty()

