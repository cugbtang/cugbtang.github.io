---
title: "Jenkins, hot backup"
date: 2022-02-01T16:01:23+08:00
lastmod: 2022-02-01T16:01:23+08:00
draft: false
tags: ["cicd", "jenkins", "backup"]
categories: ["devops", "cloudnative"]
author: "yesplease"
---

## jenkins 数据热备

> rsync : 增量备份
>
> inotify： 实时通知




## 理论
### 一、rsync

> 与传统的 cp、tar 备份方式相比，rsync 具有安全性高、备份迅速、支持**增量备份**等优点，通过 rsync 可以解决对实时性要求不高的数据备份需求，例如定期的备份文件服务器数据到远端服务器，对本地磁盘定期做数据镜像等，随着应用系统规模的不断扩大，对数据的安全性和可靠性也提出的更好的要求。
>
> rsync 在高端业务系统中也逐渐暴露出了很多不足：
>
> ​		首先，rsync 同步数据时，需要扫描所有文件后进行比对，进行差量传输。如果**文件数量**达到了百万甚至千万量级，扫描所有文件将是非常耗时的。而且正在发生变化的往往是其中很少的一部分，这是非常低效的方式。
>
> ​		其次，rsync **不能实时**的去监测、同步数据，虽然它可以通过 linux 守护进程的方式进行触发同步，但是两次触发动作一定会有时间差，这样就导致了服务端和客户端数据可能出现不一致，无法在应用故障时完全的恢复数据。基于以上原因，rsync+inotify 组合出现了！

### 二、rsync+inotify

> Inotify 是一种强大的、细粒度的、异步的文件系统**事件监控**机制，linux 内核从 2.6.13 起，加入了 Inotify支持，通过 Inotify 可以监控文件系统中添加、删除，修改、移动等各种细微事件，利用这个内核接口，第三方软件就可以监控文件系统下文件的各种变化情况，而 inotify-tools 就是这样的一个第三方软件。 inotify 可以监控文件系统的各种变化，当文件有任何变动时，就触发rsync 同步，这样刚好解决了同步数据的实时性问题。

### 三、rsync+sersync

> 1、sersync是基于Inotify开发的，类似于Inotify-tools的工具
>
> 2、sersync可以记录下被监听目录中发生变化的（包括增加、删除、修改）具体某一个文件或某一个目录的名字，然后使用rsync同步的时候，只同步发生变化的这个文件或者这个目录。

## 四、小结：

 - rsync+inotify-tools与rsync+sersync这两种架构有什么区别？

1. rsync+Inotify-tools

   - Inotify-tools只能记录下被监听的目录发生了变化（包括增加、删除、修改），并**没有把具体**是哪个文件或者哪个目录发生了变化**记录**下来；
   
   
   - rsync 在同步的时候，并不知道具体是哪个文件或者哪个目录发生了变化，每次都是对整个目录进行同步(应该是扫描)[^1]，当数据量很大时，整个目录同步非常耗时（rsync要对整个目录遍历查找对比文件），因此，效率很低。
   
2. rsync+sersync

   - sersync可以**记录**下被监听目录中发生变化的（包括增加、删除、修改）具体某一个文件或某一个目录的名字；
   
   
      - rsync在同步的时候，只同步发生变化的这个文件或者这个目录（每次发生变化的数据相对整个同步目录数据来说是很小的，rsync在遍历查找比对文件时，速度很快），因此，效率很高。
   
        
   

​	当同步的目录数据量不大时，**建议**使用 rsync+Inotify-tools；当数据量很大（几百G甚至1T以上）、文件很多时，建议使用 rsync+sersync。

## 实践

>说明：
>
>操作系统：CentOS 7.x

> 源服务器：36.111.140.109 （Sersync+web）
>
> 目标服务器： 36.111.140.99、(Rsync+web)   
>
> 目的：把源服务器上/home/Sync目录实时同步到目标服务器的/home/Sync下

### 方案一、同机热备到不同的文件目录

> Rsync+Inotify-tools 架构

