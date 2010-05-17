import codecs
import time

READY = 0
RUNNING = 1
DONE = 2

#not used:
UPLOAD = 10 #processing after upload
DOWNLOAD = 11 #preparing before download

def write(statusfile, statusmessage, completion = 0, timestamp = False, encoding = 'utf-8'):
    f = codecs.open(statusfile, 'a', encoding)
    if not timestamp:
        timestamp = int(time.time())
    f.write(str(completion) + "\t" + str(timestamp) + "\t" + statusmessage + "\n")
    f.close()

