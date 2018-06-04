#!/usr/bin/python

# Written by Aleksandr Aleksandrov <aleksandr.aleksandrov@emlid.com>
#
# Copyright (c) 2017, Emlid Limited
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


def _show_result(result, wifi_controller):
    if result:
        sys.stdout.write("Network mode: client")
    else:
        if wifi_controller.start_host_mode():
            sys.stdout.write("Network mode: master")
        else:
            sys.stdout.write("Network mode: unknown")


def initialize():
    try:
        wifi_controller = WiFiControl()
    except WiFiControlError:
        sys.stdout.write("Network mode: unknown")
    else:
        wifi_controller.turn_on_wifi()

        if wifi_controller.start_client_mode():
            wifi_controller.start_connecting(
                None, callback=_show_result,
                args=(wifi_controller,))
        else:
            if wifi_controller.start_host_mode():
                sys.stdout.write("Network mode: master")
            else:
                sys.stdout.write("Network mode: unknown")


if __name__ == "__main__":
    initialize()
