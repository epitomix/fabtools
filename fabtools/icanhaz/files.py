"""
Idempotent API for managing files and directories
"""
import hashlib
import os, os.path
from tempfile import NamedTemporaryFile
from urlparse import urlparse

from fabric.api import *
from fabtools.files import is_file, is_dir, md5sum


def directory(path, use_sudo=False, owner='', group='', mode=''):
    """
    I can haz directory
    """
    func = use_sudo and sudo or run
    if not is_dir(path):
        func('mkdir -p "%(path)s"' % locals())
        if owner:
            func('chown %(owner)s:%(group)s "%(path)s"' % locals())
        if mode:
            func('chmod %(mode)s "%(path)s"' % locals())


def file(path=None, contents=None, source=None, url=None, md5=None, use_sudo=False, owner=None, group='', mode=None):
    """
    I can haz file

    You can provide either:
    - contents: the required contents of the file
    - source: the filename of a local file to upload
    - url: the address of a file to download (path is optional)
    """
    func = use_sudo and sudo or run

    # 1) Only a path is given
    if path and not (contents or source or url):
        assert path
        if not is_file(path):
            func('touch "%(path)s"' % locals())

    # 2) A URL is specified (path is optional)
    elif url:
        if not path:
            path = os.path.basename(urlparse(url).path)

        if not is_file(path) or md5 and md5sum(path) != md5:
            func('wget --progress=dot %(url)s' % locals())

    # 3) A local filename, or a content string, is specified
    else:
        if source:
            assert not contents
            contents = open(source).read()
        else:
            tmp_file = NamedTemporaryFile(delete=False)
            tmp_file.write(contents)
            tmp_file.close()

        if not is_file(path) or md5sum(path) != hashlib.md5(contents).hexdigest():
            with settings(hide('running')):
                if source:
                    put(source, path, use_sudo=use_sudo)
                else:
                    put(tmp_file.name, path, use_sudo=use_sudo)
                    os.remove(tmp_file.name)

    # Ensure correct owner
    if owner:
        func('chown %(owner)s:%(group)s "%(path)s"' % locals())

    # Ensure correct mode
    if mode:
        func('chmod %(mode)s "%(path)s"' % locals())
