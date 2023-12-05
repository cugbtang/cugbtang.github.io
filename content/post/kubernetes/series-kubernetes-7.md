---
title: "flannel vxlan, check sum"
date: 2022-12-07T16:01:23+08:00
lastmod: 2022-12-07T16:01:23+08:00
draft: false
tags: ["kubernetes", "FAQ"]
categories: ["kubernetes", "cloudnative"]
author: "yesplease"
---


集群内pod无法dig mysql.middleware
修改主机dns nameserver为集群core dns地址，主机上可以dig mysql.middleware

## 一、问题分析

从pod内发出的请求数据包到flannel网卡时出现问题


## 二、抓包分析

- 环境 

    |类型|地址|网卡|flannel地址|docker0地址
    |---|---|---|---|---|
    |宿主机|192.168.189.5|eth0|172.30.17.0/32|172.30.17.0/24|
    |宿主机|192.168.189.3|eth0|172.30.44.0/32|172.30.44.0/24|


- 修改192.168.189.5主机的nameserver，主机上，dig  mysql.middleware.svc.cluster.local

  - 在192.168.189.3的eth0上抓包
    ```sh
    # tcpdump -i eth0 -nnvvS  udp and   host 192.168.189.5 and  host 192.168.189.3

    10:00:45.171729 IP (tos 0x0, ttl 64, id 25021, offset 0, flags [none], proto UDP (17), length 153)
        192.168.189.5.37578 > 192.168.189.3.8472: [udp sum ok] OTV, flags [I] (0x08), overlay 0, instance 1
    IP (tos 0x0, ttl 64, id 56488, offset 0, flags [none], proto UDP (17), length 103)
        172.30.17.0.6570 > 172.30.44.4.53: [udp sum ok] 30379+ [1au] A? mysql.middleware.svc.cluster.local. ar: . OPT UDPsize=4096 [COOKIE 8dd7b1a036b9e96b] (75)

    10:00:45.172148 IP (tos 0x0, ttl 64, id 11850, offset 0, flags [none], proto UDP (17), length 203)
        192.168.189.3.39446 > 192.168.189.5.8472: [bad udp cksum 0x7427 -> 0x6287!] OTV, flags [I] (0x08), overlay 0, instance 1
    IP (tos 0x0, ttl 63, id 61091, offset 0, flags [DF], proto UDP (17), length 153)
        172.30.44.4.53 > 172.30.17.0.6570: [bad udp cksum 0x95d7 -> 0x8437!] 30379*- q: A? mysql.middleware.svc.cluster.local. 1/0/1 mysql.middleware.svc.cluster.local. A 10.254.83.174 ar: . OPT UDPsize=2048 DO [COOKIE 8dd7b1a036b9e96b] (125)
    ```
  - 在192.168.189.3的flannel.1上抓包

    ```sh
    # tcpdump -i flannel.1 -nnvvS  host 172.30.44.4  or  172.30.44.0 and  host 172.30.17.0

    172.30.17.0.28706 > 172.30.44.4.53: [udp sum ok] 20554+ [1au] A? mysql.middleware.svc.cluster.local. ar: . OPT UDPsize=4096 [COOKIE 02885f0fcec139cb] (75)
    10:14:09.100234 IP (tos 0x0, ttl 63, id 25272, offset 0, flags [DF], proto UDP (17), length 153)
        172.30.44.4.53 > 172.30.17.0.28706: [bad udp cksum 0x95d7 -> 0xcda2!] 20554*- q: A? mysql.middleware.svc.cluster.local. 1/0/1 mysql.middleware.svc.cluster.local. A 10.254.83.174 ar: . OPT UDPsize=4096 [COOKIE 02885f0fcec139cb] (125)

    ```



  - 注意：请求来的时候sum ok，回的时候 bad