![image-20220318111831407](https://raw.githubusercontent.com/cugbtang/image-repo/master/PicGo/20220318111839.png)

```sh
yum install -y rsync inotify-tools

vim /usr/bin/inotify2rsync


#!/bin/bash
# 运行脚本的用户对相关路径有读写权限就行
src=/jenkins/jenkins_job      
dst=/jenkins1/jenkins_job  
      
/usr/bin/inotifywait -mrq --timefmt  '%d/%m/%y %H:%M'  --format  '%T %w%f%e'  -e modify,delete,create,attrib $src |  while  read files

         
         do

         
                 #/usr/bin/rsync -vzrtopg --delete --progress --password-file=/etc/rsyncd.secrects $src $dst
                 rsync -av --exclude  lost+found/ --exclude  backup/  $src $dst

         
                 echo  "${files} was rsynced"  >> /var/log/rsync.log  2 >& 1

         
         done

         
exit  0


```



### 方案二、不同机器热备 rsync+Inotify-tools 架构[^2]



> jenkins 主节点无法高可用（官方说的），针对两套主 jenkins 的**互备方案**，强调磁盘是为了一定要热备到ssd上，保证性能

![image-20220318113041057](https://raw.githubusercontent.com/cugbtang/image-repo/master/PicGo/20220318113041.png)



> rsync 的解决方案解析：
>
> - 左边是**原来的**，一般的rsync的cs架构（client & server）同步模式，数据源服务器上安装rsync server，由server统一控制可以传输的数据的内容，例如权限，目录，文件数等，发起传输的是rsync client，即看起来就是将数据从源服务器拉取到备份服务器。
>- 右边的是加上inotify-tools的**同步模式**，在数据源服务器上安装rsync client，在备份源服务器上安装rsync server，也是由server统一控制传输的数据内容，但是这里是数据源服务器作为了client端，因为发起传输的是rsync client，所以这里看起来就是将数据从源服务器推送到备份服务器。
> - 从逻辑上cs的架构 c 和 s 变成了相反位置，但是传输的模式依然是从 s 传输到 c 。

![blog_rsync_(bs)_introduce_20150206.jpg](https://raw.githubusercontent.com/cugbtang/image-repo/master/PicGo/20220317144123.jpeg)

目标服务器（热备服务器 == rsync服务端）

```sh
sudo yum install -y rsync

# 设置开机启动
echo '/usr/bin/rsync --daemon --config=/etc/rsyncd.conf' >> /etc/rc.d/rc.local


cat <<EOF | sudo tee /etc/rsyncd.conf

#同步目录的所属用户，有权限操作的都可以
uid = Sync
#同步目录的所属组
gid = Sync
#不打开chroot
use chroot = no
#超时时间
timeout = 800 
#日志文件位置，启动rsync后自动产生这个文件，无需提前创建
log file =/var/log/rsyncd.log 
#pid文件的存放位置
pid file =/var/run/rsyncd.pid
#支持max connections参数的锁文件
lock file =/var/run/rsync.lock
#rsync启动时欢迎信息页面文件位置（文件内容自定义）
motd file =/etc/rsyncd.Motd
#默认端口
port = 873  
#设置rsync服务端文件为读写权限
read only =no  
#不显示rsync服务端资源列表
list = no
#最大连接数
max connections = 200
#执行数据同步的用户名，可以设置多个，用英文状态下逗号隔开
auth users = Sync
#允许进行数据同步的客户端IP地址，可以设置多个，用英文状态下逗号隔开
hosts allow = 2.2.2.2
#禁止数据同步的客户端IP地址，可以设置多个，用英文状态下逗号隔开
hosts deny = *
#用户认证配置文件，里面保存用户名称和密码，后面会创建这个文件
secrets file = /etc/rsync.pass

#定义模块
[Sync]
    #rsync服务端数据目录路径
    path = /jenkins1/jenkins_job/
    #模块描述
    comment = Sync
EOF

 #配置文件，添加以下内容，添加允许传输用户和密码
 #格式，用户名:密码，可以设置多个，每行一个用户名:密码
cat <<EOF | sudo tee /etc/rsync.pass
Sync:THW7DLBQ82tBKfIf  

#设置文件所有者读取、写入权限
chmod 600 /etc/rsyncd.conf 
#设置文件所有者读取、写入权限
#这个密码文件只能是这个权限，服务端会做检测
chmod 600 /etc/rsync.pass  

#启动
systemctl enable rsyncd
systemctl restart rsyncd 

# 服务端的rsync开启873端口
#vi /etc/sysconfig/iptables  #编辑防火墙配置文件
-A RH-Firewall-1-INPUT -m state --state NEW -m tcp -ptcp --dport 873 -j ACCEPT
```


源服务器（主服务器 == rsync客户端）

```sh
# 客户端的Rsync可以不用开启873端口

yum install -y rsync inotify-tools

#设置文件权限，只设置文件所有者具有读取、写入权限即可
touch /jenkins/rsync.passwd
echo 'THW7DLBQ82tBKfIf' > /jenkins/rsync.passwd
chmod 600 /jenkins/rsync.passwd

# 测试
mkdir -p /jenkins/ceshi 
#在源服务器上创建测试文件夹，然后在源服务器运行下面1行命令
# /jenkins/ceshi 最后带不带/有很大区别
rsync -avH --port=873 --progress--delete  /jenkins/ceshi Sync@2.2.2.2::Sync --password-file=/jenkins/rsync.passwd


#!/bin/bash

src='/jenkins/jenkins_job'
passwordfile='/jenkins/rsync.passwd'
user='root'
host='2.2.2.2'
rsync_module='Sync'

/usr/bin/inotifywait -mrq --timefmt '%d/%m/%y %H:%M' --format '%T %w %f' -e modify,delete,create,attrib ${src} | while read DATE TIME DIR file
do
	/usr/bin/rsync -vzrtopg --delete --progress ${src} ${user}@${host}::${rsync_module} --password-file=${passwordfile}
	
	echo "${file} was rsynced at ${DATE}_${TIME} in ${DIR}" >> /var/log/rsync.log 2>&1
done

```



### 方案三、不同机器热备 rsync+Inotify-tools 架构[^3]

1. 服务器A（主服务器）
2. 服务器B（从服务器/备份服务器）



- 服务器B

```sh
#在服务器B上安装rsync
cd /app/local
wget  http://rsync.samba.org/ftp/rsync/src/rsync-3.1.1.tar.gz
tar zxf rsync-3.1.1.tar.gz
cd rsync-3.1.1
./configure
make && make install

#设置rsync的配置文件
vi /etc/rsyncd.conf

#服务器B上的rsyncd.conf文件内容
uid=root
gid=root
#最大连接数
max connections=36000
#默认为true，修改为no，增加对目录文件软连接的备份 
use chroot=no
#定义日志存放位置
log file=/var/log/rsyncd.log
#忽略无关错误
ignore errors = yes
#设置rsync服务端文件为读写权限
read only = no 
#认证的用户名与系统帐户无关在认证文件做配置，如果没有这行则表明是匿名
auth users = rsync
#密码认证文件，格式(虚拟用户名:密码）
secrets file = /etc/rsync.pass
#这里是认证的模块名，在client端需要指定，可以设置多个模块和路径
[rsync]
    #自定义注释
    comment  = rsync
    #同步到B服务器的文件存放的路径
    path=/app/data/site/
[img]
    comment  = img
    path=/app/data/site/img

#创建rsync认证文件  可以设置多个，每行一个用户名:密码，注意中间以“:”分割
echo "rsync:rsync" > /etc/rsync.pass

#设置文件所有者读取、写入权限
chmod 600 /etc/rsyncd.conf  
chmod 600 /etc/rsync.pass  

#启动服务器B上的rsync服务
#rsync --daemon -v
rsync --daemon

#监听端口873
netstat -an | grep 873
lsof -i tcp:873

COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
rsync   31445 root    4u  IPv4 443872      0t0  TCP *:rsync (LISTEN)
rsync   31445 root    5u  IPv6 443873      0t0  TCP *:rsync (LISTEN)


#设置rsync为服务启动项（可选）
echo "/usr/local/bin/rsync --daemon" >> /etc/rc.local

#要 Kill rsync 进程，不要用 kill -HUP {PID} 的方式重启进程，以下3种方式任选
#ps -ef|grep rsync|grep -v grep|awk '{print $2}'|xargs kill -9
#cat /var/run/rsyncd.pid | xargs kill -9
pkill rsync
#再次启动
/usr/local/bin/rsync --daemon


```

- 服务器A

```sh
#安装rsync
cd /app/local
wget  http://rsync.samba.org/ftp/rsync/src/rsync-3.1.1.tar.gz
tar zxf rsync-3.1.1.tar.gz
cd rsync-3.1.1
./configure
make && make install

#安装inotify-tools
cd /app/local
wget http://github.com/downloads/rvoicilas/inotify-tools/inotify-tools-3.14.tar.gz
tar zxf inotify-tools-3.14.tar.gz
cd inotify-tools-3.14
./configure --prefix=/app/local/inotify 
make && make install

#安装sersync
cd /app/local
wget https://sersync.googlecode.com/files/sersync2.5.4_64bit_binary_stable_final.tar.gz
tar zxf sersync2.5.4_64bit_binary_stable_final.tar.gz
mv /app/local/GNU-Linux-x86/ /app/local/sersync
cd /app/local/sersync
#配置下密码文件，因为这个密码是要访问服务器B需要的密码和上面服务器B的密码必须一致
echo "rsync" > /app/local/sersync/user.pass
#修改权限
chmod 600 /app/local/sersync/user.pass
#修改confxml.conf
vi /app/local/sersync/confxml.xml

```

修改配置

```xml

<?xml version="1.0" encoding="ISO-8859-1"?>
<head version="2.5">
 <host hostip="localhost" port="8008"></host>
 <debug start="true"/>
 <fileSystem xfs="false"/>
 <filter start="false">
 <exclude expression="(.*)\.php"></exclude>
 <exclude expression="^data/*"></exclude>
 </filter>
 <inotify>
 <delete start="true"/>
 <createFolder start="true"/>
 <createFile start="false"/>
 <closeWrite start="true"/>
 <moveFrom start="true"/>
 <moveTo start="true"/>
 <attrib start="false"/>
 <modify start="false"/>
 </inotify>
 
 <sersync>
 <localpath watch="/home/"> <!-- 这里填写服务器A要同步的文件夹路径-->
 <remote ip="8.8.8.8" name="rsync"/> <!-- 这里填写服务器B的IP地址和模块名-->
 </localpath>
 <rsync>
 <commonParams params="-artuz"/>
 <auth start="true" users="rsync" passwordfile="/app/local/sersync/user.pass"/> <!-- rsync+密码文件 这里填写服务器B的认证信息-->
 <userDefinedPort start="false" port="874"/><!-- port=874 -->
 <timeout start="false" time="100"/><!-- timeout=100 -->
 <ssh start="false"/>
 </rsync>
 <failLog path="/tmp/rsync_fail_log.sh" timeToExecute="60"/><!--default every 60mins execute once--><!-- 修改失败日志记录（可选）-->
 <crontab start="false" schedule="600"><!--600mins-->
 <crontabfilter start="false">
 </crontabfilter>
 </crontab>
 <plugin start="false" name="command"/>
 </sersync>

</head>

```

```sh
#运行sersync
nohup /app/local/sersync/sersync2 -r -d -o /app/local/sersync/confxml.xml >/app/local/sersync/rsync.log 2>&1 &

-d:启用守护进程模式
-r:在监控前，将监控目录与远程主机用rsync命令推送一遍
-n: 指定开启守护线程的数量，默认为10个
-o:指定配置文件，默认使用confxml.xml文件
```

```sh
# 添加一个保障
# vi  /home/crontab/check_sersync.sh

#!/bin/sh

sersync="/usr/local/sersync/sersync2"

confxml="/usr/local/sersync/confxml.xml"

status=$(ps aux |grep 'sersync2'|grep -v 'grep'|wc -l)

if [$status -eq 0 ];

then

$sersync -d-r -o $confxml &

else

exit 0;

fi
```



### 排错[^4]




## 文献

[^1]: [CentOS7下Rsync+sersync实现数据实时同步](https://blog.51cto.com/canonind/1843994)

[^2]: [关于rsync+inotify-tools实时同步模式](https://segmentfault.com/a/1190000002558330)](https://segmentfault.com/a/1190000002558330)

[^3]: [sersync](https://hub.fastgit.xyz/wsgzao/sersync)

[^4]: [Rsync常见错误及命令详细参数](https://blog.51cto.com/wjw7702/1148808)