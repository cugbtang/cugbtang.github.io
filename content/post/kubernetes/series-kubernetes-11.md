---
title: "etcd authentication, how to deploy?"
date: 2024-03-28T15:28:23+08:00
lastmod: 2024-03-28T15:28:23+08:00
draft: false
tags: ["kubernetes", "etcd"]
categories: ["kubernetes", "cloudnative"]
author: "yesplease"
---

## 一、加载启动参数
### 1. 配置文件（Configuration file）
如果您提供了一个配置文件，那么配置文件中的设置将具有最高优先级。这意味着配置文件中的配置项将覆盖通过命令行标志和环境变量设置的所有配置。

### 2. 命令行标志（Command-line flags）
当启动etcd时，通过命令行传递的标志具有较高的优先级。如果命令行标志被设置，它们将覆盖环境变量中的相应配置。

### 3. 环境变量（Environment variables）
每个命令行标志都有一个对应的环境变量。如果命令行中没有提供相应的标志，环境变量中的设置将被应用。环境变量的名称以`ETCD_`为前缀，并使用全大写字母和蛇形命名法。

### 优先级规则
- 如果提供了配置文件，配置文件中的配置项将覆盖命令行标志和环境变量中的设置。
- 如果没有提供配置文件，命令行标志的设置将覆盖环境变量中的设置。
- 如果命令行标志和环境变量都没有设置，etcd将使用默认值。

原文描述：
```yaml
Caution: If you mix-and-match configuration options, then the following rules apply.

1、Command-line flags take precedence over environment variables.
2、If you provide a configuration file all command-line flags and environment variables are ignored.
```


## 二、加密传输
### 已有证书
```sh
$ etcd --name infra0 --data-dir infra0 \
  --cert-file=/path/to/server.crt --key-file=/path/to/server.key \
  --advertise-client-urls=https://127.0.0.1:2379 --listen-client-urls=https://127.0.0.1:2379

$ curl --cacert /path/to/ca.crt https://127.0.0.1:2379/v2/keys/foo -XPUT -d value=bar -v
```
### 自动生成证书
```sh
DISCOVERY_URL=... # from https://discovery.etcd.io/new
# member1
$ etcd --name infra1 --data-dir infra1 \
  --auto-tls --peer-auto-tls \
  --initial-advertise-peer-urls=https://10.0.1.10:2380 --listen-peer-urls=https://10.0.1.10:2380 \
  --discovery ${DISCOVERY_URL}

# member2
$ etcd --name infra2 --data-dir infra2 \
  --auto-tls --peer-auto-tls \
  --initial-advertise-peer-urls=https://10.0.1.11:2380 --listen-peer-urls=https://10.0.1.11:2380 \
  --discovery ${DISCOVERY_URL}
```

## 三、RBAC

### 特殊用户和角色
- 存在一个特殊用户`root`和特殊角色`root`。
- `root`用户拥有对etcd的完全访问权限，必须在激活身份验证之前创建。
- `root`角色可以授予任何用户，包括root用户本身。拥有`root`角色的用户具有全局读写访问权限，并且可以更新集群的身份验证配置。

### 管理用户
- `etcdctl`的`user`子命令用于处理与用户账户相关的所有操作。
- 列出用户、创建用户、删除用户、更改用户密码等操作都可以通过`etcdctl`命令完成。
- 创建用户时，可以设置密码或不设置密码。没有密码的用户可以通过TLS通用名称（Common Name, CN）进行身份验证。

### 管理角色
- `etcdctl`的`role`子命令用于处理特定角色的访问控制。
- 列出角色、创建新角色、删除角色等操作都可以通过`etcdctl`命令完成。
- 角色可以被授予对单个键或键范围的访问权限，权限可以是只读、只写或读写。
- 角色的权限可以通过`etcdctl`命令授予和撤销。

### 启用身份验证
- 启用身份验证的最小步骤包括创建root用户和启用身份验证。
- 启用身份验证后，etcd将运行在启用身份验证的状态下。如果需要禁用身份验证，可以使用相应的命令。

### 使用`etcdctl`进行身份验证
- `etcdctl`支持类似于`curl`的身份验证标志。
- 用户可以使用用户名和密码进行身份验证，也可以从提示中获取密码或从命令行标志中提供密码。

