import subprocess
import shlex
import time

class ReachWiFi():
	def __init__(self, hostapd_path = "/etc/hostapd/hostapd.conf", wpasupplicant_path = "/etc/wpa_supplicant/wpa_supplicant.conf"):
		self.hostapd_path = hostapd_path
		self.wpasupplicant_path = wpasupplicant_path
		try:
			status = self.write("wpa_cli status")
			if not status:
				raise
		except:
			self.wpa_sup_start = False
			self.hostapd_start = True
		else:
			self.wpa_sup_start = True
			self.hostapd_start = False

		self.network_list = self.parse_wpa_conf_file()
	def __del__(self):
		pass

	def write(self, args):
		if isinstance(args, str):
			args = shlex.split(args)
		if  isinstance(args, list):
			#print args
			ps = subprocess.Popen(args, stdout=subprocess.PIPE)
			ps.wait()
			(ret, ret2) = ps.communicate()
			return ret
		else:
			return None
	#Host part
	def start_host_mode(self):
		if not self.wpa_sup_start:
			print "Already in host mode"
			return
		self.write("wpa_cli disconnect")
		self.write("systemctl stop wpa_supplicant.service")
		self.wpa_sup_start = False
		self.write("systemctl start hostapd.service")
		#self.write("hostapd -B " + self.hostapd_path)
		self.hostapd_start = True

	def start_client_mode(self):
		if not self.hostapd_start:
			print "Already in client mode"
			return
		self.write("systemctl stop hostapd.service")
		self.hostapd_start = False
		self.start_wpa_supplicant()
		self.wpa_sup_start = True


	#Client part
	def start_wpa_supplicant(self, interface = 'wlan0'):
		#self.write("wpa_supplicant -B -i " + interface + " -c " + self.wpasupplicant_path)
		self.write("systemctl start wpa_supplicant.service")

	def scan(self):
		self.write("wpa_cli scan")
		res = self.write("wpa_cli scan_result").split("\n")[2:-1]
		seq = list()
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
						e.get("ssid") if e.get("ssid") is not None else ''))
		return res

	def delta_added_scan(self):
		cur_scan = self.scan()
		if self.network_list:
			for key in self.network_list:	
				for tuple_network in cur_scan:
					if key[1].strip('\"') == tuple_network[1]:
						cur_scan.pop(cur_scan.index(tuple_network))
						break
			return cur_scan
		else:
			return cur_scan

	def add_network(self, args):
		if self.network_list:
			for key in self.network_list:
				if args[0] == key[0] & args[1] == key[1]:
					print "Already added"
					return None
		r = self.write("wpa_cli add_network").split("\n")[1]
		self.write(['wpa_cli', 'set_network', r, 'bssid', args[0]])
		self.write(['wpa_cli', 'set_network', r, 'ssid', '\"'+args[1]+'\"'])
		self.write(['wpa_cli', 'set_network', r, 'psk', '\"'+args[2]+'\"'])
		#self.write("wpa_cli enable_network %s" % r)
		self.write("wpa_cli save_config")

	def connect(self, mac_ssid):
		status = self.write("wpa_cli status")
		ind_disc = None
		if status.split('\n')[1].split('=')[1] != "DISCONNECTED":
			ind_disc = status.split('\n')[4].split('=')[1]
			self.write("wpa_cli disable_network %s" % ind_disc)
		try:
			ind_conn = self.network_list.index(self.find_tuple_ssid(mac_ssid[1]))
		except:
			print "No such network"
			if ind_disc is not None:
				print "Reconnect"
				self.write("wpa_cli enable_network %s" % ind_disc)
			else:
				print "Disconnect"
		else:
			self.write("wpa_cli enable_network %s" % ind_conn)
		finally:
			self.write("wpa_cli reconnect")

	def remove_network(self, ssid):
		tuple_network = self.find_tuple_ssid(ssid)
		if tuple_network is not None:
			index = self.network_list.index(tuple_network)
			self.network_list.pop(index)
			self.write("wpa_cli remove_network %s" % index)
			self.write("wpa_cli save_config")
			self.write("wpa_cli reconfigure")
		else:
			print "No such network"

	def find_tuple_ssid(self, ssid):
		for a in self.network_list:
			if a[1].strip('\"') == ssid:
				return a
		return None


if __name__ == '__main__':
	a = ReachWiFi()
