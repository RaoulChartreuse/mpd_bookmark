#Test made to be used with nose :
#nosetest 
#if you have trouble to close nose :
#ps -aux | grep nose | grep python | awk '{print $2}' |  xargs kill -9
from mpd_bookmark import MPDBookmark
import threading, time
from mpd import MPDClient

class TestBookmark:
    
    def __init__(self):
        #Fill there
        self.testHost="localhost"
        self.testPort=6600
        self.testPass=None
        self.testMotif=""
        self.testField="file"
        #Test songs must last more than 30s
        self.song1="Jacques Brel/Album/11-Vierson.mp3"
        self.song2="Cream/Cream - 2000 - The Millenium Collection - [V2]/07 - Tales Of Brave Ulysses.mp3"

    #Before every test
    def setup(self):
        print "Connection to MPD .........",
        self.client=MPDClient()
        self.client.connect(self.testHost,self.testPort)
        if self.testPass:
            self.client.password(self.testPass)
        print "Done"
        self.client.clear()
        self.volume=self.client.status()['volume']
        self.client.setvol(0)
        self.client.consume(0)
        self.client.sticker_set('song', self.song1, 
                                'last_up', 0)
        self.client.sticker_set('song', self.song2, 
                                'last_up', 0)
        self.launch_bookmark()


    #After every test
    def teardown(self):
        self.client.clear()
        self.client.setvol(self.volume)
        print "Disconect MPD .............",
        self.client.disconnect() 
        print "Done"
        self.kill_bookmark()
       

    def launch_bookmark(self):
        self._thread=threading.Thread(None, MPDBookmark, None, (),
                                      {'host':self.testHost,
                                       'port':self.testPort,
                                       'password':self.testPass,
                                       'motif':self.testMotif,
                                       'field':self.testField})
        self._thread.start()
        print "Launch done"

    def kill_bookmark(self):
        self._thread._Thread__stop()
        print "kill done"

    def test_Version(self):
        print "Version :    ",
        print self.client.mpd_version
        #assert self.client.mpd_version=='0.18.0'
 
        
    def test_cold_start(self):
        print "cold start"
        self.client.add(self.song1)
        Ti=time.time()
        self.client.play()
        time.sleep(6)
        self.client.pause()
        Tf=time.time()
        time.sleep(2)#Wait a bit the writing in MPD sticker
        read_time=int(self.client.sticker_get('song',  self.song1, 'last_up'))
        real_time=Tf-Ti
        print "abs(read_time-real_time) ",
        print "read time :", read_time,
        print "real time :", real_time,
        print "  = ",abs(read_time-real_time)
        assert abs(read_time-6)<=2.
        assert abs(read_time-real_time)<=2.



    def test_pause(self):
        p1=5
        p2=2
        print "pause"
        self.client.add(self.song1)
        self.client.play()
        time.sleep(p1)
        self.client.pause()
        time.sleep(2)
        self.client.play()
        time.sleep(p2)
        self.client.stop()
        time.sleep(2)#Wait a bit the writing in MPD sticker
        read_time=int(self.client.sticker_get('song',  self.song1, 'last_up'))
        print read_time, "vs", p1+p2
        assert abs(read_time-(p1+p2))<=2.

       
    def test_seek(self):
        seek=30
        delta=5
        print "Seek"
        self.client.add(self.song1)

        self.client.play()
        time.sleep(2)#If not the next command will not be executed
        self.client.seekcur(seek)
        time.sleep(0.2)#If not the next command will not be executed
        self.client.pause()
        time.sleep(2)#Wait a bit the writing in MPD sticker
        print self.client.status()
        read_time=int(self.client.sticker_get('song', self.song1, 'last_up'))
        print read_time, "vs", seek
        print "sticker ", self.client.sticker_get('song', self.song1, 'last_up')
        assert abs(read_time- seek)<=2.

        self.client.play()
        time.sleep(0.2)#If not the next command will not be executed
        self.client.seekcur("+"+str(delta))
        self.client.pause()
        time.sleep(2)#Wait a bit the writing in MPD sticker
        read_time=int(self.client.sticker_get('song', self.song1, 'last_up'))
        print read_time, "vs", seek+delta
        assert abs(read_time- seek-delta)<=2.
        
        self.client.play()
        time.sleep(0.5)#If not the next command will not be executed
        self.client.seekcur("-"+str(2*delta))
        self.client.pause()
        time.sleep(2)#Wait a bit the writing in MPD sticker
        read_time=int(self.client.sticker_get('song', self.song1, 'last_up'))
        print read_time, "vs", seek-delta
        assert abs(read_time- seek+delta)<=2.

        
    
    def test_next(self):
        seek=30
        print "-- Next --"

        self.client.add(self.song1)
        self.client.add(self.song2)

        self.client.play()
        time.sleep(2)#If not the next command will not be executed
        self.client.seekcur(seek)
        time.sleep(0.2)#If not the next command will not be executed
        self.client.next()
        self.client.pause()
        time.sleep(2)#Wait a bit the writing in MPD sticker
        self.client.play()
        read_time=int(self.client.sticker_get('song', self.song1, 'last_up'))
        print read_time, 'vs', seek
        assert abs(read_time- seek)<=2.
        time.sleep(2)#If not the next command will not be executed
        self.client.seekcur(seek)
        time.sleep(0.2)#If not the next command will not be executed
        self.client.previous()
        time.sleep(0.2)#If not the next command will not be executed
        self.client.pause()
        time.sleep(2)#Wait a bit the writing in MPD sticker
        read_time=int(self.client.sticker_get('song', self.song2, 'last_up'))
        print read_time, 'vs', seek
        assert abs(read_time- seek)<=2.


    def test_clear(self):
        print "-- Clear --"
        wait=5
        self.client.add(self.song1)
        self.client.play()
        time.sleep(wait)#If not the next command will not be executed
        self.client.clear()
        time.sleep(2)#Wait a bit the writing in MPD sticker
        read_time=int(self.client.sticker_get('song', self.song1, 'last_up'))
        print read_time, 'vs', wait
        assert abs(read_time- wait)<=2.
        

