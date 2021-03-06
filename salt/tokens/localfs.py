# -*- coding: utf-8 -*-

'''
Stores eauth tokens in the filesystem of the master. Location is configured by the master config option 'token_dir'
'''

from __future__ import absolute_import

import hashlib
import os
import logging

import salt.utils
import salt.payload

log = logging.getLogger(__name__)

__virtualname__ = 'localfs'


def mk_token(opts, tdata):
    '''
    Mint a new token using the config option hash_type and store tdata with 'token' attribute set
    to the token.
    This module uses the hash of random 512 bytes as a token.

    :param opts: Salt master config options
    :param tdata: Token data to be stored with 'token' attirbute of this dict set to the token.
    :returns: tdata with token if successful. Empty dict if failed.
    '''
    hash_type = getattr(hashlib, opts.get('hash_type', 'md5'))
    tok = str(hash_type(os.urandom(512)).hexdigest())
    t_path = os.path.join(opts['token_dir'], tok)
    while os.path.isfile(t_path):
        tok = str(hash_type(os.urandom(512)).hexdigest())
        t_path = os.path.join(opts['token_dir'], tok)
    tdata['token'] = tok
    serial = salt.payload.Serial(opts)
    try:
        with salt.utils.files.set_umask(0o177):
            with salt.utils.files.fopen(t_path, 'w+b') as fp_:
                fp_.write(serial.dumps(tdata))
    except (IOError, OSError):
        log.warning('Authentication failure: can not write token file "{0}".'.format(t_path))
        return {}
    return tdata


def get_token(opts, tok):
    '''
    Fetch the token data from the store.

    :param opts: Salt master config options
    :param tok: Token value to get
    :returns: Token data if successful. Empty dict if failed.
    '''
    t_path = os.path.join(opts['token_dir'], tok)
    if not os.path.isfile(t_path):
        return {}
    serial = salt.payload.Serial(opts)
    try:
        with salt.utils.files.fopen(t_path, 'rb') as fp_:
            tdata = serial.loads(fp_.read())
            return tdata
    except (IOError, OSError):
        log.warning('Authentication failure: can not read token file "{0}".'.format(t_path))
        return {}


def rm_token(opts, tok):
    '''
    Remove token from the store.

    :param opts: Salt master config options
    :param tok: Token to remove
    :returns: Empty dict if successful. None if failed.
    '''
    t_path = os.path.join(opts['token_dir'], tok)
    try:
        os.remove(t_path)
        return {}
    except (IOError, OSError):
        log.warning('Could not remove token {0}'.format(tok))


def list_tokens(opts):
    '''
    List all tokens in the store.

    :param opts: Salt master config options
    :returns: List of dicts (tokens)
    '''
    ret = []
    for (dirpath, dirnames, filenames) in os.walk(opts['token_dir']):
        for token in filenames:
            ret.append(token)
    return ret
