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
        self.networks = list()

    def add_network(self, network):
        pass

    def remove_network(self, network):
        pass


class ConfigurationFileUpdater(object):
    network_path = "/etc/wpa_supplicant/networks"

    def __init__(self, config_file_path="/etc/wpa_supplicant/wpa_supplicant.conf"):

        self.networks = list()
        self.__config_file_path = config_file_path
        self.__parse_network_configs()

    def __collect_network_configurations(self):
        raw_network = ''
        if os.path.exists(self.network_path):
            network_files = os.listdir(self.network_path)
            for network in network_files:
                raw_network += self.__select_and_read_netconf_files(network)

        return raw_network

    def __select_and_read_netconf_files(self, file):
        raw_network = ''
        filename, file_extension = os.path.splitext(file)
        if file_extension == ".netconf":
            network_file_path = os.path.join(self.network_path, file)
            raw_network = self.__read_network_file(network_file_path)
            return raw_network
        return raw_network

    def __read_network_file(self, path):
        try:
            with open(path, 'r') as network_file:
                raw_network_file = network_file.read()
        except IOError:
            raise FileError("No network file")
        else:
            return raw_network_file

    def __parse_network_configs(self):
        self.networks = self.__get_network_list_()

    def __get_network_list_(self):
        try:
            nets = self.__collect_network_configurations()
            raw_networks = nets[nets.index('\nnetwork={'):]
        except ValueError:
            return []
        else:
            return [self.__parse_network(network) for network in raw_networks.strip().split('\n\n')]

    def __parse_network(self, raw_network):
        try:
            param_pair_list = raw_network[raw_network.find('\t'):raw_network.find('}')].strip().split('\n')
        except ValueError:
            return None
        else:
            return {key.strip(): parameter.strip("\"") for key, parameter in (param_pair.split('=', 1) for param_pair in param_pair_list)}

    def __findNetwork(self, network_aim):
        for network in self.networks:
            if network["ssid"].strip("\'\"") == network_aim["ssid"]:
                return network

    def __write_network_file(self, network_config, network_file_path):
        with open(network_file_path, "w") as network_file:
            network_file.write(network_config)
            network_file.flush()
            os.fsync(network_file)

    def __add_network_file(self, network):
        if not os.path.exists(self.network_path):
            os.mkdir(self.network_path)

        network_file_path = "{}/{}.netconf".format(self.network_path, network['ssid'])
        network_config = self.__create_network_config(network)

        self.__write_network_file(network_config, network_file_path)

    def __create_network_config(self, network):
        return '\n{}'.format(str(NetworkTemplate(network)))

    def add_network(self, network):
        if self.__findNetwork(network) is None:
            self.networks.append(network)
            self.__add_network_file(network)
        else:
            raise AttributeError("Network already added")

    def __remove_network_file(self, network):
        network_file_path = "{}/{}.netconf".format(self.network_path, network['ssid'])

        if os.path.exists(network_file_path):
            os.remove(network_file_path)

    def remove_network(self, network):
        try:
            self.networks.remove(self.__findNetwork(network))
        except ValueError:
            raise AttributeError("No such network")
        else:
            self.__remove_network_file(network)


if __name__ == '__main__':
    config_updater = CfgFileUpdater('/etc/wpa_supplicant/wpa_supplicant.conf')
    print(type(config_updater))

    for network in config_updater.networks:
        print(NetworkTemplate(network))
