#This is part of this module for legacy reasons only (older settings files refer to it)

from hashlib import md5

def pwhash(user, realm, password):
    #computes a password hash for a given user and plaintext password (HA1)
    return md5(user.encode('utf-8') + b':' + realm.encode('utf-8') + b':' + password.encode('utf-8')).hexdigest()