- 在192.168.189.5的一个pod内，dig  mysql.middleware.svc.cluster.local
  - 在192.168.189.3的eth0上抓包

    ```sh
    # tcpdump -i eth0 -nnvvS  udp and   host 192.168.189.5 and  host 192.168.189.3

    10:20:11.021851 IP (tos 0x0, ttl 64, id 18100, offset 0, flags [none], proto UDP (17), length 153)
        192.168.189.5.54947 > 192.168.189.3.8472: [bad udp cksum 0x694b -> 0x37cc!] OTV, flags [I] (0x08), overlay 0, instance 1
    IP (tos 0x0, ttl 63, id 29991, offset 0, flags [none], proto UDP (17), length 103)
        172.30.17.0.42230 > 172.30.44.4.53: [udp sum ok] 38007+ [1au] A? mysql.middleware.svc.cluster.local. ar: . OPT UDPsize=1232 [COOKIE 8313fa6ef3e826cf] (75)

    10:20:16.026185 IP (tos 0x0, ttl 64, id 22564, offset 0, flags [none], proto UDP (17), length 153)
        192.168.189.5.29594 > 192.168.189.3.8472: [bad udp cksum 0x3c0a -> 0x9ad5!] OTV, flags [I] (0x08), overlay 0, instance 1
    IP (tos 0x0, ttl 63, id 1772, offset 0, flags [none], proto UDP (17), length 103)
        172.30.17.0.60334 > 172.30.44.4.53: [udp sum ok] 38007+ [1au] A? mysql.middleware.svc.cluster.local. ar: . OPT UDPsize=1232 [COOKIE 8313fa6ef3e826cf] (75)

    10:20:16.115807 IP (tos 0x0, ttl 64, id 22619, offset 0, flags [none], proto UDP (17), length 78)
        192.168.189.5.58541 > 192.168.189.3.8472: [udp sum ok] OTV, flags [I] (0x08), overlay 0, instance 1
    ARP, Ethernet (len 6), IPv4 (len 4), Request who-has 172.30.44.4 tell 172.30.17.0, length 28

    10:20:17.139797 IP (tos 0x0, ttl 64, id 22876, offset 0, flags [none], proto UDP (17), length 78)
        192.168.189.5.58541 > 192.168.189.3.8472: [udp sum ok] OTV, flags [I] (0x08), overlay 0, instance 1
    ARP, Ethernet (len 6), IPv4 (len 4), Request who-has 172.30.44.4 tell 172.30.17.0, length 28

    10:20:18.163773 IP (tos 0x0, ttl 64, id 23179, offset 0, flags [none], proto UDP (17), length 78)
        192.168.189.5.58541 > 192.168.189.3.8472: [udp sum ok] OTV, flags [I] (0x08), overlay 0, instance 1
    ARP, Ethernet (len 6), IPv4 (len 4), Request who-has 172.30.44.4 tell 172.30.17.0, length 28

    ```

  - 在192.168.189.3的flannel.1上抓包
    ```sh
    # tcpdump -i flannel.1 -nnvvS  host 172.30.44.4  or  172.30.44.0 and  host 172.30.17.0

    10:20:16.115829 ARP, Ethernet (len 6), IPv4 (len 4), Request who-has 172.30.44.4 tell 172.30.17.0, length 28
    10:20:17.139812 ARP, Ethernet (len 6), IPv4 (len 4), Request who-has 172.30.44.4 tell 172.30.17.0, length 28
    10:20:18.163795 ARP, Ethernet (len 6), IPv4 (len 4), Request who-has 172.30.44.4 tell 172.30.17.0, length 28
    ```



  - 注意：dig的udp请求来的时候sum bad了，似乎被内核网络丢弃了
    pod内发送的udp数据包不能正常到达

