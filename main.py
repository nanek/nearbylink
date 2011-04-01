#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import views
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library
use_library('django', '0.96')
#use_library('django', '1.2')

def main():
    application = webapp.WSGIApplication([('/', views.MainHandler),
      ('/about', views.AboutHandler),
      ('/credentials', views.CredentialHandler),
      ('/auth_return', views.OAuthHandler),
      ('/dashboard/', views.GeoLinkHandler),
      ('/dashboard/create', views.CreateGeoLinkHandler),
      ('/l/(.*)', views.ViewLinkHandler),
      ('/i/(.*)', views.ViewLinkInfoHandler),
      ('.*', views.NotFoundHandler)],
                                         debug=True)
    util.run_wsgi_app(application)

class ValidationError(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        Exception.__init__(self, message)

if __name__ == '__main__':
    main()
