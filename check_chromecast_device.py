import pychromecast
from configurations import CHROMECAST_DEVICE_IP

device = pychromecast.Chromecast(CHROMECAST_DEVICE_IP)
device.wait()
print(device)
