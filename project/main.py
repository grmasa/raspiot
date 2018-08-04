# -*- coding: utf-8 -*-
ver = '0.8.4.NP'
import time
import email
import socket
import ssl
import imaplib
import sys
import RPi.GPIO as GPIO
import string
import threading
import datetime
from time import localtime, strftime
import subprocess
import shlex

import raspauth
from client import client
c = client(ver)

subprocess.call(shlex.split('tvservice -o'))

def write_error (string) :
    with open("/home/pi/Documents/error.log","a+") as f:
        f.write("\n"+str(datetime.datetime.now())+" "+string)

def write_use (string) :
    with open("/home/pi/Documents/email.log","a+") as f:
        f.write("\n"+str(datetime.datetime.now())+" "+string)

#ping control		
var_ping = 0

def send_ping_thread():
    global var_ping
	#ping the server if there is no error
    if var_ping==1:
        c.send_ping('ok')   
    threading.Timer(3, send_ping_thread).start() 
thread_send_ping_thread = threading.Thread(target = send_ping_thread)
thread_send_ping_thread.start()
            
def update_main_prog():
    import requests,zipfile,StringIO
    from distutils.version import LooseVersion, StrictVersion
    global ver
    try:
	    
        r = requests.get('https://update.domain/panel/update.php?printer=no')
        server_version = r.text
        print server_version
        if server_version[-1:]=='F':
            if ver[-1:]!='F':
                ver='0.0.0'
        if LooseVersion(server_version) > LooseVersion(ver):
            while True:
                try:
                    r = requests.get('http://update.domain/update/no_printer_py-'+server_version+'-.zip', stream=True) 
                    z = zipfile.ZipFile(StringIO.StringIO(r.content))
                    z.extractall("/usr/")
                    
                    print 'updated'
                    time.sleep(1)
                    try:
                        import os
                        os.remove("/home/pi/Desktop/error.log")
                    except:
                        write_error('error removing log')
                        pass
                    subprocess.call(shlex.split('reboot'))
                    break
                except:
                    write_error('error with zip file')
                    write_error(str(sys.exc_info()[1]))
                    time.sleep(10)
        else:
            print 'no update available'
    except:
        print sys.exc_info()[1]
        write_error('error updating')
        print 'error updating'
        write_error(str(sys.exc_info()[1]))
            
def check_time():
    if strftime("%H:%M:%S", localtime()) == "06:22:15":
        update_main_prog()
        write_error ("6am reboot")
        subprocess.call(shlex.split('reboot'))
    threading.Timer(1, check_time).start()  
    
thread_check_time = threading.Thread(target = check_time)
thread_check_time.start()

#circ parameters
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GREEN_LED = 4
Internet_led = 27
Flash_led =22
button_red = 17
GPIO.setup(Flash_led, GPIO.OUT)
GPIO.setup(Internet_led, GPIO.OUT)
GPIO.setup(button_red, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GREEN_LED, GPIO.OUT)

def error_tone():
    GPIO.output(GREEN_LED, True)
    time.sleep(0.1)
    GPIO.output(GREEN_LED, False)
    time.sleep(0.1)
    GPIO.output(GREEN_LED, True)
    time.sleep(0.1)
    GPIO.output(GREEN_LED, False)

def check_connectivity():
    try:
        socket.gethostbyname('google.com') 
        GPIO.output(Internet_led, True)
    except:
        try:
            GPIO.output(Internet_led, False)
        except:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(Internet_led, GPIO.OUT)
            GPIO.output(Internet_led, False)
        print "No internet"
    threading.Timer(5, check_connectivity).start()

def timeDiff(time1):
    from time import localtime, strftime
    timeA = datetime.datetime.strptime(time1, "%H:%M:%S")
    timeB = datetime.datetime.strptime(strftime("%H:%M:%S", localtime()), "%H:%M:%S")
    newTime = timeB - timeA
    if newTime.seconds>160:
        return 4
    return newTime.seconds/60


def get_decoded_email_body(message_body):
    msg = email.message_from_string(message_body)
    text = ""
    if msg.is_multipart():
        html = None
        for part in msg.get_payload():
            if part.get_content_charset() is None:
                text = part.get_payload(decode=True)
                continue
            charset = part.get_content_charset()
            if part.get_content_type() == 'text/plain':
                text = unicode(part.get_payload(decode=True), str(charset), "ignore").encode('utf8', 'replace')

            if part.get_content_type() == 'text/html':
                html = unicode(part.get_payload(decode=True), str(charset), "ignore").encode('utf8', 'replace')
        if text is not None:
            return text.strip()
        else:
            return html.strip()
    else:
        text = unicode(msg.get_payload(decode=True), msg.get_content_charset(), 'ignore').encode('utf8', 'replace')
        return text.strip()            

