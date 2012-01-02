from distutils.core import setup
from setuptools import setup
from setuptools import find_packages

setup(name='python-boss-skynet',
      version='0.5.0',
      description='SkyNET for BOSS',
      author='David Greaves',
      author_email='david@dgreaves.com',
      url='http://meego.gitorious.org/meego-infrastructure-tools/python-boss-skynet',
      packages=['SkyNET',],
      requires=['RuoteAMQP',],
      scripts=['scripts/skynet', 'scripts/skynet_exo'],
      data_files=[('/usr/share/doc/python-boss-skynet',
                    ['examples/example-check-participant',
                     'examples/example-notify-participant',
                     'examples/minimal-participant',
                     'README','INSTALL']),
                  ('/etc/skynet', ['conf/skynet.conf', 'conf/skynet.env'])
                  ]
     )
