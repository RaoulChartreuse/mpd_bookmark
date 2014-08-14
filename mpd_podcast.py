import os
import sqlite3
import feedparser
from time import strftime, strptime, localtime
import urllib,sys
from mpd import MPDClient


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
                 podcast_path = None,
                 host='localhost',
                 port=6600,
                 password=None):
        #Database setup
        db_is_new= not os.path.exists(db_filename)
        self.db_filename = db_filename
        self.podcast_path = podcast_path
        self.host=host
        self.port=port
        self.password=password

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
                INSERT  INTO setup (user, podcast_path, mpd_host, mpd_port, password)
                VALUES ('main', :pod_path, :mpd_host, :mpd_port, \':passw\')
                """, {'pod_path':podcast_path,
                      'mpd_host':host,
                      'mpd_port':port,
                      'passw':password})
            else:
                cursor=conn.cursor()
                cursor.execute("""
                SELECT podcast_path, mpd_host, mpd_port, password
                FROM setup
                """)
                #TODO rajouter une procedure d'update
                for row in cursor.fetchall():
                    self.podcast_path, self.host, self.port, self.password = row[0]
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
                            INSERT INTO item (titre, url, status, item_date, flux, nom)
                            VALUES ( :title, :url, :status, :item_date , :flux_id, '')
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


    def __delete_item(self,item_id):
        with sqlite3.connect(self.db_filename) as conn:
            cursor=conn.cursor()
            cursor.execute(""" 
            SELECT flux.titre, item.nom, item.status
            FROM  flux, item 
            WHERE item.id= :item_id;
            """, {'item_id':item_id})

            #Suppression physique
            titre_flux, nom, status = cursor.fetchall()[0]
            if status!=0 :
                path=os.path.join(self.podcast_path, titre_flux, nom)
                assert os.path.exists(path)
                #TODO Add here a confirmation 
                os.remove(path)


    def remove_item(self, item_id):
        """Remove the item from the DB and the filesystem"""
        self.__delete_item(item_id)
        with sqlite3.connect(self.db_filename) as conn:
            cursor=conn.cursor()
            cursor.execute("""
            DELETE FROM item where id= :item_id
            """, {'item_id':item_id})


    def remove_dowloaded_item(self, item_id):
        """Remove the item from the filesystem, i.e. the dowloaded"""
        self.__delete_item(item_id)
        with sqlite3.connect(self.db_filename) as conn:
            cursor=conn.cursor()
            cursor.execute("""
            UPDATE item
            SET status=0
            WHERE id = :item_id
            """,{'item_id':item_id})


    def remove_flux(self, flux_id):
        with sqlite3.connect(self.db_filename) as conn:
            cursor=conn.cursor()
            #Suprimer les items
            cursor.execute(""" 
            SELECT flux.titre, item.nom
            FROM flux, item
            WHERE item.id = :flux_id
            """, {'flux_id':flux_id})
            for row in cursor.fetchall():
                titre_flux, nom, status = row
                if status==0:
                    path=os.path.join(self.podcast_path, titre_flux, nom)
                    assert os.path.exists(path)
                    #TODO Add here a confirmation 
                    os.remove(path)
            os.removedirs(os.path.join(self.podcast_path, titre_flux))

            cursor.execute(""" 
            DELETE FROM item where flux= :flux_id
            """, {'flux_id':flux_id})
            cursor.execute(""" 
            DELETE FROM flux where id= :flux_id
            """, {'flux_id':flux_id}) 


    def download_item(self, item_id, name=None):
        with sqlite3.connect(self.db_filename) as conn:
            cursor=conn.cursor()
            cursor.execute("""
            SELECT item.url, item.flux, flux.titre, item.nom
            FROM item, flux where item.id= :item_id
            """, {'item_id':item_id})
            url, flux_id, titre_flux, nom =  cursor.fetchall()[0]
            if name==None:
                if nom!='':
                    name=nom
                else :
                    name=url.split('/')[-1]
            
            print url
            print "to :"
            path=os.path.join(self.podcast_path,
                              titre_flux,
                              name)
            print path            
            downloadFile(url, path)

            cursor.execute("""
            UPDATE item
            SET status=1 , nom= :name
            WHERE id = :item_id
            """, {'item_id':item_id, 'name':name})
            return path
     

    def check_item(self):
        with sqlite3.connect(self.db_filename) as conn:
            cursor=conn.cursor()
            cursor.execute(""" 
            SELECT item.id, flux.titre, item.url, item.nom 
            FROM  flux, item 
            WHERE item.status=1;
            """)
            
            for row in cursor.fetchall():
                item_id, titre_flux, url, nom=row
                path=os.path.join(titre_flux, nom)
                if self.is_readed(path):
                    cursor.execute("""
                    UPDATE item
                    SET status=2
                    WHERE id = :item_id
                    """,{'item_id':item_id})


    def is_readed(self, path):
        client=MPDClient()
        client.connect(self.host, self.port)
        if self.password:     
            client.password(self.password) 
        song,=client.search('file', path)
        print song
        if 'last_up' in client.sticker_list('song', song['file']) :
            last_up = client.sticker_get('song', song['file'], 'last_up')
            if abs(int(song['time'])-int(last_up))<=4 :
                client.close()
                return True
        client.close()
        return False



def test():
    #pod='http://podcast.college-de-france.fr/xml/histoire.xml'
    pod="http://radiofrance-podcast.net/podcast09/rss_11074.xml"
    w=MPDPodcast(podcast_path="/media/Disque_2/mp3/laurent/Podcast")
    w.add_flux(pod)
    w.print_flux(1)
    w.remove_item(1)    
    #w.remove_flux(1)
    #w.print_items(1)
    path=w.download_item(3)
    
    #Made the item readed
    path=path.split("/")[-2:]
    path=os.path.join(path[0], path[1])
    client=MPDClient()
    client.connect('localhost', 6600)
    song,=client.search('file', path)
    client.sticker_set('song', song['file'], 'last_up',int(song['time']))
    w.check_item()
    w.remove_dowloaded_item(3)
    w.remove_item(4)


if __name__ == '__main__':
    test()

    