### 使用TLS通用名称
- 从etcd v3.2版本开始，如果etcd服务器以`--client-cert-auth=true`选项启动，客户端TLS证书中的通用名称（CN）字段将被用作etcd用户。
- 在这种情况下，通用名称用于身份验证用户，客户端不需要密码。
- 如果客户端同时提供了`--client-cert-auth=true`和CN，以及用户名和密码，那么基于用户名和密码的身份验证将被优先考虑。
- 此功能不能与gRPC-proxy和gRPC-gateway一起使用，因为这些工具在处理TLS连接时存在限制。

### 关于密码强度的注意事项
- `etcdctl`和etcd API在创建用户或更新用户密码时不会强制执行特定密码长度。
- 管理员有责任执行这些要求。
- 为了避免与密码强度相关的安全风险，可以使用基于TLS通用名称的身份验证，以及使用`--no-password`选项创建的用户。


## 四、加认证
### 配置证书认证启动
单纯的证书认证模式，默认有所有权限，其实是没有开启认证（即没有执行etcdtl auth enable）
看下原文描述：
```yaml
As of version v3.2 if an etcd server is launched with the option --client-cert-auth=true, the field of Common Name (CN) in the client’s TLS cert will be used as an etcd user. In this case, the common name authenticates the user and the client does not need a password. Note that if both of 1. --client-cert-auth=true is passed and CN is provided by the client, and 2. username and password are provided by the client, the username and password based authentication is prioritized. Note that this feature cannot be used with gRPC-proxy and gRPC-gateway. This is because gRPC-proxy terminates TLS from its client so all the clients share a cert of the proxy. gRPC-gateway uses a TLS connection internally for transforming HTTP request to gRPC request so it shares the same limitation. Therefore the clients cannot provide their CN to the server correctly. gRPC-proxy will cause an error and stop if a given cert has non empty CN. gRPC-proxy returns an error which indicates that the client has an non empty CN in its cert.
```
```sh
$ etcd --name infra0 --data-dir infra0 \
  --client-cert-auth --trusted-ca-file=/path/to/ca.crt --cert-file=/path/to/server.crt --key-file=/path/to/server.key \
  --advertise-client-urls https://127.0.0.1:2379 --listen-client-urls https://127.0.0.1:2379

$ curl --cacert /path/to/ca.crt --cert /path/to/client.crt --key /path/to/client.key \
  -L https://127.0.0.1:2379/v2/keys/foo -XPUT -d value=bar -v

```
根据证书设置RBAC
```sh
export ETCDCTL_API=3
ENDPOINTS=localhost:2379

etcdctl --endpoints=${ENDPOINTS} role add root
etcdctl --endpoints=${ENDPOINTS} role get root

etcdctl --endpoints=${ENDPOINTS} user add root
etcdctl --endpoints=${ENDPOINTS} user grant-role root root
etcdctl --endpoints=${ENDPOINTS} user get root

etcdctl --endpoints=${ENDPOINTS} role add role0
etcdctl --endpoints=${ENDPOINTS} role grant-permission role0 readwrite foo
etcdctl --endpoints=${ENDPOINTS} user add user0
etcdctl --endpoints=${ENDPOINTS} user grant-role user0 role0

etcdctl --endpoints=${ENDPOINTS} auth enable
# now all client requests go through auth

etcdctl --endpoints=${ENDPOINTS} --user=user0:123 put foo bar
etcdctl --endpoints=${ENDPOINTS} get foo
# permission denied, user name is empty because the request does not issue an authentication request
etcdctl --endpoints=${ENDPOINTS} --user=user0:123 get foo
# user0 can read the key foo
etcdctl --endpoints=${ENDPOINTS} --user=user0:123 get foo1

```

