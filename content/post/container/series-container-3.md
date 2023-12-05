---
title: "docker, net?"
date: 2023-12-02T16:01:23+08:00
lastmod: 2023-12-02T16:01:23+08:00
draft: false
tags: ["docker", "net"]
categories: ["container"]
author: "yesplease"
---


<!--more-->
## docker 默认的网络设备

```sh
# 列出不同的网络设备
docker network ls
# 专门查看网桥设备
brctl show

```

## 如果你的docker主机可以访问互联网，你会发现，容器创建后，默认也可以访问互联网, why?

docker会借助iptables，对docker0的IP段进行SNAT

![](https://cdn.jsdelivr.net/gh/cugbtang/image-repo/PicGo/20231208154856.png)


## 容器获取的IP是动态的，先来后到，先到先得，容器与IP并没有绑定死
```sh
docker inspect test2 | jq '.[].NetworkSettings.Networks.bridge.IPAddress'
```
## 如果想要让容器使用指定的IP地址，该怎么办呢？

>默认情况下，我们无法对容器指定固定的IP地址，除非我们自己创建一个新的虚拟交换机，当容器使用我们自己创建的交换机和对应的网段时，才支持对容器指定固定的IP地址。也就是说，当容器连接到默认的网络时，不支持对容器指定固定的IP地址，只有连接到自定义网络时，才能对容器指定固定的IP地址。

## 自定义网桥
```sh
docker network create test_net -d bridge -o com.docker.network.bridge.name=test_bridge --subnet "172.18.0.0/16" --gateway "172.18.0.1"

#查看主机上的网桥变化
brctl show

#查看主机上路由的变化
ip route show
# 或
route -n


```

## 默认的bridge网络和test_net网络是不通的
>查看路由表，路由条目写的都很清楚，不同的网段对应不通的接口，应该可以正常通讯才对，为什么就是无法ping通呢？
原因就是，docker会生成对应的iptables规则，阻断了默认网络和自定义桥网络之间的通讯。

删除STAGE-2中的前两条规则，即可让docker0中的容器和test_bridge中的容器进行通讯了

![](https://cdn.jsdelivr.net/gh/cugbtang/image-repo/PicGo/20231208154944.png)

但是，如果先将filter表中STAGE-2链中的规则删除，确保docker0和test_bridge能够互相通讯的情况下，会发现，即使是docker0和test_bridge之间的通讯，也是会被SNAT的（从docker0去往test_bridge，被SNAT成172.18.0.1，从test_bridge去往docker0，被SNAT成172.17.0.1），这是因为它们之间的通讯也是符合nat表中的两条SNAT规则的。造成这种情况的原因是，这两条SNAT规则没有指定固定的宿主机出口网卡（即没有使用-o指定宿主机网卡，而是使用！-o的方式把自己所在的网络内的网口排除在外）

![](https://cdn.jsdelivr.net/gh/cugbtang/image-repo/PicGo/20231208155011.png)


## 参考
- [docker(7): 网络初探](https://www.zsythink.net/archives/4409)
- [Docker与iptables docker与iptables详解](https://blog.51cto.com/u_16099349/6896881)