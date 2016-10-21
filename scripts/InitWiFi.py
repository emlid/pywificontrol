from wificontrol import wificontrol
import sys

def ConnectionCallback(result, wific):
    if not result:
        print "Can't connect to any network."
        print "Start HOSTAP mode"
        if wific.start_host_mode():
            print "In HOST mode"
            sys.exit(10)
        else:
            sys.exit(2)
    else:
        status = wific.get_status()[1]
        print "Connected to {}".format(status['ssid'])
        sys.exit(0)

if __name__ == "__main__":
    try:
        rwc = wificontrol()
    except OSError, error:
        print error
        sys.exit(2)
    else:
        print "Start wpa_supplicant service"
        if not rwc.start_client_mode():
            print "wpa_supplicant service error"
            print "For more information call \'systemctl status wpa_supplicant.service\'"
            sys.exit(2)
        print "Start connecting to networks"
        rwc.start_connecting(None, callback=ConnectionCallback,
                args = rwc, any_network=True)
