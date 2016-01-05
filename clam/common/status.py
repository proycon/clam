from __future__ import print_function, unicode_literals, division, absolute_import

import io
import time
import sys

READY = 0
RUNNING = 1
DONE = 2


def write(statusfile, statusmessage, completion = 0, timestamp = False, encoding = 'utf-8'):
    if statusfile:
        f = io.open(statusfile, 'a', encoding=encoding)
        if not timestamp:
            timestamp = int(time.time())
        if isinstance(completion, float) and completion >= 0.0 and completion <= 1.0:
            completion = int(round(completion * 100))
        if sys.version < '3' and not isinstance(statusmessage, unicode):
            statusmessage = unicode(statusmessage,'utf-8')
        f.write(str(completion) + "%\t" + str(timestamp) + "\t" + statusmessage + "\n")
        f.close()

