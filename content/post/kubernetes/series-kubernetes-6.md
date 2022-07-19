---
title: "The node was low on resource: ephemeral-storage. Evicted"
date: 2022-04-15T16:01:23+08:00
lastmod: 2022-04-15T16:01:23+08:00
draft: false
tags: ["kubernetes", "FAQ"]
categories: ["kubernetes", "cloudnative"]
author: "yesplease"
---

## The node was low on resource: ephemeral-storage. Evicted

最近某个节点频繁出现这个问题

## 问题分析



## 解决方案

- 查询到的解决方案

  不能让某个占用过多的资源，临时存储不允许一直占用，用超过Limit， kubernetes就会干掉这个Pod，当然也会迅速拉起一个

  ```sh
      resources:
        requests:
          ephemeral-storage: "100Mi"
        limits:
          ephemeral-storage: "4Gi"
  ```

- 我们的改进方案

  1、在 CICD 部署模板中添加请求和限制，包括包括cpu、mem、ephemeral-storage

  2、修改docker 容器日志的限制， 在 `/etc/docker/daemon.json`

  ```sh
  {
  "log-driver": "json-file",
  "log-opts": {
      "max-size": "300m",
      "max-file": "3"
      }
  }
  
  max-size=300m，意味着一个容器日志大小上限是300M
  max-file=3，意味着一个容器有三个日志
  ```

## 引用

- [https://stackoverflow.com/questions/59906810/the-node-was-low-on-resource-ephemeral-storage](https://stackoverflow.com/questions/59906810/the-node-was-low-on-resource-ephemeral-storage)





