from django.shortcuts import render
from django.http import StreamingHttpResponse, HttpResponse

import time
import socket

from utils.ConfigParsers import read_json
from utils.check_port import checkPort
from utils.check_usb import serialDeviceList
from utils.DebuggerService import DebuggerService
from utils.SerialTerminal import SerialGovernor

from home.views import get_status

hostname = socket.gethostname()
boards_config = "/home/pi/mcu-remote-work-pwr/resources/boards.json"
devices = read_json(boards_config, hostname)
serial_devices = serialDeviceList()
serial_governor = SerialGovernor()


def list_devices():
    parsed_devices = []
    for dev in devices:
        parsed_device = {
            "id": dev["id"],
            "port": dev["port"],
            "status": "Error",
            "board": dev["board"],
            "serial": "Unavailable",
            "features": ", ".join(dev["features"]),
            "debugger_service": dev["debugger_service"],
            "serial_in_use": False,
        }

        status = checkPort(int(dev["port"]))
        if status == 0:
            parsed_device["status"] = "Online"
        elif status == 1:
            parsed_device["status"] = "Offline"

        serial_number = dev["serial"]
        if serial_number in serial_devices:
            parsed_device["serial"] = serial_devices[serial_number]
            if serial_governor.in_use(parsed_device["serial"]):
                parsed_device["serial_in_use"] = True

        parsed_devices.append(parsed_device)

    parameters = {"devices": parsed_devices, "refreshrate": 10}

    return parameters


def home(request):
    data = list_devices()
    data.update(get_status())

    return render(request, "boards/index.html", data)


def reset(request, id: str):
    data = list_devices()
    data.update(get_status())

    # Check if id is inside devices
    available_ids = [dev["id"] for dev in devices]
    if id in available_ids:
        message_type = "success"
        message = f"Reset board with ID {id}"
        try:
            debugger = DebuggerService(devices, hostname)
            response = debugger.reset(id=id)
            if "Success" not in response:
                message_type = "danger"
                message = "Error occurred during command execution"
                print(response)
        except Exception as e:
            message_type = "danger"
            message = "Error occurred during reset"
            print(e)
    else:
        message_type = "danger"
        message = f"Wrong ID {id}"

    data["message"] = message
    data["message_type"] = message_type

    return render(request, "boards/index.html", data)


def halt(request, id: str):
    data = list_devices()
    data.update(get_status())

    # Check if id is inside devices
    available_ids = [dev["id"] for dev in devices]
    if id in available_ids:
        message_type = "success"
        message = f"Halted board with ID {id}"
        try:
            debugger = DebuggerService(devices, hostname, verbose=True)
            response = debugger.halt(id=id)
            if "Success" not in response:
                message_type = "danger"
                message = "Error occurred during command execution"
                print(response)
        except Exception as e:
            message_type = "danger"
            message = "Error occurred during halt"
            print(e)
    else:
        message_type = "danger"
        message = f"Wrong ID {id}"

    data["message"] = message
    data["message_type"] = message_type

    return render(request, "boards/index.html", data)


def resume(request, id: str):
    data = list_devices()
    data.update(get_status())

    # Check if id is inside devices
    available_ids = [dev["id"] for dev in devices]
    if id in available_ids:
        message_type = "success"
        message = f"Resumed board with ID {id}"
        try:
            debugger = DebuggerService(devices, hostname)
            response = debugger.resume(id=id)
            if "Success" not in response:
                message_type = "danger"
                message = "Error occurred during command execution"
                print(response)
        except Exception as e:
            message_type = "danger"
            message = "Error occurred during resume"
            print(e)
    else:
        message_type = "danger"
        message = f"Wrong ID {id}"

    data["message"] = message
    data["message_type"] = message_type

    return render(request, "boards/index.html", data)