thread_check_connectivity = threading.Thread(target = check_connectivity)
thread_check_connectivity.start()

emails = []

#init main
if __name__ == '__main__':
    while True:
        try:
            print 'out loop'
            server = imaplib.IMAP4_SSL(raspauth.HOSTNAME)
            server.login(raspauth.USERNAME, raspauth.PASSWORD)
            server.select(raspauth.MAILBOX)
            while True:  
                flag_beep = 0
                emails = []
                del emails[:]
                time.sleep(0.5)
                print 'loop'

                try:
                    server = imaplib.IMAP4_SSL(raspauth.HOSTNAME)
                    server.login(raspauth.USERNAME, raspauth.PASSWORD)
                    server.select(raspauth.MAILBOX)
                    print 'server connected'
                except:
                    #handle connection error
                    print sys.exc_info()[1]
                    write_error(str(sys.exc_info()[1]))
                    import  os
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    print(exc_type,  exc_tb.tb_lineno)
                    write_error(str(exc_type) +" "+  str(exc_tb.tb_lineno))
                try:
                    msss=''
                    retcode =''
                    messages =''
                    try:
                        (retcode, messages) = server.search("utf-8", "(UNSEEN)".encode("utf-8"))        
                    except:
                        pass
                    if retcode == 'OK':
                        if messages[0]!='':
                            print str(len(messages))+' New messages'
                            write_use('<----------------------------------------------------->')
                            write_use('Email Received')
                            for num in messages[0].split(' '):
                                GPIO.output(Flash_led, True)
                                print 'Processing :', messages
                                msss2 = ''
                                data = ''
                                try:
                                    typ, data = server.fetch(num,'(RFC822)')
                                    #GPIO.output(GREEN_LED, True)
                                    msss = get_decoded_email_body((data[0][1]))
                                    msss2 = string.split(msss, '\n')
                                except:
                                    GPIO.output(GREEN_LED, False)
                                    print sys.exc_info()[1]
                                    write_error(str(sys.exc_info()[1]))

                                num_of_messages = 0
                                for rowz in msss2:
                                    if rowz.find("Η/Μ: ") == -1:  
                                        pass
                                    else:
                                        time_str = rowz[-9:-1]
                                        print time_str
                                        if int(timeDiff(time_str))>3:
                                            print 'canceled'
                                            write_use('Old email >3 minutes')
                                            flag_beep = 0
                                            GPIO.output(GREEN_LED, False)
                                            GPIO.output(Flash_led, False)
                                            time.sleep(3)
                                            del emails[:]
                                            break
                                        else:
                                            for i in range(len(emails)):
                                                write_use('Received email id: '+str(rowz_split[2]))
                                            
                                        rowz_split = rowz.split(' ')
                                        emails.insert(num_of_messages, rowz_split[2])
                                        num_of_messages=num_of_messages+1
                                        flag_beep = 1
                                    
                                write_use('Email Processed')
                                print 'email Done!'
                        else:
                            pass
                            print 'No new messages'
                        GPIO.output(Flash_led, False)
                        if flag_beep == 1:
                            start = time.time()
                            GPIO.output(GREEN_LED, True)
                            var_ping=1
                            write_use('Buzzer start')
                            while True:
                                num_of_messages = 0
                                input_state = GPIO.input(button_red) 
                                if int(time.time() - start)>170:
                                    print 'timed out'
                                    write_use('Time out')
                                    GPIO.output(GREEN_LED, False)
                                    flag_beep = 0
                                    del emails[:]
                                    break
                                if input_state == True:
                                    print 'pressed'
                                    write_use('Button pressed')
                                    GPIO.output(GREEN_LED, False)
                                    flag_beep = 0
                                    										
                                    del emails[:]
                                    break
                            var_ping=0
                    
                except Exception as e:
                    var_ping=0
                    del emails[:]
                    GPIO.output(GREEN_LED, False)
                    write_error(str(sys.exc_info()[1]))
                    print sys.exc_info()[1]
                    server.logout()
                    import  os
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    print(exc_type,  exc_tb.tb_lineno)
                    write_error(str(exc_type) +" "+  str(exc_tb.tb_lineno))
        except:
            var_ping=0
            try:
                import  os
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print(exc_type,  exc_tb.tb_lineno)
                write_error(str(exc_type) +" "+  str(exc_tb.tb_lineno))
            except:
                pass
        subprocess.call(shlex.split('reboot'))
    GPIO.cleanup()
