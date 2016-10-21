from distutils.core import setup

setup(
    name='wificontrol',
    version='0.2.0',
    author='Ivan Sapozhkov',
    author_email='ivan.sapozhkov@emlid.com',
    py_modules=['wificontrol'],
    license = 'GPLv3',
    url='https://github.com/emlid/reach-wifi-configurator.git',
    description='Module for contol WiFi connections with host(AP) and client(WPA) modes.',
    long_description=open('README.md').read(),
)
