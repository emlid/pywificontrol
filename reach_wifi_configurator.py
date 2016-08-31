import subprocess
import shlex
import time

class ReachWiFi():
	def __init__(self, hostapd_path = "/etc/hostapd/hostapd.conf", wpasupplicant_path = "/etc/wpa_supplicant/wpa_supplicant.conf"):
		self.hostapd_path = hostapd_path
		self.wpasupplicant_path = wpasupplicant_path
		self.network_list = self.parse_wpa_conf_file()
	def __del__(self):
		pass
	def write(self, args):
		if isinstance(args, str):
			args = shlex.split(args)
		if  isinstance(args, list):
			print args
			ps = subprocess.Popen(args, stdout=subprocess.PIPE)
			ps.wait()
			(ret, ret2) = ps.communicate()
			#ret = subprocess.call(args)
			return ret
		else:
			return None
	#Host part
	def host_status(self):
		self.write("ifconfig")
		self.write("ip link")
		self.write("service --status-all")

	#Client part
	def wpa_sup_info(self):
		self.write("wpa_supplicant -h")	

	def start_wpa_supplicant(self, interface = 'wlan0'):
		self.write("wpa_supplicant -B -i " + interface + " -c " + self.wpasupplicant_path)

	def scan(self):
		self.write("wpa_cli scan")
		res = self.write("wpa_cli scan_result").split("\n")[2:-1]

		seq = []
		for a in res:
			r1 = a.split('\t')
			seq.append((r1[0], r1[4]))
		return seq	

	def parse_wpa_conf_file(self):
		res = list()
		b = self.write("cat " + self.wpasupplicant_path).split("\n\n")[1:]
		for c in b: 
			e = {n.strip().split('=')[0] : n.strip().split('=')[1] for n in c.strip().split('\n')[1:-1]}
                        #TODO: more effective
			res.append((e.get("bssid") if e.get("bssid") is not None else '', 
						e.get("ssid") if e.get("ssid") is not None else '', 
						e.get("psk") if e.get("psk") is not None else ''))
		return res

	def delta_added_scan(self):
		cur_scan = self.scan()
		if self.network_list:
			for key in self.network_list:	
                            for a in cur_scan:
                                if key[1].strip('\"') == a[1]:
						cur_scan.pop(cur_scan.index(a))
						break
			return cur_scan
		else:
			return cur_scan

	def add_network(self, args):
		if self.network_list:
			for key in self.network_list:
				if args == key:
					print "Already added"
					return None
		r = self.write("wpa_cli add_network").split("\n")[1]
		self.write(['wpa_cli', 'set_network', r, 'bssid', args[0]])
		self.write(['wpa_cli', 'set_network', r, 'ssid', '\"'+args[1]+'\"'])
		self.write(['wpa_cli', 'set_network', r, 'psk', '\"'+args[2]+'\"'])
		#self.write("wpa_cli enable_network %s" % r)
		self.write("wpa_cli save_config")

	def remove_network(self, ssid):
                ind = None
		for a in self.network_list:
			if a[1].strip('\"') == ssid:
				ind = self.network_list.index(a)
				break
		if ind is not None:
                    self.network_list.pop(ind)
		    self.write("wpa_cli remove_network %s" % ind)
		    self.write("wpa_cli save_config")
		    self.write("wpa_cli reconfigure")


if __name__ == '__main__':
	a = ReachWiFi()
        print a.network_list
        print a.scan()        
#        a.remove_network('ABC')

