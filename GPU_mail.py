import email.mime.multipart
import email.mime.text
import smtplib
import os
import time
import datetime


class GPURobber:

    def __init__(self):
        """
            初始化邮件信息
            FROM_MAIL：用于发送邮件的邮箱
            SMTP_SERVER：FROM_MAIL 的 SMTP服务器
            SSL_PORT ： SMTP端口
            USER_PWD： SMTP授权码
            mail_list: 需要接收提醒的邮箱
            preList: 上次发送邮件的list列表
        """
        self.hasGPU = self.check_gpus()
        if not self.hasGPU:
            raise Exception('GPU is not available')
        self.FROM_MAIL = "xxx@126.com"
        self.SMTP_SERVER = 'xxx.126.com'
        self.SSL_PORT = '465'
        self.USER_PWD = "XXXXXXXXXX"
        self.mail_list = ['xxx@126.com','yyy@qq.com']

    def check_gpus(self):
        if not 'NVIDIA System Management' in os.popen('nvidia-smi -h').read():
            print("'nvidia-smi' tool not found.")
            return False
        return True

    def parse(self, line, qargs):
        '''
        line:
            a line of text
        qargs:
            query arguments
        return:
            a dict of gpu infos
        Pasing a line of csv format text returned by nvidia-smi
        '''
        numberic_args = ['memory.free', 'memory.total', 'power.draw', 'power.limit']
        power_manage_enable = lambda v: (not 'Not Support' in v)
        to_numberic = lambda v: float(v.upper().strip().replace('MIB', '').replace('W', ''))
        process = lambda k, v: (
            (int(to_numberic(v)) if power_manage_enable(v) else 1) if k in numberic_args else v.strip())
        return {k: process(k, v) for k, v in zip(qargs, line.strip().split(','))}

    def query_gpu(self, qargs=[]):
        '''
        qargs:
            query arguments
        return:
            a list of dict
        Querying GPUs infos
        '''
        qargs = ['index', 'gpu_name', 'memory.free', 'memory.total', 'power.draw', 'power.limit'] + qargs
        cmd = 'nvidia-smi --query-gpu={} --format=csv,noheader'.format(','.join(qargs))
        results = os.popen(cmd).readlines()
        return [self.parse(line, qargs) for line in results]

    def robber_gpu_by_mem(self,mem_rate=0.8):
        """
        其他筛选的方式可以根据这个方法实现，如根据power
        :param mem_rate: 内存空闲率阈值，大于该阈值的GPU才会提醒
        :return: 返回可用的gpu idx
        """
        gpus = self.query_gpu()
        gpu_idx = []
        for i in range(len(gpus)):
            if float(gpus[i]['memory.free'] / gpus[i]['memory.total']) >= mem_rate:
                gpu_idx.append(i)
        return gpu_idx

    def send_mail(self, to_mail, title, content):
        ret = True
        USER_NAME = self.FROM_MAIL  # 邮箱用户名
        msg = email.mime.multipart.MIMEMultipart()  # 实例化email对象
        msg['from'] = self.FROM_MAIL  # 对应发件人邮箱昵称、发件人邮箱账号
        msg['to'] = ';'.join(to_mail)  # 对应收件人邮箱昵称、收件人邮箱账号
        msg['subject'] = title  # 邮件的主题
        txt = email.mime.text.MIMEText(content)
        msg.attach(txt)
        try:
            smtp = smtplib.SMTP_SSL(self.SMTP_SERVER, self.SSL_PORT)
            smtp.ehlo()
            smtp.login(USER_NAME, self.USER_PWD)
            smtp.sendmail(self.FROM_MAIL, to_mail, str(msg))
            smtp.quit()
        except Exception as e:
            ret = False
            print(e)
        return ret

    def run(self, mem_rate, skip_time=[1, 7], mail_cd=3600, query_cd=60):
        """
        启动
        :param mem_rate: 显存空闲阈值
        :param skip_time: 不扫描的时间段，24小时制
        :param mail_cd: 发邮件提醒的间隔时间，默认一个小时内只发送一次
        :param query_cd: 遍历时间，默认1分钟一次
        :return:
        """
        while True:
            time_now = datetime.datetime.now()
            if time_now.hour > skip_time[0] and time_now.hour < skip_time[1]:
                time.sleep((time_now.hour - skip_time[1]) * 3600)
                continue
            # 判断最近是否发过邮件
            send = False
            # 显存剩余比例
            gpus = self.robber_gpu_by_mem(mem_rate)
            # 如果不一样，且不为空，发邮件
            if gpus:
                for to in self.mail_list:
                    # 隔5秒发一个人,防止被当成垃圾邮件
                    time.sleep(5)
                    send = self.send_mail(to, "GPU is available", "".join(str(gpus)))
                    print("send to " + to)
            # 如果最近发送过邮件，则休眠1小时
            if send:
                time.sleep(mail_cd)
            # 每分钟扫描一次
            time.sleep(query_cd)

if __name__ == "__main__":
    robber = GPURobber()
    robber.run(0.8)

