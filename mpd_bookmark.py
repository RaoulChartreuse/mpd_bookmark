from mpd import MPDClient
from select import select
import time, re
import argparse


class MPDBookmark(object):
    def __init__(self, host="localhost", port=6600, password=None,
                 motif="Podcast", field="album"):
        self.client = MPDClient()
        try:
            self.client.connect(host, port)
            if password:
               self.client.password(password) 
            
        except :
            print "merde"
            print "host = ", host
            print "port = ", port
            print "pass = ", password
            assert False
        self.motif=motif
        self.field=field
        self.boucle()

    def stats(self):
        print "==========================================="
        print "                Version :"
        print self.client.mpd_version
        print "==========================================="
        print "fin du test"
        print self.client.status()


    def wait_action(self):
        self.client.send_idle('player')
        select([self.client], [], [], 60)
        return self.client.fetch_idle()

    
    def verif_motif(self, song):
        return  self.field in song and re.match(self.motif, song[self.field])

    
    def update_song(self, song, ts):
        new_ts=time.time()
        if 'title' in song :
            print "Update song : ", song['title'],
            print "( ",int(new_ts-ts),
            print "/",song['time']," )"
        if self.verif_motif(song):
            last_up=int(new_ts-ts)
            self.client.sticker_set('song', song['file'], 
                                    'last_up', last_up)
    
    def start_song(self, new_song):
        if ('file' in new_song) and 'last_up' in self.client.sticker_list('song', new_song['file']):
            last_up=int(self.client.sticker_get('song', 
                                                new_song['file'], 
                                                'last_up'))
            if abs(int(new_song['time'])-last_up)<=4 :
                last_up=0
            self.client.seekcur(last_up)


    def boucle(self):
        
        ts=time.time()
        state=self.client.status()['state']
        song=self.client.currentsong()
        print "song  :  ", song

        if 'elapsed' in song :
            ts-=float( song['elapsed'])

        while 1 :
            ret=self.wait_action()
            new_state=self.client.status()['state']
            new_song=self.client.currentsong()

            if new_song!=song and new_song!={}:
                self.start_song(new_song)

            state= new_state
            song= new_song
            if 'elapsed' in self.client.status():
                ts=time.time()-float( self.client.status()['elapsed'])
            if song !={}:
                print "update  ",
                self.update_song(song, ts)


#Pour les tests
def select_N_song(client, N=3):
    """On supose que le client est conecter"""
    tmp=client.listall('')
    i=0
    ret=[]
    for s in tmp:
        if 'file' in s:
            i+=1
            ret.append(s)
            if i>=N:
                break
    return ret
    



if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='MPD Bookmark is a simple script witch monitor MPD and keep a trace of where the listening of a file ended.')
    parser.add_argument('-f','--field', 
                        help='A field either song, file or any tag', 
                        default='album')
    parser.add_argument('-m','--motif', help='A regular expression', 
                        default='Podcast')
    parser.add_argument('-i','--host', help='Host of MPD', default='localhost')
    parser.add_argument('-p','--port', help='Port of MPD', default='6600')
    parser.add_argument('-pw','--password', help='Password of MPD', 
                        default=None)
    args=parser.parse_args()
    
    w=MPDBookmark(host=args.host,
                  port=args.port,
                  password=args.password,
                  motif=args.motif,
                  field=args.field)
