import codecs

READY = 0
RUNNING = 1
DONE = 2

#not used:
UPLOAD = 10 #processing after upload
DOWNLOAD = 11 #preparing before download

def writestatus(statusfile, statusmessage, encoding = 'utf-8'):
    f = codecs.open(statusfile, 'w', encoding)
    f.write(statusmessage)
    f.close()

