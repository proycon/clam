#This is part of this module for legacy reasons only (older settings files refer to it)

try:
    from hashlib import md5
except ImportError:
    from md5 import new as md5

def pwhash(user, realm, password):
    #computes a password hash for a given user and plaintext password (HA1)
    return md5(user + ':' + realm + ':' + password).hexdigest()
