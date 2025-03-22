#!/usr/bin/python3

import psutil
import subprocess
import os
import time
import subprocess as sp

class DebuggerService():
    def __init__(self, devices, server, verbose=False):
        self._devices = devices
        self._server = server
        self._verbose = verbose

        self._board_types = {'l4': {'cfg': 'st_nucleo_l4.cfg', 'keys': ['stm32l4', 'nucleo-l4']}, 
                             'f4': {'cfg': 'st_nucleo_f4.cfg', 'keys': ['stm32f4', 'nucleo-f4']}, }

        self._debugger_services = ['openocd', 'st-util-repo', 'st-util']

    def _get_cfg(self, board):
        ret = 'st_nucleo_l4.cfg'
        board = board.lower()
        found = False
        for mcu_key, mcu_value in self._board_types.items():
            for cfg in mcu_value['keys']:
                if board.find(cfg.lower()) >= 0:
                    ret = mcu_value['cfg']
                    found = True
                    break
            if found:
                break
        return ret

    def _run_cmd(self, cmd, timeout=2.0, kill=True):
        os.system(cmd)
        # p = subprocess.Popen(cmd, shell=True)
        # kill_it = False
        # try:
        #     p.wait(timeout)
        # except subprocess.TimeoutExpired:
        #     kill_it = True
        # if kill and kill_it:
        #     p.kill()

    def kill(self, id='', board='', debugger='', port='', serial='', all=False, pid=''):
        pids = psutil.pids()

        # translate id to serial
        if id != '':
            for dev in self._devices:
                if id == dev['id'] and self._server == dev['server']:
                    serial = dev['serial']
        
        # translate port to serial
        if port != '':
            for dev in self._devices:
                if port == dev['port'] and self._server == dev['server']:
                    serial = dev['serial']

        try:
            pid_number = int(pid)
        except ValueError:
            pid_number = -1

        for pid_in_list in pids:
            p = psutil.Process(pid_in_list)
            if p.name() in self._debugger_services:
                cmdline = ' '.join(p.cmdline())
                if all \
                    or cmdline.find(serial) >= 0 \
                    or pid_number == pid_in_list:
                    if self._verbose:
                        print("Killing %d" % pid_in_list)
                    p.terminate()
                    ret = p.wait(1.0)
                    if ret is not None:
                        try:
                            p.kill()
                        except psutil.NoSuchProcess:
                            print("Process already killed %d" % pid_in_list)
                        except:
                            print("Can't kill %d" % pid_in_list)

    def _check(self, dev, id, board, debugger, port, serial, all):
        if dev['server'] == self._server:
                if all or id == dev['id'] or board == dev['board'] or port == dev['port'] or serial == dev['serial']:
                    return True
        return False

    def _ports(self, port):
        port_number = int(port)
        gdb_port = port
        tcl_port = str(port_number + 2000)
        telnet_port = str(port_number + 1000)
        return gdb_port, tcl_port, telnet_port

    def _start_service(self, dev):
        #board has to be enabled in the config file
        if dev['status'] != "active":
            return

        if dev['debugger_service']=="openocd":
            gdb_port, tcl_port, telnet_port = self._ports(dev['port'])
            cfg = self._get_cfg(dev['board'])
            command = 'nohup openocd -f /usr/local/share/openocd/scripts/board/%s ' \
                '-c "hla_serial %s; gdb_port %s; tcl_port %s; telnet_port %s;" &> /dev/null &' \
                % (cfg, dev['serial'], gdb_port, tcl_port, telnet_port)
            if self._verbose:
                print(command)
            subprocess.run(command, shell=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif dev['debugger_service']=="st-util-repo" or dev['debugger_service']=="st-util":
            gdb_port, _, _ = self._ports(dev['port'])
            command = 'nohup st-util --serial %s -p %s -m &> /dev/null &' \
                % (dev['serial'], gdb_port)
            if self._verbose:
                print(command)
            self._run_cmd(command)

    def start(self, id='', board='', debugger='', port='', serial='', all=False):
        for dev in self._devices:
            if self._check(dev, id, board, debugger, port, serial, all):
                self._start_service(dev)

    def restart(self, id='', board='', debugger='', port='', serial='', all=False):
        self.kill(id, board, debugger, port, serial, all)
        self.start(id, board, debugger, port, serial, all)
        
        
    def _send_telnet_command(self, port, command):
        tn = sp.Popen(['telnet', 'localhost', port], stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
        time.sleep(0.5)
        response = ""
        stdout, stderr = tn.communicate(command.encode('ascii') + b'\n')
        if b"On-Chip" in stdout:
            response = "Success"
        else:
            response = "Error"
        tn.stdin.close()
        tn.stdout.close()
        tn.stderr.close()
        tn.wait()
        return response

    def reset(self, id='', board='', debugger='', port='', serial='', all=False):
        response = ""
        for dev in self._devices:
            if dev['debugger_service'] != "openocd":
                continue
            if self._check(dev, id, board, debugger, port, serial, all):
                _, _, telnet_port = self._ports(dev['port'])
                response += self._send_telnet_command(telnet_port, "reset_config none")
                response += self._send_telnet_command(telnet_port, "reset")
        return response

    def halt(self, id='', board='', debugger='', port='', serial='', all=False):
        response = ""
        for dev in self._devices:
            if dev['debugger_service'] != "openocd":
                continue
            if self._check(dev, id, board, debugger, port, serial, all):
                _, _, telnet_port = self._ports(dev['port'])
                response += self._send_telnet_command(telnet_port, "halt")
        return response

    def resume(self, id='', board='', debugger='', port='', serial='', all=False):
        response = ""
        for dev in self._devices:
            if dev['debugger_service'] != "openocd":
                continue
            if self._check(dev, id, board, debugger, port, serial, all):
                _, _, telnet_port = self._ports(dev['port'])
                response += self._send_telnet_command(telnet_port, "resume")
        return response
                
    def list(self):
        pids = psutil.pids()
        processes = []
        for pid in pids:
            p = psutil.Process(pid)
            if p.name() in self._debugger_services:
                openocd_process = "PID: %d, cmdline: %s" % (pid, ' '.join(p.cmdline()))
                processes.append(openocd_process)
                if self._verbose:
                    print(openocd_process)
        return processes
