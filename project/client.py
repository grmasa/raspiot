import time
import socket, sys
import raspauth

class client:

    id = raspauth.id
    host = raspauth.HOST
    port = raspauth.PORT
    packet = ''
    version = ''
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __init__(self,ver):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        try :
            self.version = ver
        except :
            print sys.exc_info()[1]
            self.version = '0.0.0'
        
        self.packet = str(self.id)+":"+self.get_local_address()+":"+self.version 
        print 'Connected'
        self.init_packet()
        
    def init_packet(self):
        while True:
            ipadress = self.get_local_address()
            self.packet = str(self.id)+":"+ipadress+":"+self.version
            if ipadress!= '':
                break
      
    def get_local_address(self):
        import socket
        import fcntl
        import struct
        ipaddr=''
        try:
            ifname='eth0'
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ipaddr = socket.inet_ntoa(fcntl.ioctl(s.fileno(),0x8915,struct.pack('256s', ifname[:15]))[20:24])
        except:
            pass
        return ipaddr

    def send_ping(self, string):
        try:
            try:
                new_packet=self.packet+":"+string
                self.s.send(new_packet)
                print new_packet
                time.sleep(3)
            except:
                print sys.exc_info()[1]
                try:
                    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.s.connect((self.host, self.port))
                except:
                    print sys.exc_info()[1]
                    pass
                finally: 
                    try :
                        time.sleep(5)
                    except :
                        print 'Unable to connect'
                        print sys.exc_info()[1]
         
        finally:
            self.s.close()
            pass



