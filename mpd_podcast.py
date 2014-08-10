import os
import sqlite3

class MPDPodcast(object):
    def __init__(self, 
                 db_filename = 'mpd_podcast.db' ,
                 schema_filename = 'mpd_podcast_schema.sql'):
        db_is_new= not os.path.exists(db_filename)
        self.db_filename = db_filename
        with sqlite3.connect(db_filename) as conn:
            if db_is_new:
                print 'Database creation'
                with open(schema_filename, 'rt') as f:
                    schema= f.read()
                conn.executescript(schema)
    
    


if __name__ == '__main__':
    w=MPDPodcast()
