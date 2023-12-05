---
title: "docker桥接网络模式下开启端口映射，流量是如何绕过防火墙的"
date: 2023-12-01T16:01:23+08:00
lastmod: 2023-12-01T16:01:23+08:00
draft: false
tags: ["docker", "net"]
categories: ["container"]
author: "yesplease"
---


## 一、iptables

![](https://cdn.jsdelivr.net/gh/cugbtang/image-repo/PicGo/20231208165600.png)
- 五条链

  - PREROUTING链
PREROUTING链是最先生效的，当数据包到达网口时，即开始工作。同时由于其在raw,mangle,nat表中都存在，其执行的优先l顺序是：raw(PREROUTING)-->man
gle(PREROUTING)---->mangle(nat)
PREROUTING一般用作对包进行目标地址修改。比如将该包的目标地址，修改为非本机的另外的网络p,一般通过DNAT规则进行修改。
  - 路由决策(Routing Decision)
决定一个包该走哪个链。如果上述PREROUTING链对包进行了目标网络更改。那么决策会觉得这个是一个需要转发的数据包，于是会将该包转发给FORWARD链。
否则，该包会走NPUT链
  - FORWARD链
FORWARD在各表中生效的优先l顺序是：mangle(FORWARD)-->filter(FORWARD)
处理路由决策派发发过来的包，到这里的包一般目标网络地址在PREROUTING链被修改过
  - INPUT链
其生效顺序是：mangle(INPUT)-->filter(INPUT)
处理路由决策派发发过来的包，到这里的包一般目标网络地址在PREROUTING链没有被修改过。
  - OUTPUT链
在目标进程端口接收到输入数据包后，输出的数据包，将在这里进行规则应用。OUTPUT链在各表中生效的先后顺序是：
raw(OUTPUT)---->mangle(OUTPUT)----nat(OUTPUT)---->filter(OUTPUT)

- 四张表
  - tr:这里面的链条，规则，可以决定一个数据包是否可以到达目标进程端口
  - mangle:这里面的链条，规则，可以修改数据包的内容，比如t!
  - nat:这里面的链条，规测，可以修改源和目标的ip地址，从而进行包路由。
  - raw:这里面的链条，规则，能基于数据包的状态进行规则设定
- 规则
一个规则一般分为两大部分：
  - 匹配：即哪些数据包会命中这个规则，比如一个指定的，即是一个匹配规则
  - 动作：匹配到规则之后，需要做什么动作，是放行，还是拒绝

  动作分为以下几种：
  - ACCEPT:直接接受该数据包，不会再走其他链条和规则。比如fit©r中的iput表中的某个规则命中后，动作是ACCEPT,那么该数据包将被直接送达目标进程端口。
  - DROP:直接抛弃该数据包，并且没有任何返回。且不会再走其他链和规则
  - REJECT:跟DROP类似，但好歹还是会跟请求方返回一些拒绝信息，比如我们拒绝掉ICMP协议后，ping该主机，会返▣“destination host unreachable”
  - RETURN:当前规则不做任何理，返回。让给下一个规则处理
  - LOG:同RETURN类以，但只是会将请求信息记录到系统日志中，记录路径为：var/log/syslog or /var/log/.messages

### 1.1、查看某个表中有哪些链和规则
```sh
```




## 二、查看docker网桥模式下，端口映射的规则变化

- 启动一个端口映射的容器

```sh
 docker run --detach -p 8888:3306 --name some-mariadb1 --env MARIADB_USER=example-user --env MARIADB_PASSWORD=m@^x8bb6$d13ixuk --env MARIADB_ROOT_PASSWORD=m@^x8bb6$d13ixuk  mariadb:latest
```

- 查看nat表

   
    ![](https://cdn.jsdelivr.net/gh/cugbtang/image-repo/PicGo/20231208171939.png)
    - 访问192.168.1.2:8888
    - 数据包首先被nat表中的PREROUTING链命中
    - 转向DOCKER链
    - 被第2条规则命中，做了DNAT动作，访问变成了172.170.2:3306
    - 经过路由处理，转向FORWARD链
    - 命中FORWARD链中的第4条规则，最终访问被响应，也就可以从外部访问端口映射的服务了
    - 由于PREROUTING对包进行了目标地址的修改，于是路由决策会将该包路由到FORWARD链。所有表中的linput链将直接忽略。
    ![](https://cdn.jsdelivr.net/gh/cugbtang/image-repo/PicGo/20231208172613.png)
    



### 2.1、原因及解决方案

- 原因
由于数据包被更改了目标地址，于是路由策略将该包导向了FORWARD链。所以我们在INPUT链中再怎么定义规则，都无法限制外网对docker服务的访问。
- 解决方案
既然包导向了FORWARD链，那么可以在FORWARD链中拦截。DOCKER官方给的建议便是如此，比如，针对本文中的例子，我们可以添加如下规则，即可实现所有外部网络都无法访问docker中的服务：
  ```sh
  iptables -I DOCKER-USER -i eth0 -j DROP
  ```
  - DOCKER-USER是FORWARD链中第一个规则命中的链
  - 从外部网络进入的数据包，直接丢弃
