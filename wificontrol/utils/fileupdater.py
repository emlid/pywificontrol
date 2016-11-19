class FileError(Exception):
    pass

class NetworkTemplate(object):

    network_template = 'network={{\n{}\n}}\n'
    string_template = '\t{}=\"{}\"'
    variant_template = '\t{}={}'

    def __init__(self, network_parameters):
        self.network_parameters = network_parameters

    def __str__(self):
        network_parameters = list()
        for key, value in self.network_parameters.items():
            if key in ('ssid', 'psk', 'identity'):
                network_parameters.append(self.string_template.format(key, value))
            else:
                network_parameters.append(self.variant_template.format(key, value))

        return self.network_template.format('\n'.join(network_parameters))

class NullFileUpdater(object):
    def __init__(self, config_file_path=None):
        self.head = None
        self.networks = list()
        self.raw_file = None

    def addNetwork(self, network):
        pass

    def removeNetwork(self, network):
        pass

class ConfigurationFileUpdater(object):
    
    __config_file_path = "/etc/wpa_supplicant/wpa_supplicant.conf"

    def __init__(self, config_file_path=None):
        
        self.head = None
        self.networks = list()
        self.raw_file = None
        if config_file_path is not None:
            self.__config_file_path = config_file_path

        self.__initialise()

    def __initialise(self):
        try:
            config_file = open(self.__config_file_path, 'r')
        except IOError:
            raise FileError("No configuration file")
        else:
            self.raw_file = config_file.read()
            self.__parse_file()

    def __parse_file(self):
        self.head = self.__get_header()
        self.networks = self.__get_network_list()

    def __get_header(self):
        try:
            return self.raw_file[0: self.raw_file.index('\nnetwork={')]
        except ValueError:
            return ''

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
        config_file = open(self.__config_file_path, 'w')
        config_file.write(self.__create_config_file())
        config_file.close()

    def addNetwork(self, network):
        if self.__findNetwork(network) is None:
            self.networks.append(network)
            self.__update_config_file()
        else:
            raise AttributeError("Network already added")

    def removeNetwork(self, network):
        try:
            self.networks.remove(self.__findNetwork(network))
        except ValueError:
            pass
        else:
            self.__update_config_file()

if __name__ == '__main__':
    try:
        config_updater = ConfigurationFileUpdater()
    except FileError as error:
        config_updater = NullFileUpdater()

    for network in config_updater.networks:
        print(NetworkTemplate(network))
    
    new_network = {"ssid": "myssid", "psk": "mypassword", "key_mgmt": "WPA-PSK"}
    config_updater.addNetwork(new_network)
    config_updater.removeNetwork(new_network)
