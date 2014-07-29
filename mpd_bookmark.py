from mpd import MPDClient
from select import select
import time, re


class MPDBookmark(object):
    def __init__(self, host="localhost", port=6600, password=None):
        self.client = MPDClient()
        try:
            self.client.connect(host, port)
            if password:
               self.client.password(password) 
            
        except :
            print "merde"
            exit
        self.motif="couleur 3"
        self.field="album"
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
        return re.match(self.motif, song[self.field])

    def boucle(self):
        
        ts=time.time()
        state=self.client.status()['state']
        #sid=self.client.status()['songid']
        song=self.client.currentsong()
        print "\n\n chanson init :", song['title']
        C=True
        while 1 :
            ret=self.wait_action()
            
            new_state=self.client.status()['state']
            new_song=self.client.currentsong()
            new_ts=time.time()
            
            if new_song!=song or  new_state=='stop' :
                print "fin de chanson", song['title'],
                print "( ",int(new_ts-ts),
                print "/",song['time']," )"
                if self.verif_motif(song):
                    last_up=int(new_ts-ts)
                    self.client.sticker_set('song', song['file'], 
                                            'last_up', last_up)
            #else on sort de la pause

            if new_state=='play' :
                if new_song!=song or state=='stop':
                    print "Nouvelle chanson :", new_song['title']
                    if 'last_up' in self.client.sticker_list('song',
                                                        new_song['file']):
                        last_up=int(self.client.sticker_get('song', 
                                                            new_song['file'], 
                                                            'last_up'))
                        if abs(int(new_song['time'])-last_up)<=4 :
                            last_up=0
                        self.client.seekcur(last_up)
                        
                #print "debut de chanson (ou seek)", new_song['title']
                new_ts=time.time()-float( self.client.status()['elapsed'])
            else :
                print "Pause ou stop"

            state= new_state
            song= new_song
            ts=new_ts
            


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
    w=MPDBookmark()
