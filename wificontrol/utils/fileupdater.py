# Written by Ivan Sapozhkov and Denis Chagin <denis.chagin@emlid.com>
#
# Copyright (c) 2016, Emlid Limited
# All rights reserved.
#
# Redistribution and use in source and binary forms,
# with or without modification,
# are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import os


class FileError(Exception):
    pass


class NetworkTemplate(object):

    _strings = ('ssid', 'psk', 'identity', 'wep_key0', 'password')
    network_template = 'network={{\n{}\n}}\n'
    string_template = '\t{}=\"{}\"'
    variant_template = '\t{}={}'


    def __init__(self, network_parameters):
        self.network_parameters = network_parameters

    def __str__(self):
        network_parameters = list()
        for key, value in self.network_parameters.items():
            if key in self._strings:
                network_parameters.append(self.string_template.format(key, value))
            else:
                network_parameters.append(self.variant_template.format(key, value))

        return self.network_template.format('\n'.join(network_parameters))


def CfgFileUpdater(cfg_file_path="/etc/wpa_supplicant/wpa_supplicant.conf"):
    try:
        with open(cfg_file_path, 'r') as cfg_file:
            pass
    except IOError:
        return NullFileUpdater()
    else:
        return ConfigurationFileUpdater(cfg_file_path)


class NullFileUpdater(object):
    def __init__(self, config_file_path=None):
        self.head = None
        self.networks = list()
        self.raw_file = None

    def add_network(self, network):
        pass

    def remove_network(self, network):
        pass


class ConfigurationFileUpdater(object):

    def __init__(self, config_file_path="/etc/wpa_supplicant/wpa_supplicant.conf"):

        self.head = None
        self.networks = list()
        self.raw_file = None
        self.__config_file_path = config_file_path

        self.__initialise()

    def __initialise(self):
        try:
            with open(self.__config_file_path, 'r') as config_file:
               self.raw_file = config_file.read() 
        except IOError:
            raise FileError("No configuration file")
        else:
            self.__parse_file()

    def __parse_file(self):
        self.head = self.__get_header()
        self.networks = self.__get_network_list()

    def __get_header(self):
        try:
            return self.raw_file[0: self.raw_file.index('\nnetwork={')]
        except ValueError:
            return (self.raw_file.strip() + '\n')

    def __get_network_list(self):
        try:
            raw_networks = self.raw_file[self.raw_file.index('\nnetwork={'):]
        except ValueError:
            return []
        else:
            return [self.__parse_network(network) for network in raw_networks.strip().split('\n\n')]

    def __parse_network(self, raw_network):
        param_pair_list = raw_network[raw_network.find('\t'):raw_network.find('}')].strip().split('\n')
        return {key.strip(): parameter.strip("\"") for key, parameter in (param_pair.split('=', 1) for param_pair in param_pair_list)}

    def __create_config_file(self):
        return self.head + '\n' + '\n'.join([str(NetworkTemplate(network)) for network in self.networks])

    def __findNetwork(self, network_aim):
        for network in self.networks:
            if network["ssid"].strip("\'\"") == network_aim["ssid"]:
                return network

    def __update_config_file(self):
        with open(self.__config_file_path, 'w') as config_file:
            config_file.write(self.__create_config_file())
            config_file.flush()
            os.fsync(config_file)

    def add_network(self, network):
        if self.__findNetwork(network) is None:
            self.networks.append(network)
            self.__update_config_file()
        else:
            raise AttributeError("Network already added")

    def remove_network(self, network):
        try:
            self.networks.remove(self.__findNetwork(network))
        except ValueError:
            raise AttributeError("No such network")
        else:
            self.__update_config_file()


if __name__ == '__main__':
    config_updater = CfgFileUpdater('/etc/wpa_supplicant/wpa_supplicant.conf')
    print(type(config_updater))

    for network in config_updater.networks:
        print(NetworkTemplate(network))