### 配置账号密码启动,即只开启RBAC
使用 `bitnami/etcd:3.5.4` 的镜像
```sh
apiVersion: apps/v1
kind: StatefulSet
metadata:
  labels:
    app: etcd
  name: etcd
spec:
  replicas: 1
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      app: etcd
  serviceName: etcd-headless
  template:
    metadata:
      labels:
        app: etcd
      name: etcd
    spec:
      containers:
      - env:
        - name: ETCD_AUTO_COMPACTION_MODE
          value: "revision"
        - name: ETCD_AUTO_COMPACTION_RETENTION
          value: "1000"
        - name: ETCD_QUOTA_BACKEND_BYTES
          value: "10240000000"
        - name: ETCD_ROOT_PASSWORD
          value: xxx
        - name: MY_POD_NAME
          valueFrom:
            fieldRef:
              apiVersion: v1
              fieldPath: metadata.name
        - name: CLUSTER_NAMESPACE
          valueFrom:
            fieldRef:
              apiVersion: v1
              fieldPath: metadata.namespace
        - name: SERVICE_NAME
          value: etcd-headless
        image: bitnami/etcd:3.5.4
        imagePullPolicy: IfNotPresent
        name: etcd
        ports:
        - containerPort: 2380
          name: peer
          protocol: TCP
        - containerPort: 2379
          name: client
          protocol: TCP
        resources:
          limits:
            cpu: 500m
            memory: 1Gi
          requests:
            cpu: 500m
            memory: 1Gi
        terminationMessagePath: /dev/termination-log
        terminationMessagePolicy: File
        volumeMounts:
        - mountPath: /etc/certs
          name: etcd-tls
        - mountPath: /bitnami/etcd/data
          name: etcd-pvc
      dnsPolicy: ClusterFirst
      restartPolicy: Always
      schedulerName: default-scheduler
      securityContext: {}
      terminationGracePeriodSeconds: 30
      volumes:
      - name: etcd-tls
        secret:
          secretName: etcd-secret
      - name: etcd-pvc
        emptyDir: {}
```
### 配置证书认证+开启RBAC
```sh
apiVersion: apps/v1
kind: StatefulSet
metadata:
  labels:
    app: etcd
  name: etcd
spec:
  replicas: 1
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      app: etcd
  serviceName: etcd-headless
  template:
    metadata:
      labels:
        app: etcd
      name: etcd
    spec:
      containers:
      - env:
        - name: ETCD_CLIENT_CERT_AUTH
          value: "true"
        - name: ETCD_TRUSTED_CA_FILE
          value: "/etc/certs/ca.pem"
        - name: ETCD_CERT_FILE
          value: "/etc/certs/etcd.pem"
        - name: ETCD_KEY_FILE
          value: "/etc/certs/etcd-key.pem"
        - name: ETCD_AUTO_COMPACTION_MODE
          value: "revision"
        - name: ETCD_AUTO_COMPACTION_RETENTION
          value: "1000"
        - name: ETCD_QUOTA_BACKEND_BYTES
          value: "10240000000"
        - name: ETCD_ROOT_PASSWORD
          value: xxx
        - name: ETCD_LISTEN_CLIENT_URLS
          value: "https://0.0.0.0:2379"
        - name: ETCD_ADVERTISE_CLIENT_URLS
          value: "https://0.0.0.0:2379"
        - name: MY_POD_NAME
          valueFrom:
            fieldRef:
              apiVersion: v1
              fieldPath: metadata.name
        - name: CLUSTER_NAMESPACE
          valueFrom:
            fieldRef:
              apiVersion: v1
              fieldPath: metadata.namespace
        - name: SERVICE_NAME
          value: etcd-headless
        image: bitnami/etcd:3.5.4
        imagePullPolicy: IfNotPresent
        name: etcd
        ports:
        - containerPort: 2380
          name: peer
          protocol: TCP
        - containerPort: 2379
          name: client
          protocol: TCP
        resources:
          limits:
            cpu: 500m
            memory: 1Gi
          requests:
            cpu: 500m
            memory: 1Gi
        terminationMessagePath: /dev/termination-log
        terminationMessagePolicy: File
        volumeMounts:
        - mountPath: /etc/certs
          name: etcd-tls
        - mountPath: /bitnami/etcd/data
          name: etcd-pvc
      dnsPolicy: ClusterFirst
      restartPolicy: Always
      schedulerName: default-scheduler
      securityContext: {}
      terminationGracePeriodSeconds: 30
      volumes:
      - name: etcd-tls
        secret:
          secretName: etcd-secret
      - name: etcd-pvc
        emptyDir: {}
```
## 五、引用
[etcd](https://etcd.io/docs/v3.6/op-guide/configuration/)