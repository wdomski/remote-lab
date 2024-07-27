# RemoteLab

RemoteLab is a platform intended to be run on small SBC like Raspberry Pi providing remote access to development boards like STM32 boards.

The project is developed in Python. Initially, the web server providing services like status server and camera serwer was realized using Flask.However, current implementation depends on Django unifying these two services and enhancing user experience.

I have created this platform for my students at Wrocław University of Science and Technology. During the period of pandemic it was necessary to develop a tool which would enable students to remotely realize exercise as they would do during normal classes. The initial version was launched in 2020 and since then it is operational 24/7 providing access to remote resources. 

# Installation

First create a virtual environment
```
python3 -m venv --system-site-packages .venv
```

Activate virtual environment
```
source .venv/bin/activate
```

Run upgrades and installation of necessary packages
```
pip install --upgrade pip
pip install -r requirements.txt
```

Run migrations for Django
```
cd RemoteLab
python manage.py makemigrations
python manage.py migrate
```

Before starting the file there are two mandatory changes that need to be done in the source code. 

Inside **RemoteLab/boards/views.py** at line 16 there is:

```
boards_config = "/home/pi/mcu-remote-work-pwr/resources/boards.json"
```

You must replace it with path to specific file with boards definitions. An example is available at **RemoteLab/resources/boards.json**.

Inside **RemoteLab/home/views.py** at line 14 there is:

```
config_file = "/home/pi/mcu-remote-work-pwr/resources/config.yml"
```

You must replace it with path to specific file with boards definitions. An example is available at **RemoteLab/resources/config.yml**.
This file also points to **boards.json**. In future it will be unified and configuration will be done outside of the project.


Now, you can run Django server, e.g. using build-in HTTP server
```
python manage.py runserver 0.0.0.0:8000
```

# Available features (for all users)

## Status server (Panel)

It allows to manage all connected development boards. It allows to:
- reset microcontroller's core (only for openocd),
- halt microcontroller's core (only for openocd),
- resume operation of microcontroller's core (only for openocd),
- restart debugger service (either openocd or stlink depending on the configuration).

It also provides the port number under which the remote connection to debugger for a given board is available. 

Along side with development board model, dedicated serial device and features are displayed. 
Serial device allows to directly connect to the development board and communicate with it. 
Features are tag-like entities. Since each development board is equipped with a shield it greatly enhances capabilities of the development board. The given tag corresponds to port number in the shield schematic, thus allowing to determine what additional devices are connected or what MCU ports could be used for operation. The PDF with the schematic could be found [here](https://github.com/wdomski/remote-lab/blob/master/board-shield/Nucleo64-shield.pdf).

### Health status

In addition, the health status is being displayed. If a smily face is being displayed it means that the debugger service is operational. However, when a warning is being displayed it means that the debugger service is not running. In this case restart of the debugger is recommended. 

## Video preview (Video)

It provides a video-like experience. It allows to stream *image* directly from a connected camera device. For example, the camera can be placed directly above the connected boards in order to provide live vide feedback.

There is a possibility to enable auto-refresh option. This allows to refresh the image every 10 seconds without user's input.

# Available features (for super user)

The serwer allows to extend available features presented to the end user after providing super user password. This feature allows to manager resources more precisely and unlocks additional capabilities.

## Terminal window

Terminal console (on the server) is available via web interface. It allows to execute commands with shell-like experience. There are some limitations, mainly when executing a command it should finish. Only when the command finishes it will provide the output of the command, thus commands like watch, less will not work.

## Status server (Panel)

Besides options available for normal user, now the control of the debugger service is more granular. Super user can start or stop the debugger service independently. 
Interaction with development board via serial interface was extended. In addition to providing path to serial device it is possible to open a serial console via web interface and directly read/send data.

The serial console offers information to what serial port it was connected and to which development board. More over, it is possible to enable:
- auto scrolling (enabled by default),
- append CR,
- append LF,
- local echo (enabled by default).

The console automatically pulls data from serial device available on the server and sends it to web interface. It is possible to clear the console or stop data reception. 

Currently, sharing of serial console between users is not supported. The received that will be send randomly to all connected recipients. The status server provides information if the console is being used (1 next to the serial device) or is idle (zero value next to the serial device).

## Video preview (Video)

Besides streaming images with auto refresh now it is possible to stream live video and configure the settings of the camera. Currently, Raspberry Pi Camera Modules are being supported with two different version of python libcamera library that is detected automatically. 

It is possible to set:
- image resolution, 
- rotation, 
- horizontal flip,
- vertical flip,
- brightness,
- contrast,
- saturation,
- sharpness.

Also direct links for image and video stream are available.
