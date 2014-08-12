import os
import sqlite3
import feedparser
from time import strftime, strptime, localtime


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class MPDPodcast(object):
    def __init__(self, 
                 db_filename = 'mpd_podcast.db' ,
                 schema_filename = 'mpd_podcast_schema.sql'):
        db_is_new= not os.path.exists(db_filename)
        self.db_filename = db_filename
        if db_is_new:
            with sqlite3.connect(db_filename) as conn:
            
                print 'Database creation'
                with open(schema_filename, 'rt') as f:
                    schema= f.read()
                conn.executescript(schema)
    
    def add_flux(self,url, title=None):
        """
        Add a flux to the database, using the url.
        If you give a title it will overwrite the RSS title
        """

        #Getting the data
        P=feedparser.parse(url)
        if P.feed=={}:
            print 'Flux vide'
            return -1
        if title==None:
            title=P.feed.title
        print 'url         :', url
        print 'title       :', title
    
        last_update = strftime("%Y-%m-%d %H:%M:%S",P.feed.published_parsed ) if 'published_parsed' in P.feed else strftime("%Y-%m-%d %H:%M:%S")
        print 'last_update :', last_update

        #Update the database
        last_id=1
        with sqlite3.connect(self.db_filename) as conn:
            cursor=conn.cursor()

            #Add flux
            cursor.execute("""
            INSERT INTO flux (url, titre, last_update)
            VALUES ( :url, :title, :last_update)
            """, {'url':url, 'title':title, 'last_update':last_update})
            last_id=cursor.lastrowid


        self.check_flux(last_id, P)


    def get_data(table, item_id, column):
        with sqlite3.connect(self.db_filename) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
            SELECT :column FROM :table where id= :item_id
            ORDER BY id
            """,  {'column':column,
                   'table':table,
                   'item':item_id})
            return cursor.fetchall()[0][column]
            

    def check_flux(self, flux_id, flux=None, date=None):
        if flux==None:
            
            flux=feedparser.parse(url)
            if flux.feed=={}:
                print 'Flux vide'
                return -1



        with sqlite3.connect(self.db_filename) as conn:
            cursor=conn.cursor()
            #print 'Flux id     :', flux_id
            #print "----------------------------------------"
            #Add all audio item
            for f in flux.entries:
                if date==None or date<f.published_parsed:
                    for l in f.links:
                        if l.rel=="enclosure" and l.type[:5]=="audio":
                            item_title=f.title
                            href=l['href']
                            item_date=strftime("%Y-%m-%d %H:%M:%S",
                                               f.published_parsed )
                            #print '\t title :', item_title 
                            #print '\t url   :', href
                            #print '\t date  :', item_date
                            status=0
                            cursor.execute("""
                            INSERT INTO item (titre, url, status, item_date, flux)
                            VALUES ( :title, :url, :status, :item_date , :flux_id)
                            """, {'title':item_title, 
                                  'url':href,
                                  'status':status,
                                  'item_date':item_date,
                                  'flux_id':flux_id})
                            #print "\n"
            #Update the last_update date:
            now=strftime("%Y-%m-%d %H:%M:%S",localtime())
            
            cursor.execute("""
            UPDATE flux 
            SET last_update= :now
            WHERE id = :flux_id
            """, {'flux_id':flux_id,
                  'now':now})

    def list_flux(self, flux_id):
        with sqlite3.connect(self.db_filename) as conn:
            conn.row_factory = dict_factory
            cursor=conn.cursor()
            cursor.execute("""
            SELECT * FROM flux WHERE id= :flux_id
            ORDER BY id
            """,  {'flux_id':flux_id})
            flux=[row for row in cursor.fetchall() ]
            return flux

    def print_flux(self, flux_id):
        flux=self.list_flux(flux_id)
        print "id  |  Title  *   last  Update"
        for f in flux:
            print f['id']," | ", f['titre'], " * ",  f['last_update']


if __name__ == '__main__':
    #pod='http://podcast.college-de-france.fr/xml/histoire.xml'
    pod="http://feeds.feedburner.com/PodcastScience"
    w=MPDPodcast()
    w.add_flux(pod)
    w.print_flux(1)
