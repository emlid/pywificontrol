from setuptools import setup

setup(
    name='wificontrol',
    version='0.2.8',
    author='Ivan Sapozhkov',
    author_email='ivan.sapozhkov@emlid.com',
    packages=['wificontrol', 'wificontrol.utils'],
    license = 'GPLv3',
    url='https://github.com/emlid/reach-wifi-configurator.git',
    description='Module for contol WiFi connections with host(AP) and client(WPA) modes.',
    long_description=open('README.md').read(),
)
