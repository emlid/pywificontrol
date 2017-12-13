from setuptools import setup, find_packages


setup(
    name='wificontrol',
    version='0.5.0',
    author='Ivan Sapozhkov, Denis Chagin, Dmitriy Skorykh',
    author_email='denis.chagin@emlid.com',
    packages=find_packages(exclude=['tests']),
    license='BSD-3',
    url='https://github.com/emlid/reach-wifi-configurator.git',
    description='Python API to control WiFi connectivity',
    tests_require=['pytest', 'pytest-mock'],
    long_description=open('README.md').read(),
    entry_points={
        'console_scripts': [
            'wifimonitord = wificontrol.wifimonitord:main',
            'wifireconnectd = wificontrol.wifireconnectd:main'
        ]
    },
)
