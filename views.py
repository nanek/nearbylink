import logging
import os
import pickle
import httplib2

from apiclient.discovery import build
from oauth2client.appengine import CredentialsProperty
from oauth2client.appengine import StorageByKeyName
from oauth2client.client import OAuth2WebServerFlow
from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext.webapp.util import login_required

import models
import quova
import urlshortener

GOOGLEAPI_CLIENT_ID='CLIENT_ID_HERE'
GOOGLEAPI_CLIENT_SECRET='CLIENT_SECRET_HERE'
GOOGLEAPI_SCOPE='https://www.googleapis.com/auth/urlshortener'
GOOGLEAPI_USER_AGENT='nearbylink/1.0'
GOOGLEAPI_XOAUTH_DISPLAYNAME='Nearby Link'

class BaseRequestHandler(webapp.RequestHandler):
  def render(self, template_name, template_values):
    user = users.get_current_user()
    values = {
          'user': user,
          'logout_url': users.create_logout_url('/'),
        }
    values.update(template_values)
    directory = os.path.dirname(__file__)
    path = os.path.join(directory, os.path.join('views', template_name))
    self.response.out.write(template.render(path, values, debug=False))

class MainHandler(BaseRequestHandler):
  def get(self):
    ip_addr = self.request.remote_addr
    location = quova.ipinfo(ip_addr);
    user_state = quova.get(location, "state").capitalize()
    user_zip = quova.get(location, "postal_code")

    self.render('home/index.html', {'user_state':user_state,
      'user_zip':user_zip});

class AboutHandler(BaseRequestHandler):
  def get(self):
    self.render('home/about.html', {});

class NotFoundHandler(BaseRequestHandler):
  def get(self):
    self.error(404)
    self.render('404.html', {});

class GeoLinkHandler(BaseRequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      
      ip_addr = self.request.remote_addr
      location = quova.ipinfo(ip_addr);
      parts = {} 
      for code in models.GEOLINK_CODES:
        parts[code.lstrip('{').rstrip('}')] = quova.get(location, code.lstrip('{').rstrip('}'));

      links = models.GeoLink.gql("WHERE user = :1 ORDER BY created_on desc", user) 
      self.render('link/index.html', {'page_title':'link',
        'links': links,
        'parts': parts})
    else:
      self.error(403)

class CreateGeoLinkHandler(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()
    only_validate = self.request.get("validate")
    if user:
      #get params
      url = self.request.get("url")
      linkmap = self.request.get("linkmap")
      linkmap_key = self.request.get("linkmap_key")
      link = models.GeoLink(user=user)
      if url:
        link.url = url
      else:
        link.linkmap = linkmap
        link.linkmap_key = linkmap_key
      valid_input = False
      try:
        valid_input = link.validate()
      except Exception, e:
        self.response.out.write(e)

      if only_validate == "" and valid_input == True:
        key = link.put()

        #create shortlink goo.gl
        credentials = StorageByKeyName(models.Credentials, user.user_id(), 'credentials').get()
        if credentials and credentials.invalid == False:
          link.shortlink = urlshortener.shorten(models.GEOLINK_BASE_URL + 'l/' + str(key), credentials)
          link.put()
        #self.response.out.write("saved the link " + url)
        self.redirect("/dashboard/")
      elif only_validate and valid_input == True:
        self.response.out.write("valid")
    else:
      self.error(403)

class ViewLinkInfoHandler(BaseRequestHandler):
  def get(self, key):
    geolink = models.GeoLink.get(key)
    self.render('link/info.html', {'geolink':geolink});

class ViewLinkHandler(webapp.RequestHandler):
  def get(self, key):
    ip_addr = self.request.remote_addr
    link = None
    try:
      link = models.GeoLink.get(key)
    except:
      self.error(404)
    if link:
      url = None
      res = quova.ipinfo(ip_addr)
      if link.url:
        # replace params
        url = link.url
        for code in models.GEOLINK_CODES:
          link_code_start = url.find(code)
          if link_code_start != -1:
            link_code_name = code.lstrip('{').rstrip('}')
            link_code_value = quova.get(res, link_code_name)
            if link_code_value:
              url = url.replace(code,link_code_value)
            else:
              url = url.replace(code,"")
      else:
        # parse linkmap to find appropriate link
        code_value = quova.get(res, link.linkmap_key)
        if code_value:
          url = link.linkmap_find(code_value)
      if url is None:
        # redirect to link info page
        self.redirect(link.infolink)
      else:
        self.redirect(url)
    else:
      self.error(404)


class CredentialHandler(webapp.RequestHandler):

  @login_required
  def get(self):
    user = users.get_current_user()
    credentials = StorageByKeyName(
        models.Credentials, user.user_id(), 'credentials').get()

    if credentials is None or credentials.invalid == True:
      flow = OAuth2WebServerFlow(
          # Visit https://code.google.com/apis/console to
          # generate your client_id, client_secret and to
          # register your redirect_uri.
          client_id=GOOGLEAPI_CLIENT_ID,
          client_secret=GOOGLEAPI_CLIENT_SECRET,
          scope=GOOGLEAPI_SCOPE,
          user_agent=GOOGLEAPI_USER_AGENT,
          #domain='anonymous',
          xoauth_displayname=GOOGLEAPI_XOAUTH_DISPLAYNAME)

      callback = self.request.relative_url('/auth_return')
      authorize_url = flow.step1_get_authorize_url(callback)
      memcache.set(user.user_id(), pickle.dumps(flow))
      self.redirect(authorize_url)
    else:
      self.redirect('/dashboard/')

class OAuthHandler(webapp.RequestHandler):

  @login_required
  def get(self):
    user = users.get_current_user()
    flow = pickle.loads(memcache.get(user.user_id()))
    if flow:
      credentials = flow.step2_exchange(self.request.params)
      StorageByKeyName(
          models.Credentials, user.user_id(), 'credentials').put(credentials)
      self.redirect("/dashboard/")
    else:
      pass

