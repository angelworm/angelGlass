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
import webapp2
import mimetypes
import os.path
from google.appengine.ext import db
import urllib2
import urllib
import notes
import json

class TumblrAPI(db.Model):
    appkey = db.StringProperty(required=True)

def getAPIkey():
    api = TumblrAPI.all().get()
    if(api == None):
        print "please set Tumblr Application key into GAE Application database"
        return ""
    else:
        return api.appkey

class PostHandler(webapp2.RequestHandler):
    def get(self):
        self.post()

    def post(self):
        blog = self.request.get("blog")

        if blog == "":
            self.redirect("/", abort=True)
            
        param = {}
        param['api_key'] = self.request.get('api_key', default_value=getAPIkey())
        param['notes_info'] = self.request.get('notes_info', default_value="true")
       
        typeQuery = self.request.get('type', default_value=None)

        if typeQuery:
            postType = '/' + typeQuery
            param['type'] = typeQuery
        else:
            postType = ''

        url = "http://api.tumblr.com/v2/blog/%s/posts%s?%s" % (blog, postType, urllib.urlencode(param))
        print url
        res = urllib2.urlopen(url)
        
        self.response.status = res.getcode()
        for h in res.headers:
            self.response.headers.add(h, res.headers[h])

        for line in res:
            self.response.out.write(line)

class NoteHandler(webapp2.RequestHandler):
    def get(self):
        url = self.request.get('url')
            
        if url == "":
            self.redirect("/", abort=True)
        else:
            obj = notes.getPostNotes(url)

        self.response.status = 200
        self.response.headers["Content-type"] = "application/json"
        self.response.out.write(json.dumps(obj))

class IconHandler(webapp2.RequestHandler):
    def get(self):
        blog = self.request.get("blog")
        size = self.request.get('size', default_value=30)

        if blog == "":
            self.redurect("/", abort=True)
            
        url = "http://api.tumblr.com/v2/blog/%s/avatar/%d" % (blog, size)
        res = urllib2.urlopen(url)
        
        self.response.status = res.getcode()
        for h in res.headers:
            self.response.headers.add(h, res.headers[h])

        self.response.out.write(res.read())

class InfoHandler(webapp2.RequestHandler):
    def get():
        blog = self.request.get("blog")

        if blog == "":
            self.redurect("/", abort=True)
            
        param = {}
        param['api_key'] = self.request.get('api_key', default_value=getAPIkey())

        url = "http://api.tumblr.com/v2/blog/%s/info?%s" % (blog, urllib.urlencode(param))
        res = urllib2.urlopen(url)
        
        self.response.status = res.getcode()
        for h in res.headers:
            self.response.headers.add(h, res.headers[h])

        self.response.out.write(res.read())


class StaticHandler(webapp2.RequestHandler):
    def get_local_file(self, path):
        localpath = os.path.join("static/", path)

        if not localpath.startswith("static/"):
            self.abort(404)

        try:
            self.response.headers["Content-Type"] = mimetypes.guess_type(localpath)[0]
            self.response.out.write(open(localpath).read())
        except IOError as e:
            print e
            self.redirect("/", abort=True)

    def get(self, path):
        print "hoge:", path
        if path == "":
            self.get_local_file("index.html")
        else:
            self.get_local_file(path)

class InitHandler(webapp2.RequestHandler):
    def get(self):
        if getAPIkey() == "":
            TumblrAPI(appkey="hoge").put()
            self.response.out.write("<h1>fuga</h1>")
        else:
            self.response.out.write("<h1>hoge</h1>")

app = webapp2.WSGIApplication([
    ("/api/init", InitHandler),
    ("/api/post", PostHandler),
    ("/api/note", NoteHandler),
    ("/api/icon", IconHandler),
    ("/api/info", InfoHandler),
    ('/(.*)', StaticHandler)
], debug=True)
