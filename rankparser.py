# -*- coding: utf-8 -*-
import feedparser
import re
import HTMLParser
import urllib2
    
def get_meneame(url):
    '''Get links from meneame.net using special names'''
    d = feedparser.parse(url)
    result = [(e['meneame_url'], e['title']) for e in d['entries']]
    return result

def fix_url(url):
    '''Avoid URLs that don't begin with http(s)://'''
    if not url.startswith('http://') and not url.startswith('https://'):
        return 'http://' + url
    else:
        return url

def get_title(url):
    '''Returns the title for the given url, or the url
    if no title is found
    
    '''
    
    # TODO: perhaps^W re.compile is not the optimal way to do this
    # HTMLParser would be a better choice.
    
    try:
        data = urllib2.urlopen(url).read()
        
        # Try to get title
        ptitle = re.compile('<title>(.*?)</title>', re.DOTALL | re.M)
        title = ptitle.findall(data)
        if len(title) > 0:
            title = title[0]
        else:
            return url

        if not title or title == '':
            return url
        else:
            # No multiline strings!
            title = title.replace('\r', '')
            title = title.replace('\n', '')
            
            # Not optimal, but works
            try:
                title = unicode(title, encoding='utf-8')
            except:
                title = unicode(title, encoding='latin1')
            # Unescape before returning: don't want HTML entities
            return HTMLParser.HTMLParser().unescape(title)
    except:
        return url
    