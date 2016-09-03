from distutils.core import setup

setup(
    name='wificontrol',
    version='0.0.1.dev1',
    author='Ivan Sapozhkov',
    author_email='i.sapozhkov.93@gmail.com',
    packages='wificontrol',
    url='https://github.com/emlid/reach-wifi-configurator.git',
    #license='LICENSE.txt',
    description='Module for contol WiFi connections with host(AP) and client(WPA) modes.',
    long_description=open('README.txt').read(),
    classifiers=[
        #   2 - Pre-Alpha
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 2 - Pre-Alpha',

        'Intended Audience :: Developers',
        'Topic :: System :: Networking',

        #'License :: OSI Approved :: BSD License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        #'Programming Language :: Python :: 3',
        #'Programming Language :: Python :: 3.3',
        #'Programming Language :: Python :: 3.4',
        #'Programming Language :: Python :: 3.5',
    ],
    install_requires=[
        "wpa_supplicant",
        "hostapd",
    ],
)