- 在192.168.189.5的一个pod内，curl 172.30.44.4:53
  - 在192.168.189.3的eth0上抓包
    ```sh
    # tcpdump -i eth0 -nnvvS  udp and   host 192.168.189.5 and  host 192.168.189.3

    10:25:36.561653 IP (tos 0x0, ttl 64, id 27101, offset 0, flags [none], proto UDP (17), length 110)
        192.168.189.5.60121 > 192.168.189.3.8472: [udp sum ok] OTV, flags [I] (0x08), overlay 0, instance 1
    IP (tos 0x0, ttl 63, id 57662, offset 0, flags [DF], proto TCP (6), length 60)
        172.30.17.0.57972 > 172.30.44.4.53: Flags [S], cksum 0x3e44 (correct), seq 1333049522, win 64860, options [mss 1410,sackOK,TS val 115443102 ecr 0,nop,wscale 7], length 0

    10:25:36.561757 IP (tos 0x0, ttl 64, id 10781, offset 0, flags [none], proto UDP (17), length 110)
        192.168.189.3.50170 > 192.168.189.5.8472: [bad udp cksum 0x4a95 -> 0x80d1!] OTV, flags [I] (0x08), overlay 0, instance 1
    IP (tos 0x0, ttl 63, id 0, offset 0, flags [DF], proto TCP (6), length 60)
        172.30.44.4.53 > 172.30.17.0.57972: Flags [S.], cksum 0x956f (incorrect -> 0xcbab), seq 2031558188, ack 1333049523, win 64308, options [mss 1410,sackOK,TS val 3396801268 ecr 115443102,nop,wscale 7], length 0

    10:25:36.561993 IP (tos 0x0, ttl 64, id 27102, offset 0, flags [none], proto UDP (17), length 102)
        192.168.189.5.60121 > 192.168.189.3.8472: [udp sum ok] OTV, flags [I] (0x08), overlay 0, instance 1
    IP (tos 0x0, ttl 63, id 57663, offset 0, flags [DF], proto TCP (6), length 52)
        172.30.17.0.57972 > 172.30.44.4.53: Flags [.], cksum 0xf37e (correct), seq 1333049523, ack 2031558189, win 507, options [nop,nop,TS val 115443103 ecr 3396801268], length 0

    10:25:36.562083 IP (tos 0x0, ttl 64, id 27103, offset 0, flags [none], proto UDP (17), length 179)
        192.168.189.5.60121 > 192.168.189.3.8472: [udp sum ok] OTV, flags [I] (0x08), overlay 0, instance 1
    IP (tos 0x0, ttl 63, id 57664, offset 0, flags [DF], proto TCP (6), length 129)
        172.30.17.0.57972 > 172.30.44.4.53: Flags [P.], cksum 0x9dd2 (correct), seq 1333049523:1333049600, ack 2031558189, win 507, options [nop,nop,TS val 115443103 ecr 3396801268], length 77 [prefix length(18245) != length(75)] (invalid)

    10:25:36.562109 IP (tos 0x0, ttl 64, id 10782, offset 0, flags [none], proto UDP (17), length 102)
        192.168.189.3.50170 > 192.168.189.5.8472: [bad udp cksum 0x4a9d -> 0xa86b!] OTV, flags [I] (0x08), overlay 0, instance 1
    IP (tos 0x0, ttl 63, id 4244, offset 0, flags [DF], proto TCP (6), length 52)
        172.30.44.4.53 > 172.30.17.0.57972: Flags [.], cksum 0x9567 (incorrect -> 0xf335), seq 2031558189, ack 1333049600, win 502, options [nop,nop,TS val 3396801269 ecr 115443103], length 0

    10:25:38.562312 IP (tos 0x0, ttl 64, id 12090, offset 0, flags [none], proto UDP (17), length 102)
        192.168.189.3.50170 > 192.168.189.5.8472: [bad udp cksum 0x4a9d -> 0xa09a!] OTV, flags [I] (0x08), overlay 0, instance 1
    IP (tos 0x0, ttl 63, id 4245, offset 0, flags [DF], proto TCP (6), length 52)
        172.30.44.4.53 > 172.30.17.0.57972: Flags [F.], cksum 0x9567 (incorrect -> 0xeb64), seq 2031558189, ack 1333049600, win 502, options [nop,nop,TS val 3396803269 ecr 115443103], length 0

    10:25:38.562435 IP (tos 0x0, ttl 64, id 28447, offset 0, flags [none], proto UDP (17), length 102)
        192.168.189.5.60121 > 192.168.189.3.8472: [udp sum ok] OTV, flags [I] (0x08), overlay 0, instance 1
    IP (tos 0x0, ttl 63, id 57665, offset 0, flags [DF], proto TCP (6), length 52)
        172.30.17.0.57972 > 172.30.44.4.53: Flags [F.], cksum 0xe38e (correct), seq 1333049600, ack 2031558190, win 507, options [nop,nop,TS val 115445103 ecr 3396803269], length 0

    10:25:38.562519 IP (tos 0x0, ttl 64, id 12091, offset 0, flags [none], proto UDP (17), length 102)
        192.168.189.3.50170 > 192.168.189.5.8472: [bad udp cksum 0x4a9d -> 0x98c9!] OTV, flags [I] (0x08), overlay 0, instance 1
    IP (tos 0x0, ttl 63, id 4246, offset 0, flags [DF], proto TCP (6), length 52)
        172.30.44.4.53 > 172.30.17.0.57972: Flags [.], cksum 0x9567 (incorrect -> 0xe393), seq 2031558190, ack 1333049601, win 502, options [nop,nop,TS val 3396803269 ecr 115445103], length 0
    ```

  - 在192.168.189.3的flannel.1上抓包
    ```sh
    # tcpdump -i flannel.1 -nnvvS  host 172.30.44.4  or  172.30.44.0 and  host 172.30.17.0

    三次握手
    10:25:36.561678 IP (tos 0x0, ttl 63, id 57662, offset 0, flags [DF], proto TCP (6), length 60)
        172.30.17.0.57972 > 172.30.44.4.53: Flags [S], cksum 0x3e44 (correct), seq 1333049522, win 64860, options [mss 1410,sackOK,TS val 115443102 ecr 0,nop,wscale 7], length 0
    10:25:36.561744 IP (tos 0x0, ttl 63, id 0, offset 0, flags [DF], proto TCP (6), length 60)
        172.30.44.4.53 > 172.30.17.0.57972: Flags [S.], cksum 0x956f (incorrect -> 0xcbab), seq 2031558188, ack 1333049523, win 64308, options [mss 1410,sackOK,TS val 3396801268 ecr 115443102,nop,wscale 7], length 0
    10:25:36.561998 IP (tos 0x0, ttl 63, id 57663, offset 0, flags [DF], proto TCP (6), length 52)
        172.30.17.0.57972 > 172.30.44.4.53: Flags [.], cksum 0xf37e (correct), seq 1333049523, ack 2031558189, win 507, options [nop,nop,TS val 115443103 ecr 3396801268], length 0

    四次挥手
    10:25:36.562088 IP (tos 0x0, ttl 63, id 57664, offset 0, flags [DF], proto TCP (6), length 129)
        172.30.17.0.57972 > 172.30.44.4.53: Flags [P.], cksum 0x9dd2 (correct), seq 1333049523:1333049600, ack 2031558189, win 507, options [nop,nop,TS val 115443103 ecr 3396801268], length 77 [prefix length(18245) != length(75)] (invalid)

    10:25:36.562105 IP (tos 0x0, ttl 63, id 4244, offset 0, flags [DF], proto TCP (6), length 52)
        172.30.44.4.53 > 172.30.17.0.57972: Flags [.], cksum 0x9567 (incorrect -> 0xf335), seq 2031558189, ack 1333049600, win 502, options [nop,nop,TS val 3396801269 ecr 115443103], length 0
    10:25:38.562279 IP (tos 0x0, ttl 63, id 4245, offset 0, flags [DF], proto TCP (6), length 52)
        172.30.44.4.53 > 172.30.17.0.57972: Flags [F.], cksum 0x9567 (incorrect -> 0xeb64), seq 2031558189, ack 1333049600, win 502, options [nop,nop,TS val 3396803269 ecr 115443103], length 0

    10:25:38.562447 IP (tos 0x0, ttl 63, id 57665, offset 0, flags [DF], proto TCP (6), length 52)
        172.30.17.0.57972 > 172.30.44.4.53: Flags [F.], cksum 0xe38e (correct), seq 1333049600, ack 2031558190, win 507, options [nop,nop,TS val 115445103 ecr 3396803269], length 0
    10:25:38.562512 IP (tos 0x0, ttl 63, id 4246, offset 0, flags [DF], proto TCP (6), length 52)
        172.30.44.4.53 > 172.30.17.0.57972: Flags [.], cksum 0x9567 (incorrect -> 0xe393), seq 2031558190, ack 1333049601, win 502, options [nop,nop,TS val 3396803269 ecr 115445103], length 0

    ```
  - pod内发送的tcp数据包可以正常发送


## 三、解决方案，关闭外层udp数据包检测
要在Linux中设置网卡或内核参数以允许数据包不进行校验和计算，可以使用ethtool工具或sysctl进行配置。

### 2.1、使用ethtool工具（推荐）

1. 首先，确保你已经安装了ethtool工具。如果没有安装，可以通过包管理器进行安装，比如在Ubuntu上可以使用以下命令：

   ```bash
   sudo apt-get install ethtool
   ```

2. 然后，使用ethtool来设置网卡参数。例如，要禁用网卡的校验和计算，可以使用以下命令：

   ```bash
   sudo ethtool -K eth0 tx off rx off
   ```

   这将禁用eth0网卡的发送和接收校验和计算。

### 2.2、使用sysctl设置内核参数（测试了这种方式似乎不生效）

1. 打开文件`/etc/sysctl.conf`：

   ```bash
   sudo nano /etc/sysctl.conf
   ```

2. 在文件末尾添加以下行以禁用校验和：

   ```bash
   net.ipv4.tcp_checksum = 0
   ```

3. 保存并关闭文件后，执行以下命令使更改生效：

   ```bash
   sudo sysctl -p
   ```



