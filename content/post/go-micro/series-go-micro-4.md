---
title: "Go-micro, how to play engineering?"
date: 2023-09-15T15:44:23+08:00
lastmod: 2023-09-15T16:44:23+08:00
draft: false
tags: [ "go", "micro","go-micro"]
categories: ["go", "micro","go-micro"]
author: "yesplease"
---
# 工程化

1、尽可能的附属到IDL
2、IDL统一仓库管理

## 统一服务端回复信息格式
    - rpc的正确返回，状态码是200，附加正确的数据信息
    - rpc的错误返回（1），状态码希望复用grpc的，外加对应的错误描述
    - rpc的错误返回（2），状态码是200，附加自定义proto格式的错误模型（IDL定义模型）

## 使用中间件，withXxxHandler/wrapXxxHandler
    - 自带的log不行

    - 缺少metric

    - 微服务间的鉴权

    -  缺少限流和熔断

    - 使用中间件，withXxxHandler/wrapXxxHandler

## API管理
    - IDL，即声明=代码=文档
    - 原信息，用于服务治理


