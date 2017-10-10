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