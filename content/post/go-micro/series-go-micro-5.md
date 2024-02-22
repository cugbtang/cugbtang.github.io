---
title: "micro quick, how to play?"
date: 2023-11-30T15:44:23+08:00
lastmod: 2023-11-30T16:44:23+08:00
draft: false
tags: [ "go", "micro"]
categories: ["go", "micro"]
author: "yesplease"
---
# 工程化

- 简单模板：
gin-vue-admin
- 自定义：
nunu+vue3+el
- 微服务：
IDL（声明+代码+文档+错误）,kratos

## 统一服务端回复信息格式

- micro: http+json
```go
func (e *Helloworld) Call(ctx context.Context, req *pb.CallRequest, rsp *pb.CallResponse) error {
  logger.Infof("Received Helloworld.Call request: %v", req)
  rsp.Msg = "Hello " + req.Name
  return errors.New("aaa")
}

  rsp, err := c.Call(context.Background(), &pb.CallRequest{Name: "John"})
```

- grpc: http2+protobuf
```go
// SayHello implements helloworld.GreeterServer
func (s *server) SayHello(ctx context.Context, in *pb.HelloRequest) (*pb.HelloReply, error) {
  log.Printf("Received: %v", in.GetName())
  return &pb.HelloReply{Message: "Hello " + in.GetName()}, nil
}

  c := pb.NewGreeterClient(conn)
  r, err := c.SayHello(ctx, &pb.HelloRequest{Name: name})
```
kratos: 感觉是go-micro的最佳实践
Errors：通过 Protobuf 的 Enum 作为错误码定义，以及工具生成判定接口；
Metadata：在协议通信 HTTP/gRPC 中，通过 Middleware 规范化服务元信息传递；
Encoding：支持 Accept 和 Content-Type 进行自动选择内容编码；


