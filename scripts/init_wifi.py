# wificontrol code is placed under the GPL license.
# Written by Ivan Sapozhkov (ivan.sapozhkov@emlid.com)
# Copyright (c) 2016, Emlid Limited
# All rights reserved.

# If you are interested in using wificontrol code as a part of a
# closed source project, please contact Emlid Limited (info@emlid.com).

# This file is part of wificontrol.

# wificontrol is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# wificontrol is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with wificontrol.  If not, see <http://www.gnu.org/licenses/>.


import sys
from wificontrol import WiFiControl, WiFiControlError


def connection_callback(result, wific):
    if not result:
        print("Can't connect to any network.")
        print("Start HOSTAP mode")
        try:
            wific.start_host_mode()
        except WiFiControlError as error:
            print(error)
            sys.exit(2)
        else: 
            print("In HOST mode")
            sys.exit(10)
    else:
        status = wific.get_status()[1]
        print("Connected to {}".format(status['ssid']))
        sys.exit(0)


if __name__ == "__main__":
    try:
        rwc = wificontrol()
    except OSError, error:
        print(error)
        sys.exit(2)
    else:
        print("Start wpa_supplicant service")
        try:
            rwc.start_client_mode()
        except WiFiControlError as error:
            print(error)
            try:
                rwc.start_host_mode()
            except WiFiControlError as error:
                print(error)
                sys.exit(2)
            else:
                print("In HOST mode")
                sys.exit(10)
        else:
            print("Start connecting to networks")
            rwc.start_connecting(None, callback=connection_callback, args=rwc)