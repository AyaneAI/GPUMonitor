from pynvml import *
import threading

import smtplib
from email.mime.text import MIMEText

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--update_interval", default=10, type=float, help='Time between each two update')
parser.add_argument("--mail_user", type=str, default='xxx', help='sender email username')
parser.add_argument("--mail_pass", type=str, default='xxx', help='sender email password')
parser.add_argument("--sender", type=str, default='xxx@qq.com', help='sender email address')
parser.add_argument("--receivers", type=str, default='xxx@qq.com', help='receiver email address')
parser.add_argument("--gpu_index", type=str, default='0', help='gpu which should be monitored')
parser.add_argument("bound", type=float, default=-0.2, help='gpu acceptable variation bound')
args = parser.parse_args()

nvmlInit()

print("Driver Version:{}".format(nvmlSystemGetDriverVersion()))
print("CUDA Version:{}".format(nvmlSystemGetCudaDriverVersion()))
print("GPU Count:{}".format(nvmlDeviceGetCount()))

# GPU Device Number
deviceCount = nvmlDeviceGetCount()
for i in range(deviceCount):
    handle = nvmlDeviceGetHandleByIndex(i)
    print("GPU {}: {}".format(i, nvmlDeviceGetName(handle)))

gpus = [int(device_num) for device_num in args.gpu_index.split(',')]
handle = [nvmlDeviceGetHandleByIndex(gpu) for gpu in gpus]

print("---------- DEVICE DETAILS ----------")

for i in range(len(gpus)):
    print("Device: {}".format(gpus[i]))
    meminfo = nvmlDeviceGetMemoryInfo(handle[i])
    print("GPU Total: {}GB".format(meminfo.total / (1024 ** 2)))
    print("GPU Used: {}GB".format(meminfo.used / (1024 ** 2)))
    print("GPU Free: {}GB".format(meminfo.free / (1024 ** 2)))

    print("Temperature is {} C".format(nvmlDeviceGetTemperature(handle[i], 0)))

RECEIVERS = [address.strip() for address in args.receivers.split(',')]


def send_Abnormal(gpu, Usage):
    # 设置服务器所需信息
    # qq邮箱服务器地址
    mail_host = 'smtp.qq.com'
    # qq用户名
    mail_user = args.mail_user
    # 密码(部分邮箱为授权码)
    mail_pass = args.mail_pass
    # 邮件发送方邮箱地址
    sender = args.sender
    # 邮件接受方邮箱地址，注意需要[]包裹，这意味着你可以写多个邮件地址群发
    receivers = RECEIVERS

    # 设置email信息
    # 邮件内容设置

    message = MIMEText('GPU{} Memory Abnormal, Usage Now: {}'.format(gpu, Usage), 'plain', 'utf-8')
    # 邮件主题
    message['Subject'] = 'GPU Abnormal'
    # 发送方信息
    message['From'] = sender
    # 接受方信息
    message['To'] = receivers[0]

    # 登录并发送邮件
    try:
        # 连接到服务器
        smtpObj = smtplib.SMTP_SSL(mail_host)
        # 登录到服务器
        smtpObj.login(mail_user, mail_pass)
        # 发送
        smtpObj.sendmail(
            sender, receivers, message.as_string())
        # 退出
        smtpObj.quit()
        print('success')
    except smtplib.SMTPException as e:
        print('error', e)  # 打印错误


MEMORY_Pre = [0.0] * len(gpus)


def gpu_timer():
    global MEMORY_Pre
    # usageinfo = nvmlDeviceGetUtilizationRates(handle)
    for i in range(len(gpus)):
        meminfo = nvmlDeviceGetMemoryInfo(handle[i])
        print("GPU: {} Used: {}GB".format(gpus[i], meminfo.used / (1024 ** 2)))
        if (meminfo.used - MEMORY_Pre[i]) / meminfo.total < args.bound:
            print("down")
            send_Abnormal(gpus[i], meminfo.used / (1024 ** 2))
        MEMORY_Pre[i] = meminfo.used

    global timer
    timer = threading.Timer(args.update_interval, gpu_timer)
    timer.start()


if __name__ == "__main__":
    timer = threading.Timer(1, gpu_timer)
    timer.start()