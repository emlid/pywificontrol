from distutils.core import setup

setup(
    name='wificontrol',
    version='0.0.1.dev',
    author='Ivan Sapozhkov',
    author_email='i.sapozhkov.93@gmail.com',
    py_modules=['wificontrol'],
    url='https://github.com/emlid/reach-wifi-configurator.git',
    description='Module for contol WiFi connections with host(AP) and client(WPA) modes.',
    long_description=open('README.md').read(),
)