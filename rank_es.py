# -*- coding=utf8 -*-
import webapp2
import logging
from scores import get_score
from google.appengine.api import memcache
from rankdb import url_in_db, insert_new_link, get_rss_links, \
    populate_rss_links
from rankgenerator import generate_main_page, generate_submitted_error_page,\
    generate_submitted_page, generate_rss_items
from rankparser import get_title, fix_url, correct_url
import PyRSS2Gen

class InstantPage(webapp2.RequestHandler):
    """Class that handles instant queries"""
    def get(self):
        url = self.request.get('url')
        if not url or url == '':
            self.response.out.write('<form><input name="url" type="text" /></form>')
        else:
            self.response.headers['Content-Type'] = 'text/plain'
            _, (fb, tw) = get_score(url)
            self.response.out.write(url + '\n')
            self.response.out.write('Facebook: %d, Twitter: %d' % (fb, tw))

class SubmittedPage(webapp2.RequestHandler):
    
    def get(self):
        
        template_values = {
                           'url': self.request.get('url'),
                           'via': self.request.get('via'),
                           'score': self.request.get('score')
                           }
        self.response.out.write(generate_submitted_page(template_values))

class SubmittedErrorPage(webapp2.RequestHandler):
    
    def get(self):
        
        template_values = {
                           'url': self.request.get('url'),
                           'via': self.request.get('via'),
                           }
        self.response.out.write(generate_submitted_error_page(template_values))



class RSS(webapp2.RequestHandler):
    """Generates RSS data"""
    def get(self):
        
        # Get RSS links
        links = map(generate_rss_items, get_rss_links())
        rss_data = PyRSS2Gen.RSS2(
                    title = 'rank-es: mejores enlaces diarios',                            
                    link = 'http://rank-es.appspot.com', 
                    description = 'Actualizado diariamente. http://rank-es.appspot.com',
                    lastBuildDate = links[0].pubDate,
                    items = links)
        self.response.out.write(rss_data.to_xml(encoding="utf-8"))
        
class RSSPopulate(webapp2.RequestHandler):
    """Populates RSS database via daily cron job"""
    def get(self):
        populate_rss_links()

class MainPage(webapp2.RequestHandler):

    def get(self):       

        # Get url if provided
        url = self.request.get('url')
        via = self.request.get('via')
        
        
        if url and url != '':
            # Insert new link into database and regenerate front page
            # Check if link already in database (current and old)
            url = fix_url(url)
            cor_url = correct_url(url)
            if cor_url and not url_in_db(url):
                title = get_title(url)
                # Insert link into database
                score, (_, _) = insert_new_link(url, title)
                logging.info('New link inserted from front page: %s (%d)' %
                              (url, score))

                # Generate main page
                generate_main_page()            
                    
                # Feedback
                self.redirect('/submitted?via=%s&url=%s&score=%s' % 
                              (via, url, str(score)))
                
            else:
                self.redirect('/submittederror?via=%s&url=%s' % 
                              (via, url))
                
        main_page = memcache.get('index')   #@UndefinedVariable
        if not main_page:
            main_page = generate_main_page()
        self.response.out.write(main_page)

# Define handler classes (except feedbot, which goes on his own)   
app = webapp2.WSGIApplication([('/', MainPage), 
                               ('/instant', InstantPage), 
                               ('/submitted', SubmittedPage), 
                               ('/submittederror', SubmittedErrorPage),
                               ('/rss', RSS),
                               ('/populate_rss', RSSPopulate)], 
                              debug=True)
