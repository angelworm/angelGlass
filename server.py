# -*- coding: utf-8 -*-

import BaseHTTPServer
import urllib, urllib2, urlparse
import os
import sys
import re
import json
import functools
from config import getApiKey
import notes

class Server(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse.urlparse(self.path)
        pattern = [
            ("/lib/.*", self.getStaticFile, (url.path[1:],)),
            ("/api/post", self.getPost, (url,)),
            ("/api/note", self.getNote, (url,)),
            ("/api/info", self.getInfo, (url,)),
            ("/api/avatar", self.getIcon, (url,)),
            (".*", self.getStaticFile, ('index.html',))
        ]
        for p, func, args in pattern:
            if re.match(p, url.path) is not None:
                func(*args)
                break
        
    def getStaticFile(self, path):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(path, 'r') as fp:
            for line in fp:
                self.wfile.write(line)
        self.wfile.close()

    def getPost(self, url):
        param = dict(urlparse.parse_qsl(url.query))

        for i in ['blog']:
            if i not in param:
                self.getStaticFile('index.html')
                return
            
        blog = param.pop('blog')
        param.setdefault('api_key', getApiKey())
        param.setdefault('notes_info', "true") # too few informations!
        if 'type' in param:
            postType = '/' + param['type']
        else:
            postType = ''

        url = "http://api.tumblr.com/v2/blog/%s/posts%s?%s" % (blog, postType, urllib.urlencode(param))
        res = urllib2.urlopen(url)
        
        self.send_response(res.getcode())
        for h in res.headers:
            self.send_header(h, res.headers[h])
        self.end_headers()

        for line in res:
            self.wfile.write(line)
        self.wfile.close()
        
        
    def getNote(self, url):
        param = dict(urlparse.parse_qsl(url.query))

        for i in ['url']:
            if i not in param:
                self.getStaticFile('index.html')
                return
            
        obj = notes.getPostNotes(param['url'])

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj))
        self.wfile.close()

    def getInfo(self, url):
        param = dict(urlparse.parse_qsl(url.query))

        for i in ['blog']:
            if i not in param:
                self.getStaticFile('index.html')
                return
            
        blog = param.pop('blog')
        param.setdefault('api_key', getApiKey())

        url = "http://api.tumblr.com/v2/blog/%s/info?%s" % (blog, urllib.urlencode(param))
        res = urllib2.urlopen(url)
        
        self.send_response(res.getcode())
        for h in res.headers:
            self.send_header(h, res.headers[h])
        self.end_headers()

        for line in res:
            self.wfile.write(line)
        self.wfile.close()

    def getIcon(self, url):
        param = dict(urlparse.parse_qsl(url.query))

        for i in ['blog']:
            if i not in param:
                self.getStaticFile('index.html')
                return
            
        blog = param.pop('blog')
        param.setdefault('api_key', getApiKey())
        size = param.get('size', 30)

        url = "http://api.tumblr.com/v2/blog/%s/avatar/%d" % (blog, size)
        res = urllib2.urlopen(url)
        
        self.send_response(res.getcode())
        for h in res.headers:
            self.send_header(h, res.headers[h])
        self.end_headers()

        self.wfile.write(res.read())
        self.wfile.close()

if __name__ == '__main__':
    server_address = ('', 8000)
    httpd = BaseHTTPServer.HTTPServer(server_address, Server)
    httpd.serve_forever()

