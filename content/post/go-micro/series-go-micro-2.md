---
title: "Go-micro cli, how to play?"
date: 2023-09-15T15:44:23+08:00
lastmod: 2023-09-15T16:44:23+08:00
draft: false
tags: [ "go", "micro","go-micro"]
categories: ["go", "micro","go-micro"]
author: "yesplease"
---
# Go-micro 简介

## 一句话介绍

Go Micro CLI is the command line interface for developing Go Micro projects.

  

## 开始表演
- 安装
```sh
go install github.com/go-micro/cli/cmd/go-micro@latest
```
- 创建测试项目（执行命令，后续根据命令提示操作）
```sh
go-micro new service helloworld
```
- 创建工程化项目（执行命令，后续根据命令提示操作）
```sh
go-micro new service --jaeger --health --grpc --advanced
```
注：
1、 Since Kubernetes 1.24, probes can make use of the gRPC Health Protocol. This allows you to directly probe the go-micro service in a Kubernetes container if it implements the health protocol.
2、By default, go-micro uses an JSON/HTTP RPC server. Many microservice use cases require a gRPC server or client, therefore, go-micro offers a gRPC server built in. gRPC默认使用HTTP/2作为其传输协议，并使用Protocol Buffers（protobuf）作为默认的消息序列化和接口定义语言

- 添加工程化插件
1、consul 配置和服务发现中心


- 本地测试接口

测试非流
```sh
$ go-micro call helloworld Helloworld.Call '{"name": "John"}'
{"msg":"Hello John"}
```
测试单流
```sh
$ go-micro stream server helloworld Helloworld.ServerStream '{"count": 10}'
{"count":0}
{"count":1}
{"count":2}
{"count":3}
{"count":4}
{"count":5}
{"count":6}
{"count":7}
{"count":8}
{"count":9}
```
测试双向流
```sh
$ go-micro stream bidi helloworld Helloworld.BidiStream '{"stroke": 1}' '{"stroke": 2}' '{"stroke": 3}'
{"stroke":1}
{"stroke":2}
{"stroke":3}
```
或者 curl
```sh
curl -XPOST \
     -H 'Content-Type: application/json' \
     -H 'Micro-Endpoint: Helloworld.Call' \
     -d '{"name": "alice"}' \
      http://localhost:8080
```


## 探索
- 阅读 examples
- 尝试 plugins