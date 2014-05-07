#!/usr/bin/env python
# PyBBIO setup script

import sys, os, shutil

# detect platform:
PLATFORM = ''
with open('/proc/cpuinfo', 'rb') as f:
  cpuinfo = f.read().lower() 
if ('armv7' in cpuinfo and 
    ('am335x' in cpuinfo or 'am33xx' in cpuinfo)):
  PLATFORM = 'BeagleBone'

  import commands
  uname_status, uname = commands.getstatusoutput('uname -a')
  if uname_status > 0:
    exit('uname failed, cannot detect kernel version! uname output:\n %s' % uname)
  if ('3.2' in uname):
    PLATFORM += ' 3.2'
  else:
    PLATFORM += ' >=3.8'

assert PLATFORM, "Could not detect a supported platform, aborting!"

TASK = ''
if len(sys.argv) > 1:
  if sys.argv[1] == 'install':
    TASK = 'install'
  if sys.argv[0] == '-c':
    # happens when called by pip
    if len(sys.argv) > 2 and sys.argv[1] == 'develop':
      # pip is installing the package
      TASK = 'install'

def preinstall():

  # Check for device tree compiler:
  from distutils import spawn
  assert spawn.find_executable('dtc'), "dtc not installed, aborting!"

  # Earlier versions of PyBBIO used a shell script to install the 
  # bbio module, and it was put in a different directory than this 
  # script will install it. The old install directory is before the 
  # new in the Python search path, so we have to make sure to remove
  # the old install if it is there:
  old_install = ("/usr/lib/python2.7/bbio.py", 
                 "/usr/lib/python2.7/bbio.pyo")
  removed_old_install = False
  for f in old_install:
    if os.path.exists(f):
      try:
        os.remove(f)
        removed_old_install = True
      except Exception as e:
        print ("**Error!**\nAn old PyBBIO install was found at %s\nbut could"+\
              " not be removed. Exception raised:\n%s\nAborting install.") %\
              (f, e)
        sys.exit(0)
  if (removed_old_install):
    print \
"""
An old installation of PyBBIO was removed, but its config file was
preserved in ~/.pybbio/, in case any local customizations were made.
If you have no need to save the old config file you can delete the
entire ~/.pybbio/ directory, as all configuration is now contained 
in the bbio package.
"""


  # Through version 0.5 distutils was used to install PyBBIO instead of 
  # setuptools, and PyBBIO was installed into a different directory. This
  # test looks for all the possible distutils install directories. If an
  # old distutils install is found, the user is notified that it should be 
  # removed and isntall is aborted:
  possible_old_install_paths = ["/usr/local/lib/python2.7/dist-packages/",
                                "/usr/local/lib/python2.7/site-packages/",
                                "/usr/lib/python2.7/site-packages/",
                                "/usr/lib/python2.7/dist-packages/"]
  for p in possible_old_install_paths:
    if os.path.exists(p + "bbio"):
      print \
""" 
An old installation of PyBBIO was found which must be removed manually 
before installation can continue. Remove old install with:
  # rm -rf %sbbio
  # rm -rf %sPyBBIO*
Then run the setup.py script again.
""" % (p, p)
      sys.exit(0)

  # Some Angstrom images are missing the py_compile module; get it if not
  # present:
  import random
  python_lib_path = random.__file__.split('random')[0]
  if not os.path.exists(python_lib_path + 'py_compile.py'):
    print "py_compile module missing; installing to %spy_compile.py" %\
                                                            python_lib_path
    import urllib2
    url = "http://hg.python.org/cpython/raw-file/4ebe1ede981e/Lib/py_compile.py"
    py_compile = urllib2.urlopen(url)
    with open(python_lib_path+'py_compile.py', 'w') as f:
      f.write(py_compile.read())
    print "testing py_compile..."
    try:
      import py_compile
      print "py_compile installed successfully"
    except Exception, e:
      print "*py_compile install failed, could not import"
      print "*Exception raised:"
      raise e

  # List of directories by relative path to copy to /usr/local/lib/PyBBIO/:
  dirs_to_copy = [
    'libraries',
    'examples'
  ]

  for d in dirs_to_copy:
    # Copy the libraries directory to /usr/local/lib:
    dst = '/usr/local/lib/PyBBIO/%s' % d
    src = os.path.join(os.getcwd(), d)
    if os.path.exists(dst):
      print "Found old PyBBIO '%s' directory, replacing" % d
      shutil.rmtree(dst)
    shutil.copytree(src, dst)


