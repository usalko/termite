import struct
import uuid
import random
import time
import os
import pickle
import zlib
import threading
import hmac
import base64
import logging
from hashlib import md5, sha1, sha224, sha256, sha384, sha512

try:
    from Crypto.Cipher import AES
except ImportError:
    import gluon.contrib.aes as AES


_struct_2_long_long = struct.Struct('=QQ')

logger = logging.getLogger("web2py")


def initialize_urandom():
    """
    This function and the web2py_uuid follow from the following discussion:
    http://groups.google.com/group/web2py-developers/browse_thread/thread/7fd5789a7da3f09

    At startup web2py compute a unique ID that identifies the machine by adding
    uuid.getnode() + int(time.time() * 1e3)

    This is a 48-bit number. It converts the number into 16 8-bit tokens.
    It uses this value to initialize the entropy source ('/dev/urandom') and to seed random.

    If os.random() is not supported, it falls back to using random and issues a warning.
    """
    node_id = uuid.getnode()
    microseconds = int(time.time() * 1e6)
    ctokens = [((node_id + microseconds) >> ((i % 6) * 8)) %
               256 for i in range(16)]
    random.seed(node_id + microseconds)
    try:
        os.urandom(1)
        have_urandom = True
        try:
            # try to add process-specific entropy
            frandom = open('/dev/urandom', 'wb')
            try:
                frandom.write(bytes([]).join(bytes([t])
                                             for t in ctokens))  # python 3
            finally:
                frandom.close()
        except IOError:
            # works anyway
            pass
    except NotImplementedError:
        have_urandom = False
        logger.warning(
            """Cryptographically secure session management is not possible on your system because
your system does not provide a cryptographically secure entropy source.
This is not specific to web2py; consider deploying on a different operating system.""")

    packed = bytes([]).join(bytes([x]) for x in ctokens)  # python 3
    unpacked_ctokens = _struct_2_long_long.unpack(packed)
    return unpacked_ctokens, have_urandom


UNPACKED_CTOKENS, HAVE_URANDOM = initialize_urandom()


def pad(s, n=32, padchar=' '):
    return s + (32 - len(s) % 32) * padchar


def AES_new(key, IV=None):
    """ Returns an AES cipher object and random IV if None specified """
    if IV is None:
        IV = fast_urandom16()

    return AES.new(key, AES.MODE_CBC, IV), IV


def fast_urandom16(urandom=[], locker=threading.RLock()):
    """
    this is 4x faster than calling os.urandom(16) and prevents
    the "too many files open" issue with concurrent access to os.urandom()
    """
    try:
        return urandom.pop()
    except IndexError:
        try:
            locker.acquire()
            ur = os.urandom(16 * 1024)
            urandom += [ur[i:i + 16] for i in range(16, 1024 * 16, 16)]
            return ur[0:16]
        finally:
            locker.release()


def web2py_uuid(ctokens=UNPACKED_CTOKENS):
    """
    This function follows from the following discussion:
    http://groups.google.com/group/web2py-developers/browse_thread/thread/7fd5789a7da3f09

    It works like uuid.uuid4 except that tries to use os.urandom() if possible
    and it XORs the output with the tokens uniquely associated with this machine.
    """
    rand_longs = (random.getrandbits(64), random.getrandbits(64))
    if HAVE_URANDOM:
        urand_longs = _struct_2_long_long.unpack(fast_urandom16())
        byte_s = _struct_2_long_long.pack(rand_longs[0] ^ urand_longs[0] ^ ctokens[0],
                                          rand_longs[1] ^ urand_longs[1] ^ ctokens[1])
    else:
        byte_s = _struct_2_long_long.pack(rand_longs[0] ^ ctokens[0],
                                          rand_longs[1] ^ ctokens[1])
    return str(uuid.UUID(bytes=byte_s, version=4))


def compare(a, b):
    """ compares two strings and not vulnerable to timing attacks """
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0


def secure_dumps(data, encryption_key, hash_key=None, compression_level=None):
    if not hash_key:
        hash_key = sha1(encryption_key).hexdigest()
    dump = pickle.dumps(data)
    if compression_level:
        dump = zlib.compress(dump, compression_level)
    key = pad(encryption_key[:32])
    cipher, IV = AES_new(key)
    encrypted_data = base64.urlsafe_b64encode(IV + cipher.encrypt(pad(dump)))
    signature = hmac.new(hash_key, encrypted_data).hexdigest()
    return signature + ':' + encrypted_data


def secure_loads(data, encryption_key, hash_key=None, compression_level=None):
    if not ':' in data:
        return None
    if not hash_key:
        hash_key = sha1(encryption_key).hexdigest()
    signature, encrypted_data = data.split(':', 1)
    actual_signature = hmac.new(hash_key, encrypted_data).hexdigest()
    if not compare(signature, actual_signature):
        return None
    key = pad(encryption_key[:32])
    encrypted_data = base64.urlsafe_b64decode(encrypted_data)
    IV, encrypted_data = encrypted_data[:16], encrypted_data[16:]
    cipher, _ = AES_new(key, IV=IV)
    try:
        data = cipher.decrypt(encrypted_data)
        data = data.rstrip(' ')
        if compression_level:
            data = zlib.decompress(data)
        return pickle.loads(data)
    except Exception as e:
        return None
