---
title: "namespace && cgroups "
date: 2022-06-01T16:01:23+08:00
lastmod: 2022-06-01T16:01:23+08:00
draft: false
tags: ["kubernetes", "term"]
categories: ["kubernetes", "cloudnative"]
author: "yesplease"
---

## namespace

- 定义

  >​		namespace是 Linux 内核的一项功能，该功能对内核资源进行分区，以使一组进程看到一组资源，而另一组进程看到另一组资源。namespace 的工作方式通过为一组资源和进程设置相同的 namespace 而起作用，但是这些 namespace 引用了不同的资源。资源可能存在于多个 namespace 中。这些资源可以是进程ID、主机名、用户ID、文件名、与网络访问相关的名称和进程间通信。

- 特征

  > ​        可以实现在同一主机系统中对进程ID、主机名、用户名ID、文件名、网络和进程间通信等资源的隔离

- 类型

|            namespace            |                 summary                  | kernel | describe                                                     |
| :-----------------------------: | :--------------------------------------: | :----: | ------------------------------------------------------------ |
|           Mount(mnt)            |                隔离挂载点                | 2.4.19 | 隔离不同的进程或进程组看到的挂载点，实现容器内只能看到自己的挂在信息，在容器内的挂载操作不会影响主机的挂载目录 |
|         Process ID(pid)         |               隔离进程 ID                | 2.6.24 |                                                              |
|          Network(net)           |          隔离网络设备，端口号等          | 2.6.29 |                                                              |
| Interprocess Communication(ipc) | 隔离 System VIPC 和 POSIX message queues | 2.6.19 |                                                              |
|       UTS Namespace(uts)        |             隔离主机名和域名             | 2.6.19 |                                                              |
|      User Namespace(user)       |             隔离用户和用户组             |  3.8   |                                                              |
| Control group(cgroup) Namespce  |           隔离 Cgroups 根目录            |  4.6   |                                                              |
|         Time Namespace          |               隔离系统时间               |  5.6   |                                                              |

## Mount Namespace

> 使用 unshare 命令可以新建 Mount Namespace，并且在新建的 Mount Namespace 内 mount 是和外部完全隔离的。

- 创建一个bash 进程并且新建一个 Mount Namespace

  ```bash
  [vagrant@localhost ~]$ sudo unshare --mount --fork /bin/bash
  [root@localhost vagrant]#
  ```

- 验证在独立的 namespce 内挂载文件，不影响别的

  在 /tmp 目录下创建一个目录

  ```bash
  [root@localhost vagrant]# mkdir /tmp/tmpfs
  ```

- 使用 mount 命令挂载一个 tmpfs 类型的目录

  ```bash
  [root@localhost vagrant]# mount -t tmpfs -o size=20m tmpfs /tmp/tmpfs
  ```

- 使用 df 命令查看已经挂载的目录信息

  ```bash
  [root@localhost vagrant]# df -h
  Filesystem                                                                          Size  Used Avail Use% Mounted on
  /dev/sda1                                                                            40G  3.8G   37G  10% /
  devtmpfs                                                                            457M     0  457M   0% /dev
  tmpfs                                                                               464M     0  464M   0% /dev/shm
  tmpfs                                                                               464M     0  464M   0% /sys/fs/cgroup
  tmpfs                                                                               464M   13M  451M   3% /run
  tmpfs                                                                                93M     0   93M   0% /run/user/1000
  //172.29.0.1/vgt-2469b42ebff188de622646551002b263-6ad5fdbcbf2eaa93bd62f92333a2e6e5  466G  171G  295G  37% /vagrant
  tmpfs                                                                                20M     0   20M   0% /tmp/tmpfs
  ```

- 新打开一个命令窗口，执行 df 命令查看主机的挂载信息

  ```bash
  [vagrant@localhost ~]$ df -h
  Filesystem                                                                          Size  Used Avail Use% Mounted on
  devtmpfs                                                                            457M     0  457M   0% /dev
  tmpfs                                                                               464M     0  464M   0% /dev/shm
  tmpfs                                                                               464M   13M  451M   3% /run
  tmpfs                                                                               464M     0  464M   0% /sys/fs/cgroup
  /dev/sda1                                                                            40G  3.8G   37G  10% /
  //172.29.0.1/vgt-2469b42ebff188de622646551002b263-6ad5fdbcbf2eaa93bd62f92333a2e6e5  466G  171G  295G  37% /vagrant
  tmpfs                                                                                93M     0   93M   0% /run/user/1000
  ```

