# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

assert str is bytes
assert unicode is not str

from builtins import range
from future.utils import raise_from
import os, os.path
import hashlib
import random
import threading
import time

def os_replace(src, dst):
    '''
    Simple emulation of function `os.replace(..)` from modern version of Python.
    Implementation is not fully atomic, but enough for us
    '''
    
    orig_os_replace_func = getattr(os, 'replace', None)
    
    if orig_os_replace_func is not None:
        # not need for emulation: we using modern version of Python.
        # fully atomic for this case
        
        orig_os_replace_func(src, dst)
        return
    
    if os.name == 'posix':
        # POSIX requirement: `os.rename(..)` works as `os.replace(..)`
        # fully atomic for this case
        
        os.rename(src, dst)
        return
    
    # simple emulation for `os.name == 'nt'` and other marginal operation systems.
    # not fully atomic implementation for this case
    
    try:
        # trying atomic `os.rename(..)` without `os.remove(..)` or other operations
        
        os.rename(src, dst)
        error = None
    except EnvironmentError:
        error = e
    
    if error is None:
        return
    
    for i in range(5):
        # some number of tries may be failed
        # because we may be in concurrent environment with others processes/threads
        
        try:
            os.remove(dst)
        except EnvironmentError:
            # destination was not exist
            # or concurrent process/thread is removing it in parallel with us
            pass
        
        try:
            os.rename(src, dst)
            error = None
        except EnvironmentError as e:
            error = e
            continue
        
        break
    
    if error is not None:
        raise_from(EnvironmentError('failed to replace'), error)

def path_list_to_file_name(path_list):
    assert isinstance(path_list, (tuple, list))
    
    def normalize(name):
        if isinstance(name, unicode):
            return name.\
                    replace(u'[', u'[[').\
                    replace(u']', u']]').\
                    replace(u'.', u'[dot]').\
                    replace(u'/', u'[sl]').\
                    replace(u'\\', u'[bksl]')
        
        if isinstance(name, bytes):
            return normalize(name.decode('utf-8', 'replace'))
        
        return normalize(unicode(name))
    
    name = u'[sep]'.join(normalize(x) for x in path_list)
    
    sha1 = hashlib.new('sha1')
    sha1.update(name.encode('utf-8'))
    
    file_name = u'%s-%s.bin' % (sha1.hexdigest()[:7], name)
    file_dir = os.path.join(*(x for x in (
        file_name[:1],
        file_name[:2],
        file_name[:4],
        file_name[:7],
    )))
    
    return file_dir, file_name

def write_first_cache(cache_dir, cache_path_list, data):
    file_dir, file_name = path_list_to_file_name(cache_path_list)
    file_path = os.path.join(cache_dir, file_dir, file_name)
    
    if data is None:
        try:
            os.remove(file_path)
        except EnvironmentError:
            pass
        
        return
    
    if isinstance(data, unicode):
        data = data.encode('utf-8')
    
    try:
        os.makedirs(cache_dir)
    except EnvironmentError:
        pass
    
    try:
        os.makedirs(os.path.join(cache_dir, file_dir), 0700)
    except EnvironmentError:
        pass
    
    swap_file_path = '%s.swp-%s-%s-%s' % (
        file_path,
        os.getpid(),
        threading.currentThread().ident,
        random.randint(1,1000000),
    )
    
    with open(swap_file_path, 'wb') as fd:
        fd.write(data)
    
    os_replace(swap_file_path, file_path)

def read_first_cache(cache_dir, cache_path_list):
    file_dir, file_name = path_list_to_file_name(cache_path_list)
    file_path = os.path.join(cache_dir, file_dir, file_name)
    
    try:
        with open(file_path, 'rb') as fd:
            age = abs(time.time() - os.fstat(fd.fileno()).st_mtime)
            data = fd.read()
    except EnvironmentError:
        age = None
        data = None
    
    return age, data

def roll_the_dice(refresh_prob, refresh_interval, age):
    assert isinstance(refresh_prob, (int, long, float))
    assert isinstance(refresh_interval, (int, long, float))
    assert isinstance(age, (int, long, float))
    
    return random.random() < \
            min(age / refresh_interval, 1.0) * min(refresh_prob / 100.0, 1.0)
