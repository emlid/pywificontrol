import sys
from wificontrol import WiFiControl, WiFiControlError

def ConnectionCallback(result, wific):
    if not result:
        print "Can't connect to any network."
        print "Start HOSTAP mode"
        try:
            wific.start_host_mode()
        except WiFiControlError as error:
            print error
            sys.exit(2)
        else: 
            print "In HOST mode"
            sys.exit(10)
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
        try:
            rwc.start_client_mode()
        except WiFiControlError as error:
            print error
            try:
                rwc.start_host_mode()
            except WiFiControlError as error:
                print error
                sys.exit(2)
            else:
                print "In HOST mode"
                sys.exit(10)
        else:
            print "Start connecting to networks"
            rwc.start_connecting(None, callback=ConnectionCallback, args = rwc)