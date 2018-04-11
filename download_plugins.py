#!/usr/bin/python
# -*- coding: utf-8 -*-

# jimmy.yin5@gmail.com, 2018.04.10

import requests
import hashlib
import os, sys

def rmfile(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)

def hashfile(filepath):
    if not os.path.exists(filepath):
        return ''

    sha1 = hashlib.sha1()
    f = open(filepath, 'rb')
    try:
        sha1.update(f.read())
    finally:
        f.close()
    return sha1.hexdigest()

def run(cmd, quiet=False):
    from subprocess import call
    if quiet:
        ret = call(cmd, shell=True, stdout=subprocess.PIPE)
    else:
        ret = call(cmd, shell=True)
    if ret != 0:
        print "==> Command failed: " + cmd
        print "==> Stopping build."
        sys.exit(1)

def download(bundle):
    filepath = bundle['bundle']
    if hashfile(filepath) == bundle['sha1']:
        return
    else:
        if os.path.exists(filepath):
            os.remove(filepath)
        link = os.path.join(pre, filepath
        print('> Download ' + link)

        cmd = 'wget ' + link)
        run(cmd)
        print ('Checking {0} sha1'.format(filepath), hashfile(filepath) == bundle['sha1'])

pre = 'http://download.sdkbox.com/installer/v1/'

# download & save manifest.json
r = requests.get('http://download.sdkbox.com/installer/v1/manifest.json')
rmfile('manifest.json')
with open('manifest.json', 'w') as the_file:
    the_file.write(r.text)

# download installer
manifest = r.json()
sdkbox_installer = manifest['packages']['SDKBOX']['versions']
download(sdkbox_installer.values()[0])

# download plugins
for name in manifest['packages']:
    print(name)
    if name == 'SDKBOX':
        continue

    package = manifest['packages'][name]
    versions = package['versions'].values()[0]
    download(versions['v2'])
    download(versions['v3'])
    sys.exit(0)

print('> Done.')