- 基本验证完毕。接着我们查看新的mount namespace 信息

  ```sh
  [root@localhost vagrant]# ls -l /proc/self/ns/
  total 0
  lrwxrwxrwx. 1 root root 0 Feb 26 09:56 ipc -> ipc:[4026531839]
  lrwxrwxrwx. 1 root root 0 Feb 26 09:56 mnt -> mnt:[4026532117]
  lrwxrwxrwx. 1 root root 0 Feb 26 09:56 net -> net:[4026531956]
  lrwxrwxrwx. 1 root root 0 Feb 26 09:56 pid -> pid:[4026531836]
  lrwxrwxrwx. 1 root root 0 Feb 26 09:56 user -> user:[4026531837]
  lrwxrwxrwx. 1 root root 0 Feb 26 09:56 uts -> uts:[4026531838]
  ```

- 新打开一个命令窗口，使用相同的命令查看主机上的 namespace 信息

  ```sh
  [vagrant@localhost ~]$ ls -l /proc/self/ns/
  total 0
  lrwxrwxrwx. 1 vagrant vagrant 0 Feb 26 09:57 ipc -> ipc:[4026531839]
  lrwxrwxrwx. 1 vagrant vagrant 0 Feb 26 09:57 mnt -> mnt:[4026531840]
  lrwxrwxrwx. 1 vagrant vagrant 0 Feb 26 09:57 net -> net:[4026531956]
  lrwxrwxrwx. 1 vagrant vagrant 0 Feb 26 09:57 pid -> pid:[4026531836]
  lrwxrwxrwx. 1 vagrant vagrant 0 Feb 26 09:57 user -> user:[4026531837]
  lrwxrwxrwx. 1 vagrant vagrant 0 Feb 26 09:57 uts -> uts:[4026531838]
  ```

## PID Namespace

> 用来隔离进程，在不同的namespace内可以拥有相同的进程号

- 创建一个 bash 进程，并且新建一个 PID Namespace

  ```sh
  [vagrant@localhost ~]$ sudo unshare --pid --fork --mount-proc /bin/bash
  [root@localhost vagrant]#
  ```

- 在当前的命令行窗口使用 ps aux 命令查看进程信息

  ```sh
  [root@localhost vagrant]# ps aux
  USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
  root         1  0.0  0.2  15792  2616 pts/3    S    13:59   0:00 /bin/bash
  root        16  0.0  0.1  55192  1844 pts/3    R+   14:02   0:00 ps aux
  ```

## UTS Namespace

> 它允许每个UTS Namespace 拥有一个独立的主机名

- 使用 unshare 命令创建一个 UTS Namespace

  ```sh
  [vagrant@localhost ~]$ sudo unshare --uts --fork /bin/bash
  [root@localhost vagrant]#
  ```

- 使用 hostname 命令设置主机

  ```sh
  [root@localhost vagrant]# hostname -b docker
  [root@localhost vagrant]# hostname
  docker
  ```

- 新打开一个命令行窗口，使用相同的命令查看主机的hostname

  ```sh
  [root@localhost vagrant]# localhost
  ```

## IPC Namespace

> 主要用来隔离进程间通信的。PID Namespace 和 IPC Namespace一起使用可以实现同一 IPC Namespace 内的进程彼此可以通信，不同 IPC Namespace 的进程却不能通信。

- 使用 unshare 命令创建一个 IPC Namespace

  ```sh
  [vagrant@docker ~]$ sudo unshare --ipc --fork /bin/bash
  ```

- 另起一个窗口，查看系统的通信进程

  ```sh
  [vagrant@docker ~]$ ipcs -q
  
  ------ Message Queues --------
  key        msqid      owner      perms      used-bytes   messages
  ```

- 在新的ipc namespace下新建一个进程通信队列

  ```sh
  [root@docker vagrant]# ipcmk -Q
  Message queue id: 0
  ```

- 查看当前ipc namespace 下的系统通信队列列表

  ```sh
  [root@docker vagrant]# ipcs -q
  
  ------ Message Queues --------
  key        msqid      owner      perms      used-bytes   messages
  0x2ae315e9 0          root       644        0            0
  ```

  

- 再次查看主机的系统通信队列

  ```sh
  [vagrant@docker ~]$ ipcs -q
  
  ------ Message Queues --------
  key        msqid      owner      perms      used-bytes   messages
  ```

## User Namespace

> 主要用来隔离用户和用户组。可以实现进程在容器内拥有 root 权限， 而在主机上却只是普通用户。

