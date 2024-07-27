import sys
import subprocess
import re
import os

def serialDeviceList():
    serial_char_device = {}

    serial_devices = []
    dev_path = '/dev/serial/by-id'
    try:
        serial_devices = os.listdir(dev_path)
    except Exception as e:
        print(e)

    for dev in serial_devices:
        match = re.search("usb-STMicroelectronics_STM32_STLink_([0-9a-fA-F]+)-if([0-9]+)", dev)
        if match is not None:
            serial = match.group(1)
            usb_path = os.path.join(dev_path, dev)
            real_path = os.path.realpath(usb_path)
            serial_char_device[serial] = real_path

    return serial_char_device

def main():
    devs = serialDeviceList()
    for k, v in devs.items():
        print("%s -> %s" % (k, v))
    

if __name__=="__main__":
    main()
