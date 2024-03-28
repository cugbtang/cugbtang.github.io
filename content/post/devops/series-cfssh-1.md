---
title: "cfssh, Q&A"
date: 2024-03-28T13:28:23+08:00
lastmod: 2024-03-28T13:28:23+08:00
draft: false
tags: ["tools", "cfssh"]
categories: ["devops", "tools"]
author: "yesplease"
---

为了使用`cfssl`工具自签发证书，并设置不同的有效期，你需要创建JSON配置文件来指定证书的属性，包括有效期。以下是生成根证书、服务端证书和客户端证书的具体命令和示例配置文件。

### 1. 生成根证书（CA）

首先，创建一个根证书的配置文件（例如`ca-config.json`）：

```json
{
  "signing": {
    "profiles": {
      "root": {
        "usages": [
          "cert sign",
          "crl sign",
          "key encipherment",
          "server auth",
          "client auth"
        ],
        "expiry": "10000m"  // 100年，这里使用月份表示法
      }
    },
    "default": {
      "expiry": "10000m"  // 默认有效期也为100年
    }
  }
}
```

然后，使用以下命令生成根证书：

```bash
cfssl gencert -initca ca-csr.json | cfssljson -bare ca
```

这里假设你已经有了一个名为`ca-csr.json`的证书签名请求（CSR）配置文件。

### 2. 生成服务端证书

创建一个服务端证书的配置文件（例如`server-csr.json`）：

```json
{
  "hosts": [
    "example.com"  // 服务端的域名
  ],
  "CN": "example.com",  // 通用名称，通常与域名相同
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "ST": "State",
      "L": "Locality",
      "O": "Organization",
      "OU": "Unit"
    }
  ],
  "ca": "/etc/cfssl/ca.pem",  // 根证书文件路径
  "ca_key": "/etc/cfssl/ca-key.pem",  // 根证书密钥文件路径
  "expiry": "10y"  // 服务端证书有效期10年
}
```

使用以下命令生成服务端证书：

```bash
cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=root server-csr.json | cfssljson -bare server
```

### 3. 生成客户端证书

创建一个客户端证书的配置文件（例如`client-csr.json`）：

```json
{
  "hosts": [],
  "CN": "client",  // 客户端的名称或ID
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "ST": "State",
      "L": "Locality",
      "O": "Organization",
      "OU": "Unit"
    }
  ],
  "ca": "/etc/cfssl/ca.pem",  // 根证书文件路径
  "ca_key": "/etc/cfssl/ca-key.pem",  // 根证书密钥文件路径
  "expiry": "1y"  // 客户端证书有效期1年
}
```

使用以下命令生成客户端证书：

```bash
cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=root client-csr.json | cfssljson -bare client
```

在上述命令中，`ca.pem`和`ca-key.pem`是由`cfssl gencert`命令生成的根证书和密钥文件。`server-csr.json`和`client-csr.json`是服务端和客户端证书的CSR配置文件，你需要根据实际情况调整其中的域名、国家代码、州/省、城市/地区、组织名称和组织单位等信息。

请注意，有效期可以通过字符串表示法来设置，例如`"10y"`表示10年，`"1y"`表示1年。确保在执行命令之前，你已经创建了相应的配置文件，并且文件路径正确指向了你的根证书和密钥。