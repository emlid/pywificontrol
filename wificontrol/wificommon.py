import subprocess
from sysdmanager import SystemdManager

class WiFiControlError(Exception):
    pass

class WiFi(object):

    restart_mdns = "systemctl restart mdns.service && sleep 2"
    rfkill_wifi_control = lambda self, action: "rfkill {} wifi".format(action)

    def __init__(self):
        self.sysdmanager = SystemdManager()

    def restart_mdns(self):
        self.execute_command(self.restart_mdns)

    def block():
        self.execute_command(self.rfkill_wifi_control("unblock"))

    def unblock():
        self.execute_command(self.rfkill_wifi_control("unblock"))

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