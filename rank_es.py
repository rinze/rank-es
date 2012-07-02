# -*- coding=utf8 -*-
import webapp2
import logging
from scores import get_score
from google.appengine.api import memcache
from rankdb import url_in_db, insert_new_link
from rankgenerator import generate_main_page
from rankparser import get_title, fix_url, correct_url

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


class MainPage(webapp2.RequestHandler):

    def get(self):       

        # Get url if provided
        url = self.request.get('url')
        
        if url and url != '':
            # Insert new link into database and regenerate front page
            # Check if link already in database (current and old)
            url = fix_url(url)
            cor = correct_url(url)
            if not url_in_db(url) and cor:
                title = get_title(url)
                logging.info('New link inserted from front page: %s' % url)
                insert_new_link(url, title)     # Insert link into database
                generate_main_page()            # Generate main page    
                # TODO: a bit of feedback wouldn't hurt.
                self.redirect('/')              # Get rid of ugly GET url
            elif not cor:
                self.redirect('/')

        main_page = memcache.get('index')   #@UndefinedVariable
        if not main_page:
            main_page = generate_main_page()
        self.response.out.write(main_page)


   
app = webapp2.WSGIApplication([('/', MainPage), ('/instant', InstantPage)], 
                              debug=True)
