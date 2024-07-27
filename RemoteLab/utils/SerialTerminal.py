
import time
import serial
import queue
from multiprocessing import Process, Queue, Event
from threading import Thread, Lock

class SerialHandler:
    def __init__(self):
        pass

    def run(self, device, queue_in, queue_out, event_read, event_close):
        s = serial.Serial(device, 115200, timeout=0.1)

        data_read = b''
        last_read_event = time.time()
        
        if s.is_open:
            s.reset_input_buffer()
            s.reset_output_buffer()

        while s.is_open:
            data_read += s.read(10000)
            if event_read.is_set():
                event_read.clear()
                last_read_event = time.time()
                if len(data_read) > 0:
                    queue_out.put(data_read)
                    data_read = b''

            current_time = time.time()
            if current_time > last_read_event + 10.0:
                data_read = b''
                last_read_event = current_time

            while not queue_in.empty():
                data_write = queue_in.get()
                s.write(data_write.encode('utf-8'))
                
            if event_close.is_set():
                print(f"Closing device {device}")
                break
            
        if s.is_open:
            s.close()

class SerialGovernor:
    def __init__(self, close_delay=10):
        self._serial_list = {}
        self._lock = Lock()
        self._close_delay = close_delay

    def add_serial(self, serial_device):
        sh = SerialHandler()
        queue_in = Queue()
        queue_out = Queue()
        event_read = Event()
        event_close = Event()
        p = Process(target=sh.run, args=(serial_device, queue_in, queue_out, event_read, event_close))
        p_watcher = Thread(target=self._watch_action, args=(serial_device, event_close, self._lock, self._close_delay))

        self._serial_list[serial_device] = {'queue_in': queue_in, 'queue_out': queue_out, 'event_read': event_read, 
                                            'process': p, 'event_close': event_close,
                                            'last_action': time.time(),
                                            'watcher': p_watcher}
        
        p.start()
        p_watcher.start()
        
    def _watch_action(self, serial_device, event_close, lock, delay):
        while True:
            diff = 0
            if lock.acquire(blocking=True, timeout=1.0):
                diff = time.time() - self._serial_list[serial_device]['last_action'] 
                if diff > delay:
                    del self._serial_list[serial_device]
                    lock.release()
                    event_close.set()
                    break
                lock.release()   

    def put_to_queue_out(self, serial_device, data):
        if serial_device not in self._serial_list:
            self.add_serial(serial_device)
        self._serial_list[serial_device]['queue_out'].put(data)

    def read(self, serial_device):
        self._lock.acquire()
        if serial_device in self._serial_list:
            self._serial_list[serial_device]['last_action'] = time.time()
        self._lock.release()
        
        if serial_device not in self._serial_list:
            self.add_serial(serial_device)

        data = None
        self._serial_list[serial_device]['event_read'].set()
        try:
            data = self._serial_list[serial_device]['queue_out'].get(timeout=1.0)
        except queue.Empty:
            pass

        if data is not None:
            try:
                data = data.decode('utf-8')
            except UnicodeDecodeError:
                return ""
            return data
        
        return ""

    def write(self, serial_device, data):
        self._lock.acquire()
        if serial_device in self._serial_list:
            self._serial_list[serial_device]['last_action'] = time.time()
        self._lock.release()
        
        if serial_device not in self._serial_list:
            self.add_serial(serial_device)
        data = data.replace("\\\\", "\\")
        self._serial_list[serial_device]['queue_in'].put(data)
        
    def in_use(self, serial_device):
        if serial_device in self._serial_list:
            return True
        return False