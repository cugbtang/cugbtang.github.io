---
title: "nginx 鉴权_k8s中的服务使用proxy auth鉴权"
date: 2022-04-01T16:01:23+08:00
lastmod: 2022-04-01T16:01:23+08:00
draft: false
tags: ["kubernetes", "auth"]
categories: ["kubernetes", "cloudnative"]
author: "yesplease"
---

## nginx 鉴权_k8s中的服务使用proxy auth鉴权

## 需求

k8s nginx ingress除了可以对服务提供basic权限验证外，也可以使用外部的鉴权服务。我们集群内肯定会有很多服务， 比如我们会有论坛博客、有视频点播等等服务，我们肯定为了避免用户在各个子服务内重复登陆而采用了单点登录服务。很好，而nginx ingress也可以帮我们做一些工作。

比如，我们建立了一套登录与鉴权服务，登录页面URL是http://example.com/login ，鉴权URL是http://example.com/auth，我们约定登录用户会设定一个Header X-Forwarded-User来记录用户名，子服务收到请求直接检查有无此Header即可判断是否是已登录的某用户。