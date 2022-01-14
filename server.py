import socket
import sys
import time
import csv
import pymysql

import threading

import json
from flask import Flask, jsonify, request
from gevent import pywsgi

from itertools import chain

from datetime import datetime, date

from flask.json import JSONEncoder
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return JSONEncoder.default(self, obj)

HOST = '' # Symbolic name meaning all available interfaces
PORT = 9494 # Arbitrary non-privileged port

BUFSIZE = 1024

class Thread_recv_data(threading.Thread):
    def __init__(self, host, port, db_user, db_pwd):
        super().__init__()
        self.host = host
        self.port = port
        self.server = None

        self.db_user = db_user
        self.db_pwd = db_pwd

        # data
        self.recv_msg, self.client_addr = None, None

    def create_socket(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error as msg:
            print('Failed to create socket. Error message: ' , msg)
            sys.exit()

        print('socket created')

    def bind_socket(self):
        try:
            self.server.bind((HOST, PORT))
        except socket.error as msg:
            print('Bind failed. Error msg:', msg)
            sys.exit()

        print('socket bind complete')

    def sql_saving(self, device_name, monitor_time, msg):
        db = pymysql.connect(host='', user='gaoya', password='gaoya', database="gpu_status")
        cursor = db.cursor()

        sql = "INSERT INTO `gpu_stat` (`device_name`, `monitor_time`, `msg`) VALUES (" + ",".join(["'" + x + "'" for x in [device_name, monitor_time, msg]]) + ")"

        try:
            # 执行sql语句
            cursor.execute(sql)
            # 提交到数据库执行
            db.commit()
        except:
            # 如果发生错误则回滚
            db.rollback()

        db.close()

    def run(self):
        self.create_socket()
        self.bind_socket()

        # Function for handling connections. This will be used to create threads
        while True:
            self.recv_msg, self.client_addr = self.server.recvfrom(BUFSIZE)
            try:
                self.recv_msg = json.loads(self.recv_msg)
                device_name = self.recv_msg['device_name']
                device_time = self.recv_msg['time']
                device_msg = self.recv_msg['msg']
                print(device_msg)
                # sql Saving
                self.sql_saving(str(device_name), device_time, json.dumps(device_msg))
            except:
                print("Error is occured")

            print(self.recv_msg)

        self.server.close()

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder
@app.route('/get_data', methods=['get'])
def get_data():
    devices = None

    if request.is_json:
        request_data = request.get_json()
        devices = request_data['query']
    else:
        print('not json')
        return jsonify('request should be json')

    data = {}
    res = {}

    if devices:
        db = pymysql.connect(host='', user='gaoya', password='gaoya', database="gpu_status")
        cursor = db.cursor()

        for dev in devices:

            sql = "SELECT device_name, monitor_time, msg FROM `gpu_stat` WHERE device_name=" + str(dev) + " ORDER BY id DESC LIMIT 1"
            try:
                # 执行SQL语句
                cursor.execute(sql)
                # 获取所有记录列表
                results = cursor.fetchone()

                if results:
                    data[results[0]] = {'gpu_time': results[1], 'gpu_status': results[2]}
            except:
                print("Error: unable to fetch data")

        db.close()

    res['msg'] = data
    return jsonify(res)

@app.route('/get_device', methods=['get'])
def get_device():
    if request.is_json:
        request_data = request.get_json()
    else:
        print('not json')
        return jsonify('request should be json')

    db = pymysql.connect(host='', user='gaoya', password='gaoya', database="gpu_status")
    cursor = db.cursor()
    res = {}
    sql = "SELECT DISTINCT device_name FROM `gpu_stat`"

    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        res['device'] = list(chain.from_iterable(results))
    except:
        print("Error: unable to fetch data")

    db.close()

    return jsonify(res)

if __name__ == '__main__':
    thread_data = Thread_recv_data(HOST, PORT, 'gaoya', 'gaoya')
    thread_data.start()

    server = pywsgi.WSGIServer(('0.0.0.0', 5089), app)
    server.serve_forever()
    # app.run(host='0.0.0.0', port=5089, debug=False)