# ------ essential plugin needed to setup: pynvml -------
from pynvml import *
import argparse

import datetime
import json

import socket

parser = argparse.ArgumentParser()
parser.add_argument("--update_interval", default=300, type=float, help='update each minute')
parser.add_argument("--device_name", default=3090, type=str, help='device name')

args = parser.parse_args()

nvmlInit()

class GPU:
    def __init__(self, ip, port):
        print("Driver Version:{}".format(str(nvmlSystemGetDriverVersion(), 'utf-8')))
        print("CUDA Version:{}".format(nvmlSystemGetCudaDriverVersion()))
        print("GPU Count:{}".format(nvmlDeviceGetCount()))

        self.client = None
        self.ip = ip
        self.port = port

        self.timer = None

    def socket_create(self):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error as msg:
            print('Failed to create socket. Error message: ' , msg)
            sys.exit()

    def timer_create(self):
        self.timer = threading.Timer(1, self.gpu_timer)

    def socket_send(self, gpu_status, ip, port):
        self.client.sendto(json.dumps(gpu_status).encode("utf-8"), (ip, port))

    def gpu_timer(self):
        local_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        device_count = nvmlDeviceGetCount()
        gpu_status = {'device_name': args.device_name, 'time': local_time, 'msg':{}}
        print("----------", local_time, "----------")
        for i in range(device_count):
            handle = nvmlDeviceGetHandleByIndex(i)
            meminfo = nvmlDeviceGetMemoryInfo(handle)

            print("GPU {}: {}".format(i, str(nvmlDeviceGetName(handle), 'utf-8')))
            print("GPU Total: {}GB".format(round(meminfo.total / (1024 ** 3), 2)))
            print("GPU Used: {}GB".format(round(meminfo.used / (1024 ** 3), 2)))
            print("GPU Free: {}GB".format(round(meminfo.free / (1024 ** 3), 2)))

            print("Temperature is {} C".format(nvmlDeviceGetTemperature(handle, 0)))
            print("Fan speed is {} %".format(nvmlDeviceGetFanSpeed(handle)))
            print("Power status {}".format(nvmlDeviceGetPowerState(handle)))

            status = {}
            status['GPU_Type'] = str(nvmlDeviceGetName(handle), 'utf-8')
            status['GPU_Used'] = round(meminfo.used / (1024 ** 3), 2)
            status['GPU_Usage'] = round(meminfo.used / meminfo.total, 2)
            status['GPU_Temp'] = nvmlDeviceGetTemperature(handle, 0)
            status['Fan_Speed'] = nvmlDeviceGetFanSpeed(handle)
            gpu_status['msg'][i] = status

            self.socket_send(gpu_status, self.ip, self.port)

        self.timer = threading.Timer(args.update_interval, self.gpu_timer)
        self.timer.start()

    def run(self):
        self.socket_create()
        self.timer_create()
        self.timer.start()

    def stop(self):
        self.client.close()
        self.timer.cancel()


if __name__ == "__main__":
    gpu = GPU("120.25.2.31", 9494)
    gpu.run()
