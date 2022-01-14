<!--
 * @Author: wuwenbo
 * @Date: 2021-12-10 21:37:43
 * @LastEditTime: 2021-12-10 21:52:12
 * @FilePath: /GPUWatch/README.md
-->
# GPUWatch
对GPU运行状态进行实时监控，如果GPU断开，则邮件报警
## 1. 需要安装`pynvml`包
```python
pip install pynvml
```
## 2. 功能
- 定时监控功能，可设定`update_interval`控制监控间隔时间长短
- 邮件报警功能，若波动小于所设定的阈值`bound`，则通过`smtplib`模块发送警报邮件
## 3. 参数输入
- GPU监控编号：`gpu_index`
- GPU显存允许波动范围：`bound`
- 监控间隔时间：`update_interval`
- 发送邮箱用户名：`mail_user`
- 发送邮箱密码(验证码)：`mail_pass`
- 发送邮箱地址：`sender`
- 接收邮箱地址：`receivers`（多个邮箱之间可通过`,`分隔）
## 4. 使用范例
`python main.py --gpu_index 0,1 --bound -0.2 --update_interval 10 --mail_user xxx -- mail_pass xxx --sender xxx@qq.com --receivers xxx@qq.com,yyy@qq.com`

---

## GPU状态信息监控
- client实现对设备GPU状态信息的获取，并且通过`json`发送给server
- server接收数据，并且将数据存放至数据库中，并提供功能接口，实现GPU状态数据检索

### 使用方式
- 在设备客户端部署`client.py`，并在后台运行

  ```bash
  nohup python -u client.py > monitor.log 2>&1 &
  ```

- 在服务器端部署`server.py`，并在后台运行

  ```bash
  nohup python -u server.py > monitor.log 2>&1 &
  ```

### 接口（端口：5089）
1. [GET] get_device
   - 功能：查询有哪些已经在监测中的设备
   - 发送：无
   - 返回：设备名称

2. [GET] get_data
   - 功能：查询设备具体状态信息
   - 发送：需要查询的设备编号（需要为数组格式）
   - 返回：设备具体状态信息