def restart_debugger(request, id: str):
    # check if id is inside devices
    available_ids = [dev["id"] for dev in devices]
    if id in available_ids:
        message_type = "success"
        message = f"Restarted board with ID {id}"
        try:
            debugger = DebuggerService(devices, hostname, verbose=True)
            debugger.restart(id=id)
            time.sleep(0.5)
        except Exception as e:
            message_type = "danger"
            message = "Error occurred during restart"
            print(e)
    else:
        message_type = "danger"
        message = f"Wrong ID {id}"

    data = list_devices()
    data.update(get_status())
    data["message"] = message
    data["message_type"] = message_type

    return render(request, "boards/index.html", data)


def start_debugger(request, id: str):
    # Check if id is inside devices
    available_ids = [dev["id"] for dev in devices]
    if id in available_ids:
        message_type = "success"
        message = f"Started debugger for board with ID {id}"
        try:
            debugger = DebuggerService(devices, hostname)
            response = debugger.start(id=id)
            time.sleep(0.5)
        except Exception as e:
            message_type = "danger"
            message = "Error occurred while starting debugger"
            print(e)
    else:
        message_type = "danger"
        message = f"Wrong ID {id}"

    data = list_devices()
    data.update(get_status())
    data["message"] = message
    data["message_type"] = message_type

    return render(request, "boards/index.html", data)


def stop_debugger(request, id: str):
    # Check if id is inside devices
    available_ids = [dev["id"] for dev in devices]
    if id in available_ids:
        message_type = "success"
        message = f"Stopped debugger for board with ID {id}"
        try:
            debugger = DebuggerService(devices, hostname)
            response = debugger.kill(id=id)
            time.sleep(0.5)
        except Exception as e:
            message_type = "danger"
            message = "Error occurred while stopping debugger"
            print(e)
    else:
        message_type = "danger"
        message = f"Wrong ID {id}"

    data = list_devices()
    data.update(get_status())
    data["message"] = message
    data["message_type"] = message_type

    return render(request, "boards/index.html", data)


def serial_console(request, id: str):
    data = list_devices()
    data.update(get_status())
    # check if id is inside devices
    available_ids = [dev["id"] for dev in devices]
    if id in available_ids:
        dev = next(dev for dev in devices if dev["id"] == id)
        serial_number = dev["serial"]
        serial_device = serial_devices[serial_number]
        parameters = {
            "id": id,
            "serial_port": serial_device,
        }
        data.update(parameters)
    else:
        data["message"] = "Wrong ID"
        data["message_type"] = "danger"
        data["id"] = -1

    return render(request, "boards/serial_console.html", data)


def serial_read_stream(request, id: str):
    available_ids = [dev["id"] for dev in devices]
    if id in available_ids:
        dev = next(dev for dev in devices if dev["id"] == id)
        serial_number = dev["serial"]
        serial_device = serial_devices[serial_number]

        def generate():
            while True:
                data = serial_governor.read(serial_device)
                yield data

        g = generate()
        return StreamingHttpResponse(g, content_type="text/plain")
    
    return HttpResponse("Wrong ID", status=404)


def serial_read(request, id: str):
    available_ids = [dev["id"] for dev in devices]
    output = ""
    if id in available_ids:
        dev = next(dev for dev in devices if dev["id"] == id)
        serial_number = dev["serial"]
        serial_device = serial_devices[serial_number]
        output = serial_governor.read(serial_device)
    else:
        return HttpResponse("Wrong ID", status=404)

    return HttpResponse(output)


def serial_write(request, id: str):
    available_ids = [dev["id"] for dev in devices]
    if id in available_ids:
        dev = next(dev for dev in devices if dev["id"] == id)
        serial_number = dev["serial"]
        serial_device = serial_devices[serial_number]
        data = request.POST.get("data", "")
        serial_governor.write(serial_device, data)

    return HttpResponse("OK")

def plot(request):
    data = list_devices()
    data.update(get_status())

    return render(request, "boards/plot.html", data)