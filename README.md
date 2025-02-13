# RemoteLab

RemoteLab is a platform intended to be run on small SBC like Raspberry Pi providing remote access to development boards like STM32 boards.

The project is developed in Python. Initially, the web server providing services like status server and camera server was realized using Flask.However, current implementation depends on Django unifying these two services and enhancing user experience.

I have created this platform for my students at Wrocław University of Science and Technology. During the period of pandemic it was necessary to develop a tool which would enable students to remotely realize exercise as they would do during normal classes. The initial version was launched in 2020 and since then it is operational 24/7 providing access to remote resources. 

Demonstration of the RemoteLab is available in the below video:

[![RemoteLab a distributed Hardware-as-a-Service demonstration](https://img.youtube.com/vi/YvHmJQDw91k/0.jpg)](https://www.youtube.com/watch?v=YvHmJQDw91k "RemoteLab a distributed Hardware-as-a-Service demonstration")

Also, there are articles featuring the RemoteLab platform:

- [RemoteLab - a distributed Hardware-as-a-Service platform](https://blog.domski.pl/remotelab-a-distributed-hardware-as-a-service/)
- [RemoteLab goes open source](https://blog.domski.pl/remotelab-goes-open-source/)
- [RemoteLab can now plot data in real-time](https://blog.domski.pl/remotelab-can-now-plot-data-in-real-time/)

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

Each board has a status field that determines operation of the debugger service associated with given board. Three states are available:
- **established**, connection with the debugger session was established and it is currently **active**, unless you terminate current debug session another one cannot be started,
- **online**, debugger service is active and waiting for incoming connections,
- **offline**, debugger service is not running. It can be started using Start or Restart button.

Along side with development board model, dedicated serial device and features are displayed. 
Serial device allows to directly connect to the development board and communicate with it. 
Features are tag-like entities. Since each development board is equipped with a shield it greatly enhances capabilities of the development board. The given tag corresponds to port number in the shield schematic, thus allowing to determine what additional devices are connected or what MCU ports could be used for operation. The PDF with the schematic could be found [here](https://github.com/wdomski/remote-lab/blob/master/board-shield/Nucleo64-shield.pdf).

### Health status

In addition, the health status is being displayed. If a smiley face is being displayed it means that the debugger service is operational. However, when a warning is being displayed it means that the debugger service is not running. In this case restart of the debugger is recommended. 

### Serial console

In addition to providing path to serial device it is possible to open a serial console via web interface and directly read/send data and plot in real-time.

The serial console offers information to what serial port it was connected and to which development board. More over, it is possible to enable:
- auto scrolling (enabled by default),
- append CR,
- append LF,
- local echo (enabled by default).

The console automatically pulls data from serial device available on the server and sends it to web interface. It is possible to clear the console or stop data reception. Refresh rate for pulling data from serial device can be adjusted. It is possible to change it between 200 ms up to 2 seconds wit a 50 ms step. Default value is set to 500 ms.

**Attention!**
Currently, sharing of a serial console between users is not supported. The received that will be send randomly to all connected recipients. The status server provides information if the console is being used (1 next to the serial device) or is it idle (zero value next to the serial device).

### Real-time plotting

When in serial console it is possible to plot a graph in real-time. The data sent via serial port is parsed and displayed on a graph. By default plotting is disabled. It can be enabled by checking the *Use plotting* checkbox.

**Attention!**
The data has to be sent in specific format in order to be parsed correctly. The format is following:
```
value1;value2;value3;...[\r]\n
```
where values are separated by semicolon and the line ends with carriage return and new line characters (at least a new line is required).

The number of values is not limited. However, the number of values should be kept constant and consistent throughout the whole transmission. Thus, no additional values should be added or removed. Additionally, each value must be an integer or float value.

An example of a proper data frame:
```
10;2.1;-3.4;0.0\r\n
```
Above consists of 4 values: 10, 2.1, -3.4, 0.0.

Once the data is received it is parsed and displayed on the graph. The number of values is automatically detected and the number of curves is set accordingly. No manual configuration is required.

It is possible to clear the plot or purge it. *Clearing the plot* removes all data from the graph leaving curve configuration intact, thus preserving line colors. *Purging the plot* removes all data and curve configuration. It is useful when the data format has changed and the graph needs to be reinitialized.

The number of retained samples can be adjusted using the *MAx Samples* number field input below the plot. The default value is set to 10 samples.

#### Counter availability

It is possible to use a counter as X axis values. By default each sample is timestamped and added to the graph. However, it is possible to use a counter instead. The first value of a data frame is interpreted as a counter value. Therefore when counter usage is enabled the first value is used as a counter and will not be displayed on the graph.

It is necessary tu *Purge the plot* after enabling or disabling the counter usage.

#### Statistics

The plot offers simple statistics calculated based on received data:
- last received value,
- minimum value,
- maximum value,
- average value.

Additionally each dataset provides color identification for easier distinction between curves.

## Video preview (Video)

It provides a video-like experience. It allows to stream *image* directly from a connected camera device. For example, the camera can be placed directly above the connected boards in order to provide live vide feedback.

There is a possibility to enable auto-refresh option. This allows to refresh the image every 10 seconds without user's input.

# Available features (for super user)

The serwer allows to extend available features presented to the end user after providing super user password. This feature allows to manager resources more precisely and unlocks additional capabilities.

The password can be configured inside **RemoteLab/resources/config.yml** file. For *password* key enter MD5 hash of the password.

## Terminal window

Terminal console (on the server) is available via web interface. It allows to execute commands with shell-like experience. There are some limitations, mainly when executing a command it should finish. Only when the command finishes it will provide the output of the command, thus commands like watch, less will not work.

## Status server (Panel)

Besides options available for normal user, now the control of the debugger service is more granular. Super user can start or stop the debugger service independently. 

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
