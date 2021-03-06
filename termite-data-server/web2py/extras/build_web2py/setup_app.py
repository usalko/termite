#!/usr/bin/env .venv/bin/python3
# -*- coding: utf-8 -*-

"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

copy_apps = False
copy_scripts = True
copy_site_packages = True
remove_build_files = True
make_zip = True
zip_filename = "web2py_osx"

from setuptools import setup
from gluon.import_all import base_modules, contributed_modules
from gluon.fileutils import readlines_file
import os
import fnmatch
import shutil
import sys
import re
import zipfile

#read web2py version from VERSION file                                                 
web2py_version_line = readlines_file('VERSION')[0]
#use regular expression to get just the version number                                 
v_re = re.compile('[0-9]+\.[0-9]+\.[0-9]+')
web2py_version = v_re.search(web2py_version_line).group(0)

class reglob:
    def __init__(self, directory, pattern="*"):
        self.stack = [directory]
        self.pattern = pattern
        self.files = []
        self.index = 0

    def __getitem__(self, index):
        while 1:
            try:
                file = self.files[self.index]
                self.index = self.index + 1
            except IndexError:
                self.index = 0
                self.directory = self.stack.pop()
                self.files = os.listdir(self.directory)
            else:
                fullname = os.path.join(self.directory, file)
                if os.path.isdir(fullname) and not os.path.islink(fullname):
                    self.stack.append(fullname)
                if not (file.startswith('.') or file.startswith('#') or file.endswith('~')) \
                        and fnmatch.fnmatch(file, self.pattern):
                    return fullname

setup(app=['web2py.py'],
      version=web2py_version,
      description="web2py web framework",
      author="Massimo DiPierro",
      license="LGPL v3",
      data_files=[
      'NEWINSTALL',
      'ABOUT',
      'LICENSE',
      'VERSION',
      'splashlogo.gif',
      'logging.example.conf',
      'options_std.py',
      ],
      options={'py2app': {
               'argv_emulation': True,
               'includes': base_modules,
               }},
      setup_requires=['py2app'])


def copy_folders(source, destination):
    """Copy files & folders from source to destination (within dist/)"""
    print('copying %s -> %s' % (source, destination))
    base = 'dist/web2py.app/Contents/Resources/'
    if os.path.exists(os.path.join(base, destination)):
        shutil.rmtree(os.path.join(base, destination))
    shutil.copytree(os.path.join(source), os.path.join(base, destination))

#Should we include applications?
copy_folders('gluon','gluon')

if copy_apps:
    copy_folders('applications', 'applications')
    print("Your application(s) have been added")
else:
    #only copy web2py's default applications
    copy_folders('applications/admin', 'applications/admin')
    copy_folders('applications/welcome', 'applications/welcome')
    copy_folders('applications/examples', 'applications/examples')
    print("Only web2py's admin, examples & welcome applications have been added")


#should we copy project's site-packages into dist/site-packages
if copy_site_packages:
    #copy site-packages
    copy_folders('site-packages', 'site-packages')
else:
    #no worries, web2py will create the (empty) folder first run
    print("Skipping site-packages")
    pass

#should we copy project's scripts into dist/scripts
if copy_scripts:
    #copy scripts
    copy_folders('scripts', 'scripts')
else:
    #no worries, web2py will create the (empty) folder first run
    print("Skipping scripts")
    pass


#borrowed from http://bytes.com/topic/python/answers/851018-how-zip-directory-python-using-zipfile
def recursive_zip(zipf, directory, folder=""):
    for item in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, item)):
            zipf.write(os.path.join(directory, item), folder + os.sep + item)
        elif os.path.isdir(os.path.join(directory, item)):
            recursive_zip(
                zipf, os.path.join(directory, item), folder + os.sep + item)

#should we create a zip file of the build?

if make_zip:
    #to keep consistent with how official web2py windows zip file is setup,
    #create a web2py folder & copy dist's files into it
    shutil.copytree('dist', 'zip_temp/web2py')
    #create zip file
    #use filename specified via command line
    zipf = zipfile.ZipFile(
        zip_filename + ".zip", "w", compression=zipfile.ZIP_DEFLATED)
    path = 'zip_temp'  # just temp so the web2py directory is included in our zip file
    recursive_zip(
        zipf, path)  # leave the first folder as None, as path is root.
    zipf.close()
    shutil.rmtree('zip_temp')
    print("Your Windows binary version of web2py can be found in " + \
        zip_filename + ".zip")
    print("You may extract the archive anywhere and then run web2py/web2py.exe")

#should py2exe build files be removed?
if remove_build_files:
    shutil.rmtree('build')
    shutil.rmtree('deposit')
    shutil.rmtree('dist')
    print("py2exe build files removed")

#final info
if not make_zip and not remove_build_files:
    print("Your Windows binary & associated files can also be found in /dist")

print("Finished!")
print("Enjoy web2py " + web2py_version_line)
