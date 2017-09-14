from setuptools import setup

setup(
    name='wificontrol',
    version='0.4.0',
    author='Ivan Sapozhkov, Denis Chagin',
    author_email='ivan.sapozhkov@emlid.com, denis.chagin@emlid.com',
    packages=['wificontrol', 'wificontrol.utils'],
    license='GPLv3',
    url='https://github.com/emlid/reach-wifi-configurator.git',
    description='Module for control WiFi connections with host(AP) and client(WPA) modes.',
    install_requires=[
        'sysdmanager',
        'netifaces'
    ],
    extras_require={
        'test': ['pytest', 'pytest-cov'],
    },
    long_description=open('README.md').read()
)
