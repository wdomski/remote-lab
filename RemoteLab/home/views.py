from django.shortcuts import render
from django.http import HttpResponse

import time
import socket
import multiprocessing
import subprocess
import hashlib

from utils.yaml import read_yaml

hostname = socket.gethostname()

config_file = "/home/pi/mcu-remote-work-pwr/resources/config.yml"
config = {"boards_config": "/home/pi/mcu-remote-work-pwr/resources/boards.json",
                  "password": ""}
config_read = read_yaml(config_file)
config.update(config_read)

class SessionSingleton:
    _session_processes = {}

    @classmethod
    def _init_value(cls) -> tuple:
        return tuple([None]*6)

    @classmethod
    def reset_process(cls, session_key: str):
        cls._session_processes[session_key] = cls._init_value()

    @classmethod
    def get_process(cls, session_key: str):
        if session_key not in cls._session_processes:
            cls.reset_process(session_key)
        return cls._session_processes[session_key]

    @classmethod
    def set_process(cls, session_key: str, process: tuple):
        cls._session_processes[session_key] = process


def get_status():
    data = {
        "hostname": hostname,
        "current_time": time.strftime("%H:%M:%S"),
    }
    return data


def home(request):
    data = get_status()
    return render(request, 'home/index.html', data)

def login(request):
    data = get_status()
    
    login_successful = request.session.get("login_successful", 0)
    if login_successful:
        return render(request, 'home/home.html', data)

    if "password" in request.POST:
        password = request.POST["password"]
        md5_password = hashlib.md5(password.encode()).hexdigest()
        if md5_password == config['password']:
            request.session["login_successful"] = 1
            data['message_type'] = "success"
            data['message'] = "Login successful."
            return render(request, 'home/index.html', data)
        else:
            data['message_type'] = "danger"
            data['message'] = "Bad password, try again."
            return render(request, 'home/login.html', data)
            
    return render(request, 'home/login.html', data)

def logout(request):
    data = get_status()
    
    request.session["login_successful"] = 0
    
    data['message_type'] = "success"
    data['message'] = "Logout successfully."
    
    return render(request, 'home/login.html', data)

def check_authorized(request):
    login_successful = request.session.get("login_successful", 0)
    if login_successful == 0:
        return render(request, 'home/unauthorized.html')
    return None


def read_output(pipe, queue):
    while True:
        if not pipe.closed:
            line = pipe.readline()
            if len(line) > 0:
                queue.put(line)
            else:
                queue.put(b'>>>Empty pipe\n')
                break
        else:
            print("Bye")
            break

def terminal(request):
    authorized = check_authorized(request)
    if authorized is not None:
        return authorized
    
    session_key = request.session.session_key
    process, queue_stdout, queue_stderr, reader_stdout, reader_stderr, reading_lock = SessionSingleton.get_process(
        session_key)

    if process is None or not reader_stdout.is_alive() or not reader_stderr.is_alive():
        if process is not None:
            process.terminate()
        process = subprocess.Popen(
            ["bash"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        queue_stdout = multiprocessing.Queue()
        queue_stderr = multiprocessing.Queue()
        reader_stdout = multiprocessing.Process(target=read_output,
                                                args=(process.stdout, queue_stdout))
        reader_stderr = multiprocessing.Process(target=read_output,
                                                args=(process.stderr, queue_stderr))
        reader_stdout.start()
        reader_stderr.start()
        reading_lock = multiprocessing.Lock()
        SessionSingleton.set_process(
            session_key, (process, queue_stdout, queue_stderr, reader_stdout, reader_stderr, reading_lock))

    if request.method == 'POST':
        command = request.POST.get('command', '')
        try:
            process.stdin.write(f"{command}\n".encode())
            process.stdin.flush()
        except BrokenPipeError:
            pass
    else:
        return render(request, 'home/terminal.html', {'command': '', 'output': ''})

    output = ""

    time.sleep(0.1)
    with reading_lock:
        if queue_stdout is not None:
            while not queue_stdout.empty():
                line = queue_stdout.get()
                output += line.decode()
        if queue_stderr is not None:
            while not queue_stderr.empty():
                line = queue_stderr.get()
                output += line.decode()

    return HttpResponse(output, content_type="text/plain")


def terminal_reset(request):
    authorized = check_authorized(request)
    if authorized is not None:
        return authorized
    
    session_key = request.session.session_key
    process, _, _, reader_stdout, reader_stderr, _ = SessionSingleton.get_process(
        session_key)

    if process is not None:
        reader_stdout.terminate()
        reader_stderr.terminate()
        process.terminate()

    SessionSingleton.reset_process(session_key)

    output = "reseted"

    return HttpResponse(output, content_type="text/plain")


def terminal_update(request):
    authorized = check_authorized(request)
    if authorized is not None:
        return authorized
        
    session_key = request.session.session_key
    process, queue_stdout, queue_stderr, _, _, reading_lock = SessionSingleton.get_process(
        session_key)

    output = ""
    if process is not None:
        if reading_lock.acquire(timeout=0.2):
            try:
                if queue_stdout is not None:
                    while not queue_stdout.empty():
                        line = queue_stdout.get()
                        output += line.decode()
                if queue_stderr is not None:
                    while not queue_stderr.empty():
                        line = queue_stderr.get()
                        output += line.decode()
            finally:
                reading_lock.release()

    return HttpResponse(output, content_type="text/plain")
