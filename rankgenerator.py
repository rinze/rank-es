# -*- coding=utf8 -*-
import jinja2
import os
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
    
    jinja_environment = jinja2.Environment(autoescape=True,
                        loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))
    template = jinja_environment.get_template('index.html')
    page = template.render(template_values) 
    memcache.set('index', page)     #@UndefinedVariable
    return page

def shortened_url(url, truncate=50):
    """Just for esthetic purposes"""
    if len(url) > truncate:
        return url[:truncate] + '...'
    else:
        return url