- 以普通用户的身份创建一个 User Namespace

  ```sh
  [vagrant@docker ~]$ unshare --user --fork /bin/bash
  unshare: unshare failed: Invalid argument
  # 查看内核版本
  [vagrant@docker ~]$ uname -a
  Linux docker 3.10.0-1127.el7.x86_64 #1 SMP Tue Mar 31 23:36:51 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux
  # 查阅资料
  # max_user_namespaces文件记录了允许创建的user namespace数量，我的CentOS 7.5默认是0，修改之
  echo 2147483647 > /proc/sys/user/max_user_namespaces
  # 再次运行
  [vagrant@docker ~]$ unshare --user -r /bin/bash
  [root@docker ~]#
  ```

- 执行 id 命令查看当前的用户信息

  ```sh
  [root@docker ~]# id
  uid=0(root) gid=0(root) groups=0(root),65534(nfsnobody) context=unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023
  ```

- 在当前窗口执行 reboot 命令

  ```sh
  [root@docker ~]# reboot
  Failed to open /dev/initctl: Permission denied
  Failed to talk to init daemon.
  ```

## Net Namespace

> 用来隔离网络设备、IP地址和端口等信息。
>
> 可以让每个进程拥有自己独立的IP地址，端口和网卡信息

- 首先查看主机上的ip 信息

  ```sh
  [vagrant@docker ~]$ ip a
  1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
      link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
      inet 127.0.0.1/8 scope host lo
         valid_lft forever preferred_lft forever
      inet6 ::1/128 scope host
         valid_lft forever preferred_lft forever
  2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
      link/ether 00:15:5d:25:01:09 brd ff:ff:ff:ff:ff:ff
      inet 172.29.5.132/20 brd 172.29.15.255 scope global noprefixroute dynamic eth0
         valid_lft 82979sec preferred_lft 82979sec
      inet6 fe80::215:5dff:fe25:109/64 scope link
         valid_lft forever preferred_lft forever
  3: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN group default
      link/ether 02:42:f0:82:11:e0 brd ff:ff:ff:ff:ff:ff
      inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
         valid_lft forever preferred_lft forever
  ```

- 创建 net namespace

  ```sh
  [vagrant@docker ~]$ sudo unshare --net --fork /bin/bash
  [root@docker vagrant]#
  ```

- 使用 ip a命令查看当前namespace的网络信息

  ```sh
  [root@docker vagrant]# ip a
  1: lo: <LOOPBACK> mtu 65536 qdisc noop state DOWN group default qlen 1000
      link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
  ```

## 为什么 docker 需要 namespace?

Linux 内核从2002年2.4.19版本开始加入了 Mount Namspace

内核3.8版本加入了 User Namespace 为容器提供了足够的支持功能

当 docker 新建一个容器时

会创建这六种 namespace， 然后将容器中的进程加入这些 namespace之中

# Cgroups

- 定义

  全程是 control groups， 是Linux 内核的一个功能。可以实现限制进程或者进程组的资源（cpu、mem、磁盘IO等）

- 特征

  资源限制：限制资源的使用量

  优先级控制： 不同的组可以有不用的资源使用优先级

  审计：计算控制组的资源使用情况

  控制： 控制进程的挂起或恢复

- 核心

  subsystem: 一个内核的组件，代表一类资源调度控制器

  cgroup： 表示一组进程和一组带有参数的子系统的关联关系

  hierarchy：由一些列的控制组按照树状结构排列组成的子控制组默认拥有父控制组的属性

## subsystem

- 查看当前主机使用了哪些子系统

  ```sh
  [vagrant@docker ~]$ sudo mount -t cgroup
  cgroup on /sys/fs/cgroup/systemd type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,xattr,release_agent=/usr/lib/systemd/systemd-cgroups-agent,name=systemd)
  cgroup on /sys/fs/cgroup/cpuset type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,cpuset)
  cgroup on /sys/fs/cgroup/cpu,cpuacct type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,cpuacct,cpu)
  cgroup on /sys/fs/cgroup/perf_event type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,perf_event)
  cgroup on /sys/fs/cgroup/blkio type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,blkio)
  cgroup on /sys/fs/cgroup/memory type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,memory)
  cgroup on /sys/fs/cgroup/hugetlb type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,hugetlb)
  cgroup on /sys/fs/cgroup/freezer type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,freezer)
  cgroup on /sys/fs/cgroup/net_cls,net_prio type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,net_prio,net_cls)
  cgroup on /sys/fs/cgroup/devices type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,devices)
  cgroup on /sys/fs/cgroup/pids type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,pids)
  ```

