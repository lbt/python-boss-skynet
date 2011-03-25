from distutils.core import setup
from setuptools import setup

setup(name='python-boss-skynet',
      version='0.2',
      description='SkyNET for BOSS',
      author='David Greaves',
      author_email='david@dgreaves.com',
      url='http://meego.gitorious.org/meego-infrastructure-tools/python-boss-skynet',
      packages=['SkyNET',],
      requires=['RuoteAMQP',],
      data_files=[('/usr/share/doc/python-boss-skynet',['example-check-participant','example-notify-participant','minimal-participant','README',]),
                  ]
     )
