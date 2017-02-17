#!/usr/bin/env python2
# -*- mode: python; coding: utf-8 -*-
#
# gunicorn --log-level debug -w 4 -b [::]:8081 --pythonpath ../vector-datasource,../tilequeue tileserver_app:app
#

assert str is not unicode
assert str is bytes

import yaml as _yaml
import os.path as _os_path
import tileserver as _tileserver
#import werkzeug.contrib.profiler as _werkzeug_profiler

_config_path = _os_path.join(
    _os_path.dirname(__file__),
    '..',
    'tileserver',
    'config.yaml',
)

#app = _werkzeug_profiler.ProfilerMiddleware(
#    _tileserver.wsgi_server(_config_path),
#    sort_by=('cumtime', 'ncalls'),
#)
app = _tileserver.wsgi_server(_config_path)