if TASK == 'install':
  preinstall()
  print "Installing PyBBIO..." 

from setuptools import setup, Extension

warnings = []

driver_extensions = []
driver_packages = []
driver_package_dirs = {}
driver_data = []

install_requires = [
  'pyserial',
  'smbus'
]
    
if 'BeagleBone' in PLATFORM:
  # 3.2 and 3.8, list common things:
  driver_packages += ['bbio.platform.beaglebone']
  driver_extensions += [Extension('bbio.platform.beaglebone.driver', 
                                  ['bbio/platform/beaglebone/src/beaglebone.c', 
                                   'bbio/platform/util/mmap_util.c'],
                                  include_dirs=['bbio/platform/util'])]

  driver_data += [('bbio/platform', ['bbio/platform/beaglebone/api.py'])
]
  driver_package_dirs['bbio.platform.'] = 'bbio/platform/beaglebone/'

if (PLATFORM == 'BeagleBone >=3.8'):
  # BeagleBone or BeagleBone Black with kernel >= 3.8  

  


  driver_data += [('bbio/platform/beaglebone', 
                   ['bbio/platform/beaglebone/3.8/config.py',
                    'bbio/platform/beaglebone/3.8/pinmux.py',
                    'bbio/platform/beaglebone/3.8/adc.py',
                    'bbio/platform/beaglebone/3.8/pwm.py',
                    'bbio/platform/beaglebone/3.8/cape_manager.py',
                    'bbio/platform/beaglebone/3.8/uart.py',
                    'bbio/platform/beaglebone/3.8/i2c_setup.py'])]

  if TASK == 'install':
    os.system('python tools/install-bb-overlays.py')

elif (PLATFORM == 'BeagleBone 3.2'):
  # BeagleBone or BeagleBone Black with kernel < 3.8 (probably 3.2)
  driver_data += [('bbio/platform/beaglebone', 
                   ['bbio/platform/beaglebone/3.2/config.py', 
                    'bbio/platform/beaglebone/3.2/pinmux.py',
                    'bbio/platform/beaglebone/3.2/adc.py',
                    'bbio/platform/beaglebone/3.2/pwm.py',
                    'bbio/platform/beaglebone/3.2/uart.py',
                    'bbio/platform/beaglebone/3.2/i2c_setup.py'])]

  # Older Angstrom images only included support for one of the PWM modules
  # broken out on the headers, check and warn if no support for PWM2 module:
  if (not os.path.exists('/sys/class/pwm/ehrpwm.2:0')):
    w = "you seem to have an old BeagleBone image which only has drivers for\n"+\
        "the PWM1 module, PWM2A and PWM2B will not be available in PyBBIO.\n"+\
        "You should consider updating Angstrom!"
    warnings.append(w)


setup(name='PyBBIO',
      version='0.8.5',
      description='A Python library for Arduino-style hardware IO support on single board Linux systems',
      author='Alexander Hiam',
      author_email='hiamalexander@gmail.com',
      license='Apache 2.0',
      url='https://github.com/alexanderhiam/PyBBIO/wiki',
      packages=['bbio', 'bbio.platform'] + driver_packages,
      py_modules = ['bbio.test'],
      package_dir=driver_package_dirs,
      ext_modules=driver_extensions, 
      install_requires=install_requires)
#data_files=driver_data,

if TASK == 'install':
  print "install finished with %i warnings" % len(warnings)
  if (len(warnings)):
    for i in range(len(warnings)):
      print "*Warning [%i]: %s\n" % (i+1, warnings[i])

  print "PyBBIO is now installed on your %s, enjoy!" % PLATFORM

