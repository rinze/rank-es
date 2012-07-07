import logging
from google.appengine.ext import db
from google.appengine.api import memcache
from scores import get_score, get_score_modifier
from rankparser import get_title 
from rankconfig import cfg_links_rss

class LinkEnt(db.Model):
    """Link model.
    LinkEnt consists of:
    - title: Page title
    - url: URL
    - score: Score as given by get_score()[0]
    - date: Insertion date
    
    """
    title = db.StringProperty(required=True)
    url = db.StringProperty(required=True)
    score = db.IntegerProperty(required=True)
    date = db.DateTimeProperty(auto_now_add=True)

class OldLinkEnt(db.Model):
    """OldLink database used to store expired links
    and depopulate the main database. When a link has expired,
    only the url is needed.
    
    """
    url = db.StringProperty(required=True)

class RSSLinkEnt(db.Model):
    """RSS link model. Consists on:
    - title: Page title.
    - link: Page link.
    - score: Link score.
    - data: database population date. Same for all items.
    
    """
    title = db.StringProperty(required=True)
    url = db.StringProperty(required=True)
    score = db.IntegerProperty(required=True)
    date = db.DateTimeProperty(auto_now_add=True)

def update_links(c, links, current_time):
    """Updates the LinkEnt database with the current scores.
    The links to be updated are a GQL query passed as argument (c).
    
    """
    
    l = [x[0] for x in links]
    for e in c:
        if (e.url not in l):    # Update only links not recently added
            score = get_score(e.url)
            
            # How old is this link?
            time_diff = current_time - e.date
            mod = get_score_modifier(time_diff.total_seconds())
            e.score = int(score[0]*mod)
            e.put()

def get_top_links(n, update=False):
    """Returns the n top links"""
    c = memcache.get('toplinks%d' % n)   #@UndefinedVariable
    if not update and c:
        return c
    else:
        # LIMIT clause does not accept bound parameters. 
        # Use modulo operator for string formatting.
        q = 'SELECT * FROM LinkEnt ORDER BY score DESC LIMIT %d' % n
        c = db.GqlQuery(q)
        memcache.set('toplinks%d' % n, c)   #@UndefinedVariable
        return c

def insert_new_link(url, title=None, log=False):
    """Inserts a new LinkEnt into the datastore. If no title is
    provided, get_title() will be called to find it.
    Returns the link score.
    
    """
    if not title:
        title = get_title(url)
    score = get_score(url)
    if log:
        logging.info('Inserting link %s with score %d' % \
                     (url, score[0]))
    le = LinkEnt(title=title, url=url, score=score[0])
    le.put()
    return score

def delete_links(cursor):
    """Deletes all the links within the current cursor and stores them
    in OldLinkEnt
    Returns number of deleted links
    
    """
    expired_links = 0
    for e in cursor:
        ol = OldLinkEnt(url=e.url)
        ol.put()
        e.delete()
        expired_links += 1
    return expired_links
    
def url_in_db(url):
    """Returns True if the url is already in one of the Links databases,
    False otherwise
    
    """
    
    # If already in cache, return True
    res = memcache.get('lookup %s' % url)   #@UndefinedVariable
    if res:
        return res
    
    c = db.GqlQuery('SELECT * FROM LinkEnt WHERE url = :1', url)
    n1 = c.get()
    c = db.GqlQuery('SELECT * FROM OldLinkEnt WHERE url = :1', url)
    n2 = c.get()
    res = n1 is not None or n2 is not None
    if not res:
        return res
    else:
        # If it's in the database already, it will be forever, so let's cache
        # this, just in case we have a popular URL that is going to be
        # submitted time after time
        memcache.set('lookup %s' % url, True)   #@UndefinedVariable
        return res

def populate_rss_links():
    """Populates the RSSEnt database with cfg_links_rss top links. 
    This function is called daily. get_top_links(cfg_links_rss) cannot
    be used as it would have to be updated sometime and would be
    much more difficult to control.
    
    """
    
    # First, remove whatever links we already have
    c = RSSLinkEnt.all()
    db.delete(c)
    
    # Get cfg_links_rss top links (and don't get the cached copy)
    c = get_top_links(cfg_links_rss, True)
    for l in c:
        rss = RSSLinkEnt(title=l.title, url=l.url, score=l.score)
        rss.put()

def get_rss_links():
    """Get RSS links"""
    return RSSLinkEnt.all().order('-score')