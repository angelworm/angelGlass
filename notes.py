# -*- coding: utf-8 -*- 
import os
import urllib2
import urllib
import json
import logging
import time
import sys
import lxml.html as html
import re

def fromURL(url):
    return re.search(r"(?:http://)?([\w.-]+)/post/(\d+).*", url, re.U | re.M | re.L | re.I).groups()

def getNotesKey(blog, noteid):
    text = urllib2.urlopen("http://%s/post/%s" % (blog, noteid)).read()
    result = re.search(r"/notes/(\d+)/(\w+)\?from\_c=(\d+)", text, re.U | re.M | re.L | re.I)
    if result is None:
        return text, (None, None, -1)
    else:
        return text, result.groups()

def getNotes(blog, noteid, note_load_id, from_c=0):
    text = urllib2.urlopen("http://%s/notes/%s/%s?from_c=%s" % (blog, noteid, note_load_id, from_c)).read().decode('utf-8')

    fromc_match = re.search(r"/notes/\d+/\w+\?from\_c=(\d+)", text, re.U | re.M | re.L | re.I)
    fromc = -1
    if fromc_match is not None:
        fromc = fromc_match.groups()[0]

    return html.fromstring(text), fromc

def notes(blog, noteid):
    text, (postid, postkey, fromc) = getNotesKey(blog, noteid)
    ret = []

    if fromc == -1:
        for li in html.fromstring(text).xpath('//ol[@class="notes"]/li'):
            if li.get('class', "") is None:
                continue
            if li.get('class', "").find("more_notes_link_container") == -1:
                ret.append(li)
            
        return ret
    else:
        fromc = 0
        while fromc != -1:
            ol, fromc = getNotes(blog, noteid, postkey, fromc)
            
            for li in ol:
                if li.get('class', "") is None:
                    continue
                if li.get('class', "").find("more_notes_link_container") == -1:
                    ret.append(li)
    
        return ret

def simplify(posts):
    def getHost(url):
        return re.search(r"(?:http://)?([\w.-]+)/?.*", url, re.U | re.M | re.L | re.I).groups()[0]

    ret = []
    for li in posts:
        o = {
            'type': li.attrib["class"].split()[1],
            'data': list()
        }
        if 'original_post' in li.attrib["class"].split():
            o['type'] = 'post'
        for a in li.xpath('.//a')[1:]:
            o['data'].append({
                'user_name': a.text_content().strip(),
                'user_blog': getHost(a.get('href', "***** "))
            })
        
        ret.append(o)
    return ret

def getPostNotes(url):
    return simplify(notes(*fromURL(url)))

def main(url):
    def prittyfy(li):
        for r in li.findall("blockquote"):
            li.remove(r)
        return li.text_content().strip()
    
    posts = notes(*fromURL(url))
    for li in posts:
        print prittyfy(li)
    print simplify(posts)

if __name__ == '__main__': 
    if len(sys.argv) != 2:
        print "useage: tublrnotes.py url"
    else:
        main(sys.argv[1])
