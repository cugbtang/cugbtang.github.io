---
title: "Go-micro advance, how to play?"
date: 2023-09-15T15:44:23+08:00
lastmod: 2023-09-15T16:44:23+08:00
draft: false
tags: [ "go", "micro","go-micro"]
categories: ["go", "micro","go-micro"]
author: "yesplease"
---
# 疑问

## 服务发现，一个服务注册到consul/etcd，客户端怎么感知到

利用注册中心的订阅能力。客户端使用 Subscribe 方法来订阅服务更新的事件。该方法接收三个参数：服务名称、事件处理函数和可选的过滤器选项。当有新的服务注册或者已注册的服务发生变化时，事件处理函数将被调用。

## 注册中心，一个服务不可用了，consul默认是怎么感知的

Consul 提供了多种类型的健康检查，包括 HTTP、TCP、gRPC、Script 等。
默认，Consul Agent 在每次进行健康检测时，会向服务实例发送一个 HTTP GET 请求，并等待该请求的响应。如果在 1 秒内没有收到响应，该次检测将被视为超时。Consul Agent 将尝试最多 3 次健康检测，如果在这些检测中有任何一次超时或者返回的状态码不符合健康条件，那么该服务实例将被标记为不健康状态。

## 客户端，当有多个微服务可用时，客户端的负载均衡是怎么做的

默认的负载均衡策略是轮询（Round-Robin）。go-micro v4 提供了多种负载均衡策略供选择，包括 Round-Robin、Random、LeastConnection 和 Weighted 等。

## 如果不想使用服务发现，就想已ip+port的方式启动，该怎么办?
Go Micro CLI is the command line interface for developing Go Micro projects.

## 如果我想自定义错误返回，该怎么办？

## 插件化原理
强定义的接口

## 扩展性
基于Wrapper（中间件）
