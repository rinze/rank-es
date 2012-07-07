# -*- coding=utf8 -*-
import jinja2
import os
import PyRSS2Gen
from google.appengine.api import memcache
from rankdb import get_top_links
from rankconfig import cfg_links_front_page


def generate_main_page(template_values={}):
    """"Generates the main page HTML and memcaches it"""
    
    c = get_top_links(cfg_links_front_page)
    links = [{'url':x.url, 'title':x.title, 'score': x.score,
              's_url': shortened_url(x.url), 
              'q_title': x.title.replace(' ', '+')} for x in c]
    template_values['links'] = links
    
    page = prepare_template('index.html', template_values) 
    memcache.set('index', page)     #@UndefinedVariable
    return page

def generate_submitted_page(template_values):
    """Generates the 'Thank you for submitting a new link' page"""
    
    # 'via' key must be in template values. Else, return None
    if 'via' not in template_values:
        return None
    
    if template_values['via'] == 'bookmarklet':
        page = prepare_template('submitted_b.html', template_values)
    else:
        page = prepare_template('submitted.html', template_values)
        
    return page
    
def generate_submitted_error_page(template_values):
    """Generates the 'The link you just send is crap or already in database"""
    
    # 'via' key must be in template_values. Else, return None
    if 'via' not in template_values:
        return None
    
    if template_values['via'] == 'bookmarklet':
        page = prepare_template('submitted_error_b.html', template_values)
    else: 
        page = prepare_template('submitted_error.html', template_values)
        
    return page

def shortened_url(url, truncate=50):
    """Just for esthetic purposes"""
    if len(url) > truncate:
        return url[:truncate] + '...'
    else:
        return url

def prepare_template(page, template_values):
    """Sets up a Jinja2 template and returns the generated page"""
    jinja_environment = jinja2.Environment(autoescape=True,
                        loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))
    template = jinja_environment.get_template(page)
    page = template.render(template_values)
    return page


def generate_rss_items(item_data):
    """Generates RSS item data using PyRSS2Gen library"""
    return PyRSS2Gen.RSSItem(title = '(%d) %s' % 
                          (item_data.score, item_data.title), 
                      link = item_data.url,
                      guid = PyRSS2Gen.Guid(item_data.url),
                      pubDate = item_data.date,
                      description = item_data.url)
    