- 以 cpu 子系统为例，演示 cgroups 如何限制进程的 cpu使用时间

  ```sh
  #在cpu子系统下创建测试文件夹
  mkdir /sys/fs/cgroup/cpu/mydocker
  #查看
  [root@docker vagrant]# ls /sys/fs/cgroup/cpu/mydocker -l
  total 0
  -rw-r--r--. 1 root root 0 Feb 26 15:15 cgroup.clone_children
  --w--w--w-. 1 root root 0 Feb 26 15:15 cgroup.event_control
  -rw-r--r--. 1 root root 0 Feb 26 15:15 cgroup.procs
  -r--r--r--. 1 root root 0 Feb 26 15:15 cpuacct.stat
  -rw-r--r--. 1 root root 0 Feb 26 15:15 cpuacct.usage
  -r--r--r--. 1 root root 0 Feb 26 15:15 cpuacct.usage_percpu
  -rw-r--r--. 1 root root 0 Feb 26 15:15 cpu.cfs_period_us
  -rw-r--r--. 1 root root 0 Feb 26 15:15 cpu.cfs_quota_us
  -rw-r--r--. 1 root root 0 Feb 26 15:15 cpu.rt_period_us
  -rw-r--r--. 1 root root 0 Feb 26 15:15 cpu.rt_runtime_us
  -rw-r--r--. 1 root root 0 Feb 26 15:15 cpu.shares
  -r--r--r--. 1 root root 0 Feb 26 15:15 cpu.stat
  -rw-r--r--. 1 root root 0 Feb 26 15:15 notify_on_release
  -rw-r--r--. 1 root root 0 Feb 26 15:15 tasks
  # 将当前shell进程加入cgroup
  [root@docker mydocker]# echo $$> tasks
  # 查看tasks文件内容
  [root@docker mydocker]#
  ```

- mem

  ```sh
  # 在memory子系统下创建cgroup
  [root@docker mydocker]# mkdir /sys/fs/cgroup/memory/mydocker
  
  # 查看新建目录中的内容
  [root@docker mydocker]# ls
  cgroup.clone_children
  cgroup.event_control
  cgroup.procs
  memory.failcnt
  memory.force_empty
  memory.kmem.failcnt
  memory.kmem.limit_in_bytes
  memory.kmem.max_usage_in_bytes
  memory.kmem.slabinfo
  memory.kmem.tcp.failcnt
  memory.kmem.tcp.limit_in_bytes
  memory.kmem.tcp.max_usage_in_bytes
  memory.kmem.tcp.usage_in_bytes
  memory.kmem.usage_in_bytes
  memory.limit_in_bytes
  memory.max_usage_in_bytes
  memory.memsw.failcnt
  memory.memsw.limit_in_bytes
  memory.memsw.max_usage_in_bytes
  memory.memsw.usage_in_bytes
  memory.move_charge_at_immigrate
  memory.numa_stat
  memory.oom_control
  memory.pressure_level
  memory.soft_limit_in_bytes
  memory.stat
  memory.swappiness
  memory.usage_in_bytes
  memory.use_hierarchy
  notify_on_release
  tasks
  
  # 限制内存使用
  [root@docker mydocker]# echo 1073741824 > memory.limit_in_bytes
  
  # 将当前shell写入tasks内
  [root@docker mydocker]# echo $$>tasks
  [root@docker mydocker]# cat tasks
  3356
  3484
  # 申请内存，当达到1G时 被杀死
  [root@docker mydocker]# memtester 1500M 1
  memtester version 4.3.0 (64-bit)
  Copyright (C) 2001-2012 Charles Cazabon.
  Licensed under the GNU General Public License version 2 (only).
  
  pagesize is 4096
  pagesizemask is 0xfffffffffffff000
  want 1500MB (1572864000 bytes)
  got  1500MB (1572864000 bytes), trying mlock ...Killed
  
  # 修改申请大小，完美
  [root@docker mydocker]# memtester 500M 1
  memtester version 4.3.0 (64-bit)
  Copyright (C) 2001-2012 Charles Cazabon.
  Licensed under the GNU General Public License version 2 (only).
  
  pagesize is 4096
  pagesizemask is 0xfffffffffffff000
  want 500MB (524288000 bytes)
  got  500MB (524288000 bytes), trying mlock ...locked.
  Loop 1/1:
    Stuck Address       : ok
    Random Value        : ok
    Compare XOR         : ok
    Compare SUB         : ok
    Compare MUL         : ok
    Compare DIV         : ok
    Compare OR          : ok
    Compare AND         : ok
    Sequential Increment: ok
    Solid Bits          : ok
    Block Sequential    : ok
    Checkerboard        : ok
    Bit Spread          : ok
  ```

- docker 是如何使用cgroups的？

  ```sh
  docker run -ti -m=1g nginx
  ```

  