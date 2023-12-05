---
title: "Go-micro, how to play introduction?"
date: 2023-09-15T15:44:23+08:00
lastmod: 2023-09-15T16:44:23+08:00
draft: false
tags: [ "go", "micro","go-micro"]
categories: ["go", "micro","go-micro"]
author: "yesplease"
---
# Go-micro 简介

## 一句话介绍

Go Micro is a framework for distributed systems development.

  

## 多说两句

Go Micro provides the core requirements for distributed systems development including RPC and Event driven communication. 
The Go Micro philosophy is sane defaults with a pluggable architecture. We provide defaults to get you started quickly but everything can be easily swapped out.

## 介绍下具体功能

- Authentication - Auth is built in as a first class citizen. Authentication and authorization enable secure zero trust networking by providing every service an identity and certificates. This additionally includes rule based access control.

- Dynamic Config - Load and hot reload dynamic config from anywhere. The config interface provides a way to load application level config from any source such as env vars, file, etcd. You can merge the sources and even define fallbacks.

- ata Storage - A simple data store interface to read, write and delete records. It includes support for memory, file and CockroachDB by default. State and persistence becomes a core requirement beyond prototyping and Micro looks to build that into the framework.

- Service Discovery - Automatic service registration and name resolution. Service discovery is at the core of micro service development. When service A needs to speak to service B it needs the location of that service. The default discovery mechanism is multicast DNS (mdns), a zeroconf system.

- Load Balancing - Client side load balancing built on service discovery. Once we have the addresses of any number of instances of a service we now need a way to decide which node to route to. We use random hashed load balancing to provide even distribution across the services and retry a different node if there's a problem.

- Message Encoding - Dynamic message encoding based on content-type. The client and server will use codecs along with content-type to seamlessly encode and decode Go types for you. Any variety of messages could be encoded and sent from different clients. The client and server handle this by default. This includes protobuf and json by default.

- RPC Client/Server - RPC based request/response with support for bidirectional streaming. We provide an abstraction for synchronous communication. A request made to a service will be automatically resolved, load balanced, dialled and streamed.

- Async Messaging - PubSub is built in as a first class citizen for asynchronous communication and event driven architectures. Event notifications are a core pattern in micro service development. The default messaging system is a HTTP event message broker.

- Event Streaming - PubSub is great for async notifications but for more advanced use cases event streaming is preferred. Offering persistent storage, consuming from offsets and acking. Go Micro includes support for NATS Jetstream and Redis streams.

- Synchronization - Distributed systems are often built in an eventually consistent manner. Support for distributed locking and leadership are built in as a Sync interface. When using an eventually consistent database or scheduling use the Sync interface.

- Pluggable Interfaces - Go Micro makes use of Go interfaces for each distributed system abstraction. Because of this these interfaces are pluggable and allows Go Micro to be runtime agnostic. You can plugin any underlying technology.

## 相关的 toolkit
- [API](https://github.com/go-micro/api)
- [CLI](https://github.com/go-micro/cli)
- [Demo](https://github.com/go-micro/demo)
- [Plugins](https://github.com/go-micro/plugins)
- [Examples](https://github.com/go-micro/examples)
- [Dashboard](https://github.com/go-micro/dashboard)
- [Generator](https://github.com/go-micro/generator)