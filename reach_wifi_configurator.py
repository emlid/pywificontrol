import subprocess
import shlex
import time

class ReachWiFi():
	def __init__(self):
		pass
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

	def connect(self, path = '/etc/wpa_supplicant/example.conf', interface = 'wlp6s0'):
		self.write("wpa_supplicant -B -i " + interface + " -c " + path)

	def scan(self):
		self.write("wpa_cli scan")
		time.sleep(1)
		res = self.write("wpa_cli scan_result").split("\n")[2:-1]

		seq = []
		for a in res:
			r1 = a.split('\t')
			seq.append((r1[0], r1[4]))
		return seq	


if __name__ == '__main__':
	a = ReachWiFi()
	a.connect()
	print a.scan()

	r = a.write("wpa_cli add_network")
	r = r.split("\n")[1]
	print a.write(['wpa_cli', 'set_network', r, 'ssid', '\"EML33T2\"'])
	print a.write(['wpa_cli', 'set_network', r, 'psk', '\"emrooftop\"'])
	print a.write("wpa_cli enable_network %s" % r)
	print a.write("wpa_cli save_config")
	print a.write("wpa_cli quit")
