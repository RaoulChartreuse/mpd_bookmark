import os
import sqlite3
import feedparser
from time import strftime, strptime, localtime
import urllib,sys


def report(blocknr, blocksize, size):
    current = blocknr*blocksize
    sys.stdout.write("\r{0:.2f} %".format(100.0*current/size))


def downloadFile(url, path):
    urllib.urlretrieve(url, path, report)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d



class MPDPodcast(object):
    def __init__(self, 
                 db_filename = 'mpd_podcast.db' ,
                 schema_filename = 'mpd_podcast_schema.sql',
                 podcast_path = None):
        #Database setup
        db_is_new= not os.path.exists(db_filename)
        self.db_filename = db_filename
        self.podcast_path = podcast_path
        with sqlite3.connect(db_filename) as conn:
            if db_is_new:
                #Test if the podcast directory is available
                assert podcast_path != None
                assert os.path.isdir(podcast_path)
                
                print 'Database creation'
                with open(schema_filename, 'rt') as f:
                    schema= f.read()
                conn.executescript(schema)

                cursor=conn.cursor()
                cursor.execute("""
                INSERT  INTO setup (user, podcast_path)
                VALUES ('main', :pod_path)
                """, {'pod_path':podcast_path})
            else:
                cursor=conn.cursor()
                cursor.execute("""
                SELECT podcast_path FROM setup
                """)
                for row in cursor.fetchall():
                    self.podcast_path=row[0]
                    print row[0]
    
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

        #Check if the directory exist
        path=os.path.join(self.podcast_path, title)
        if not os.path.exists(path):
            os.makedirs(path, 0755)
        else :
            print "Warning the path already exist !!!!!!!!!!!!!!!!!"

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
        return last_id


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


    def list_items(self, flux_id):
         with sqlite3.connect(self.db_filename) as conn:
            conn.row_factory = dict_factory
            cursor=conn.cursor()
            cursor.execute("""
            SELECT * FROM item WHERE flux= :flux_id
            ORDER BY id
            """,  {'flux_id':flux_id})
            items=[row for row in cursor.fetchall() ]
            return items


    def print_items(self,flux_id):
        items=self.list_items(flux_id)
        print "id  |  Title * Date"
        for i in items:
            print i['id'], ' | ', i['titre'], " * ", i['item_date'] 


    def remove_item(self, item_id):
        #remove_item_file()
         with sqlite3.connect(self.db_filename) as conn:
            cursor=conn.cursor()
            cursor.execute("""
            DELETE FROM item where id= :item_id
            """, {'item_id':item_id})


    def remove_flux(self, flux_id):
        #remove the directory
        with sqlite3.connect(self.db_filename) as conn:
            cursor=conn.cursor()
            cursor.execute(""" 
            DELETE FROM item where flux= :flux_id
            """, {'flux_id':flux_id})
            cursor.execute(""" 
            DELETE FROM flux where id= :flux_id
            """, {'flux_id':flux_id}) 

    def download_item(self, item_id):
        with sqlite3.connect(self.db_filename) as conn:
            cursor=conn.cursor()
            cursor.execute("""
            SELECT url, flux FROM item where id= :item_id
            """, {'item_id':item_id})
            url, flux_id =  cursor.fetchall()[0]
            
            cursor.execute("""
            SELECT titre FROM flux where id= :flux_id
            """, {'flux_id':flux_id})
            titre_flux, = cursor.fetchall()[0]
            print url
            print "to :"
            path=os.path.join(self.podcast_path,
                              titre_flux,
                              url.split('/')[-1])
            print path            
            downloadFile(url, path)

            cursor.execute("""
            UPDATE item
            SET status=1 
            WHERE id = :item_id
            """, {'item_id'=item_id})
     



def test():
    #pod='http://podcast.college-de-france.fr/xml/histoire.xml'
    pod="PodcastScience"
    w=MPDPodcast(podcast_path="/media/Disque_2/mp3/laurent/Podcast")
    w.add_flux(pod)
    w.print_flux(1)
    w.remove_item(1)    
    #w.remove_flux(1)
    #w.print_items(1)
    print  w.download_item(12)

if __name__ == '__main__':
    test()

    
