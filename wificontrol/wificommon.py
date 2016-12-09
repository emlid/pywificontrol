import re
import subprocess
from sysdmanager import SystemdManager

class WiFiControlError(Exception):
    pass

class WiFi(object):

    restart_mdns = "systemctl restart mdns.service && sleep 2"
    rfkill_wifi_control = lambda self, action: "rfkill {} wifi".format(action)

    def __init__(self, interface):
        self.interface = interface
        self.sysdmanager = SystemdManager()

    def restart_dns(self):
        self.execute_command(self.restart_mdns)

    def block():
        self.execute_command(self.rfkill_wifi_control("block"))

    def unblock():
        self.execute_command(self.rfkill_wifi_control("unblock"))

    def get_device_ip(self):
        ip_pattern = "[0-9]+.[0-9]+.[0-9]+.[0-9]+"
        data = self.execute_command("ifconfig {}".format(self.interface))
        try:
            return re.search("inet addr:{}".format(ip_pattern), data).group(0)[10:]
        except TypeError:
            return None

    def get_device_mac(self):
        mac_pattern = "..:..:..:..:..:.."
        data = self.execute_command("ifconfig {}".format(self.interface))
        try:
            return re.search(mac_pattern, data).group(0)
        except TypeError:
            return None

    def execute_command(self, args):
        try:
            return subprocess.check_output(args, stderr=subprocess.PIPE, shell=True)
        except subprocess.CalledProcessError as error:
            error_message = "WiFiControl: subprocess call error\n"
            error_message += "Return code: {}\n".format(error.returncode)
            error_message += "Command: {}".format(args)
            raise WiFiControlError(error_message)

if __name__ == '__main__':
    wifi = WiFi()