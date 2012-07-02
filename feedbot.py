# -*- coding=utf8 -*-
import webapp2
import logging
from rankparser import get_meneame
from rankdb import update_links, get_top_links, insert_new_link, \
    delete_links
from google.appengine.ext import db
from datetime import datetime, timedelta
from rankgenerator import generate_main_page
from rankconfig import cfg_links_front_page, cfg_link_expiration_seconds
    
class FeedBot(webapp2.RequestHandler):
    
    def get(self):
        """
        1 - Remove expired links
        2 - Gets new items from meneame.net and includes them in the database
        3 - Update scores for already existing links
        
        """
        
        # Remove expired links
        today = datetime.today()                
        logging.info('Doing database cleanup')
        
        # First, low-score links with no chance of getting to the front page.
        links = [x for x in get_top_links(cfg_links_front_page)]
        if len(links) > 0:  # Just in case we have not populated the database
                            # This is necessary as we are not working directly
                            # on the query cursor but are building a list
            min_score = links[-1].score
            # Everything with more than cfg_link_expiration_seconds/10
            # age and less than min_score/3 will go away.
            time_diff = today - timedelta(seconds = cfg_link_expiration_seconds/10)
            c = db.GqlQuery('SELECT * FROM LinkEnt WHERE date < :1', 
                            time_diff)
            # Cannot run the query with two selectors the way I want, so let's
            # do it another way.
            low = [x for x in c if x.score < min_score/3]
            expired_links = delete_links(low)
            logging.info('%d links removed due to low scores' % expired_links)

        # Now, expired links        
        time_diff = today - timedelta(seconds = cfg_link_expiration_seconds)
        c = db.GqlQuery('SELECT * FROM LinkEnt WHERE date < :1', time_diff)
        expired_links = delete_links(c)
        logging.info('%d links expired. Shiny database!' % expired_links)

        logging.info('Getting meneame.net latest RSS items.')
        # Front page
        l1 = get_meneame('http://www.meneame.net/rss2.php?meta=0')
        # Voting queue
        l2 = get_meneame('http://www.meneame.net/rss2.php?status=queued&meta=0')
        links = l1 + l2
        
        # Filter the links: use only the ones we don't already have
        current_links_db = db.GqlQuery('SELECT * FROM LinkEnt')
        current_links = [x.url for x in current_links_db]
        # Get results into an array to avoid expiration when updating
        # DB queries last for only 30 seconds.
        current_links_ents = [x for x in current_links_db]
        new_links = [x for x in links if x[0] not in current_links]

        # Insert new links into database
        logging.info('%d links in database, %d retrieved, %d to be inserted' 
                     % (len(current_links), len(links), len(new_links)))
        for l in new_links:
            url, title = l
            insert_new_link(url, title, log=False)
        logging.info('Finished fetching new items.')

        # Update the links scores and the top links cached search
        logging.info('Updating %d links...' % len(current_links_ents))
        update_links(current_links_ents, new_links, datetime.today())
        get_top_links(cfg_links_front_page, update=True)
        logging.info('Finished updating links.')
        
        # Update Main Page
        logging.info('Generating main page...')
        generate_main_page()
        logging.info('Main page generated')
        

# TODO: this bot should publish, at regular intervals, the most relevant
# news, either from the front page or from any of the categories.
# Further database tweaking may be needed.
# For now, let's just write a reminder that this shall be done.
# The Twitter account rank_es has been reserved for this purpose (by @rinze).
class TwitterBot():
    pass
   
app = webapp2.WSGIApplication([('/feedbot', FeedBot)], debug=True)
