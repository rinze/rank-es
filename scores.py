# -*- coding: utf-8 -*-
import urllib2
import json
import logging
from rankparser import fix_url
from rankconfig import cfg_link_expiration_seconds, cfg_link_fresh

def get_score_modifier(seconds):
    '''Returns a linear score modifier,
     that depends on how old a link is
     
     '''
    if seconds < cfg_link_fresh:
        return 1.0
    else:
        return (cfg_link_expiration_seconds - seconds + cfg_link_fresh)/float(cfg_link_expiration_seconds)
    
def get_score(url):
    '''Returns the global score'''

    # Fix the URL and quote it
    try:
        url = urllib2.quote(fix_url(url))
    except:
        # This happens once in a while
        logging.critical('Error while quoting url %s' % url)
        url = fix_url(url)

    # Get partial and global scores
    fb = get_fb_score(url)
    tw = get_tw_score(url)   
    scores = fb, tw
    return fb+tw, scores

def get_fb_score(url):
    '''Returns Facebook score for the given URL.
    Please note: http://stackoverflow.com/questions/5699270/how-to-get-share-counts-using-graph-api
    
    '''
    
    try:
        fb_url = 'http://graph.facebook.com/' + url
        d = urllib2.urlopen(fb_url).read()
        j = json.JSONDecoder().decode(d)
        if 'shares' in j:   
            return j['shares']
        else:
            return 0
    except:
        return 0

def get_tw_score(url):
    '''Returns Twitter score for the given URL '''
    
    try:
        tw_url = 'http://urls.api.twitter.com/1/urls/count.json?url=' \
                 + url
        d = urllib2.urlopen(tw_url).read()
        j = json.JSONDecoder().decode(d)
        return j['count']
    except:
        return 0
