# GPU_robber
Monitor the GPUs wether is available and reminder by email

实时监控服务器是否有可用的GPU，并及时发送提醒。

默认采用的是GPU显存空闲率大于80%提醒，可以根据需要自行调整。

如果出现SMTP error：554的异常，说明邮件发送被反垃圾邮件系统侦测到了，可以适当调整发送每个邮件的间隔时间

使用之前请把用于发送邮件的邮箱的SMTP服务打开，并且取得授权码。
