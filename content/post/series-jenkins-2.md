---
title: "Jenkins, Q&A"
date: 2018-03-01T16:01:23+08:00
lastmod: 2018-03-01T16:01:23+08:00
draft: false
tags: ["cicd", "jenkins"]
categories: ["cicd", "jenkins"]
author: "yesplease"
---


## 1、镜像选择 ` jenkinsci/blueocean `  , why?

- 安装blue ocean插件前

![](https://i.loli.net/2021/10/27/r1wjF2aUuZ7vm9M.png)

- 安装blue ocean插件后

![](https://i.loli.net/2021/10/27/3aJV4YNPRjdCtI1.png)


## 2、启动参数都表示什么？

  ```shell
  docker run \
    --rm \
    -u root \
    -p 8080:8080 \
    -v jenkins-data:/var/jenkins_home \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$HOME":/home \
    jenkinsci/blueocean
  ```

  - `-p 8080:8080 ` 映射（例如“发布”）jenkinsci/blueocean 容器的端口8080到主机上的端口8080。 第一个数字代表主机上的端口，而最后一个代表容器的端口。因此，如果您为此选项指定 -p 49000:8080 ，您将通过端口49000访问主机上的Jenkins。
  - `-p 50000:50000`（可选）将 jenkinsci/blueocean 容器的端口50000 映射到主机上的端口50000。 如果您在其他机器上设置了一个或多个基于JNLP的Jenkins代理程序，而这些代理程序又与 jenkinsci/blueocean 容器交互（充当“主”Jenkins服务器，或者简称为“Jenkins主”）， 则这是必需的。默认情况下，基于JNLP的Jenkins代理通过TCP端口50000与Jenkins主站进行通信。 您可以通过“ 配置全局安全性” 页面更改Jenkins主服务器上的端口号。如果您要将您的Jenkins主机的JNLP代理端口的TCP端口 值更改为51000（例如），那么您需要重新运行Jenkins（通过此 docker run … 命令）并指定此“发布”选项 -p 52000:51000，其中后一个值与Jenkins master上的这个更改值相匹配，第一个值是Jenkins主机的主机上的端口号， 通过它，基于JNLP的Jenkins代理与Jenkins主机进行通信 - 例如52000。
  - `-v jenkins-data:/var/jenkins_home`（可选，但强烈建议）映射在容器中的/var/jenkins_home 目录到具有名字 jenkins-data 的volume。 如果这个卷不存在，那么这个 docker run 命令会自动为你创建卷。 如果您希望每次重新启动Jenkins（通过此 docker run … 命令）时保持Jenkins状态，则此选项是必需的 。 如果你没有指定这个选项，那么在每次重新启动后，Jenkins将有效地重置为新的实例。
    注意: 所述的 jenkins-data 卷也可以 docker volume create命令创建： docker volume create jenkins-data 代替映射 /var/jenkins_home 目录转换为Docker卷，还 可以将此目录映射到计算机本地文件系统上的目录。 例如，指定该选项 -v $HOME/jenkins:/var/jenkins_home 会将容器的 /var/jenkins_home 目录映射到 本地计算机上目录中的 jenkins 子目录， 该$HOME目录通常是 /Users/<your-username>/jenkins 或/home/<your-username>/jenkins 。
  - `-v /var/run/docker.sock:/var/run/docker.sock`（可选 /var/run/docker.sock 表示Docker守护程序通过其监听的基于Unix的套接字。 该映射允许 jenkinsci/blueocean 容器与Docker守护进程通信，如果jenkinsci/blueocean容器需要实例化其他Docker容器，则该守护进程是必需的。 如果运行声明式管道，其语法包含agent部分用 docker 例如， agent { docker { ... } } 此选项是必需的。



  