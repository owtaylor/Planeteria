#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Planeteria admin interface
Copyright 2011 James Vasile <james@hackervisions.org>
Released under AGPL, version 3 or later <http://www.fsf.org/licensing/licenses/agpl-3.0.html>
Version 0.2

"""

__authors__ = [ "James Vasile <james@hackervisions.org>"]
__license__ = "AGPLv3"

import simplejson as json
from util import merge_dict
import os, sys

from config import *
log = logging.getLogger('planeteria')
from util import Msg

#########################
 ##
## TEMPLATE FUNCTIONS
 ##
##########################
def render_text_input (id, label, default="", size = 25):
   "Return html for a text input field"
   default = default.encode('utf-8', 'ignore')
   return ('<label for="%s">%s:</label>' % (id, label)
          + '<input type="text" size="%d" name="%s" id="%s" value="%s">' % (size, id, id, default)
          + "\n")
def render_pass_input (id, label, default="", size = 25):
   "Return html for a password input field"
   return ('<label for="%s">%s:</label>' % (id, label)
           + '<input type="password" size="%d" name="%s" id="%s" value="%s">' % (size, id, id, default)
           + "\n")

def render_push_feed(planet):
   "Return javascript for pushing feeds into array"
   ret = ''

   for url, feed in planet.feeds.items():
      ret = (ret + "      new_feed('%s', '%s', %s, '%s', '%s', '%s', '%s');\n"
             % (url, url, json.dumps(feed['name']), '', feed['image'], '', ''))
   return ret
         
def template_vars(err, planet, form):
   "Returns a dict with the template vars in it"
   doc = opt.copy()
   doc['admin']=1
   doc['error'] = err.html()
   doc['name'] = planet.name
   doc['title'] = planet.name
   doc = dict(doc.items() + planet.__dict__.items() + [(k, form[k]) for k in form])
   if doc['password'] == 'passme':
      doc['passme'] = 1
   doc['planet_name_input'] = render_text_input("PlanetName", "Planet name", doc['name'], 40)
   doc['owner_name_input'] = render_text_input("OwnerName", "Your name", doc['user'], 40)
   doc['owner_email_input']=render_text_input("OwnerEmail", "Your email", doc['email'], 40)
   doc['change_pass_input'] = render_text_input("ChangePass", "New Password", form.getvalue('ChangePass',''))
   doc['pass_input'] = render_pass_input("Pass", "Password", form.getvalue('Pass', ''))
   doc['push_feeds'] = render_push_feed(planet)

   doc['timestamp'] = planet.last_config_change
   doc['Feeds']=[]
   count = 0
   for url, feed in planet.feeds.items():
      f={} 
      f['idx'] = count
      f['row_class'] = "face%d" % (count % 2)
      f['image'] = feed['image']
      if not f['image'] and 'faceurl' in feed:
         f['image'] = feed['faceurl']
         log.debug("Pulled url from feed['faceurl'].")
      f['feedurl'] = url
      f['facewidth'] = ''
      f['faceheight'] = '' 
      f['section'] = url
      f['name'] = feed['name']

      doc['Feeds'].append(f)
      count += 1;

   from operator import itemgetter, attrgetter
   doc['Feeds'] = sorted(doc['Feeds'], key=itemgetter('name'))
   return doc

############################
 ##
##  Config.ini Stuff
 ##
############################

# Helper function to prevent duplicate key values for new feeds.
def good_field(x):
   """Forms sometimes have duplicate fields; when they do, it turns into an array.
   Error cases always had a blank string and a real string. 
   This function returns the real string. """
   if isinstance(x,str): 
      return x
   else:
      for value in x:
         if len(value) > 1:
            return value

# Main function for config.ini
def update_config(planet, form, err):
   """Grab new values from the form and stick them in config.
   Modifies config in place.  Does not save to file."""
   for k,v in {'PlanetName':'name', 'OwnerName':'user', 'OwnerEmail':'email',
               'Pass':'password', 'Sidebar':'sidebar'}.items():
      planet.__dict__[v] = form.getvalue(k,'')

   if form.getvalue('ChangePass','') != '':
      planet.password = form.getvalue('ChangePass','')

   feed_count = 0;
   form_field = ['feedurl', 'name', 'image'] #, 'facewidth', 'faceheight']

   urls_seen = []
   while (form.has_key('section%d' % feed_count)):
      url = good_field(form.getvalue('feedurl%d' % feed_count,'')).strip()
      urls_seen.append(url)
      if not url:
         err.add("Ignoring feed with no url specified.")
         feed_count += 1;
         continue
      if good_field(form.getvalue('delete%d' % feed_count)) == '1':
         del planet.feeds[url]
      else:
         if not url in planet.feeds:
            planet.add_feed(url, 
                            good_field(form.getvalue('name%d' % feed_count, '').strip()),
                            form.getvalue('image%d' % feed_count, '').strip())
         else:
            # Copy the values from the form into planet
            for field in form_field:
               planet.feeds[url][field] = good_field(form.getvalue('%s%d' % (field, feed_count),'')).strip()
               log.debug(str(type(good_field(form.getvalue('%s%d' % (field, feed_count),'')))))
      feed_count += 1;

   # handle edited url
   to_delete=[]
   for url in planet.feeds:
      if not url in urls_seen:
         to_delete.append(url)
   for url in to_delete:
      del planet.feeds[url]
      log.debug("%s has changed.  Deleting old feed record." % url)

   return planet

############################
 ##
##  Setup and Prep
 ##
############################
import shutil, planet

## Setup and globals
VERSION = "0.2";


def handle(path, form, start_response):
#   import cgitb
#   cgitb.enable()

   err = Msg(web=True)
   planet_subdir = path.split(os.sep)[-2]

   from planet import Planet
   planet = Planet(direc=planet_subdir)

   ## Handle form input
   if form.has_key('PlanetName'):
      orig_pass = planet.password
      planet = update_config(planet, form, err)

      if form.getvalue('Timestamp') != str(planet.last_config_change):
         err.add("Admin page has expired!  Perhaps somebody else is " +
                 "editing this planet at the same time as you?  Please " +
                 "reload this page and try again.")
         #if debug: err.add("%s != %s" % (form.getvalue('Timestamp'), planet.last_config_change))
      elif form.getvalue('Pass','') == '':
         err.add("Please enter your password at the bottom of the page.")
      elif form.getvalue('Pass') != orig_pass:
         err.add("Invalid password")
      else:
         planet.save(update_config_timestamp=True)

   ## Template
   from templates import Admin
   start_response("200 OK", [('Content-Type', 'text/html')])
   a = Admin(template_vars(err, planet, form)).render()
   return [a]
