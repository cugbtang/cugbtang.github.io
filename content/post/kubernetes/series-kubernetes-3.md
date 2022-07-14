---
title: "kubeadm startup Kubernetes more than v1.20.0 (centos7+containerd+ipvs+calico)"
date: 2022-05-15T16:01:23+08:00
lastmod: 2022-05-15T16:01:23+08:00
draft: false
tags: ["kubernetes", "kubeadm","deploy"]
categories: ["kubernetes", "cn"]
author: "yesplease"
---
这篇文章的作者部署的是kubernetes v1.23，但其实是基于kubernetes对CRI的改动执行的较为流行的方案。

我绝的主要是针对Docker的支持问题，因为在1.24中才正式将docker-shim剔除。以下列举了较为流行的部署方案：

- kubernetes < 1.20 + centos7 + docker + iptables + flannel
- kubernetes < 1.20 + centos7 + docker + ipvs + calico

- 1.20 <kubernetes < 1.24 + centos7 + docker + ipvs + calico
- kubernetes > 1.24 + centos7 + containerd + ipvs + calico
- kubernetes > 1.24 + centos7 + cri-o + ipvs + calico
- kubernetes > 1.24 + centos7 + cri-dockerd + docker + ipvs + calico

[转载声明：使用kubeadm部署Kubernetes 1.23](https://blog.frognew.com/2021/12/kubeadm-install-kubernetes-1.23.html#1%E5%87%86%E5%A4%87)

kubeadm是Kubernetes官方提供的用于快速安部署Kubernetes集群的工具，伴随Kubernetes每个版本的发布都会同步更新，kubeadm会对集群配置方面的一些实践做调整，通过实验kubeadm可以学习到Kubernetes官方在集群配置上一些新的最佳实践。

## 1.准备

### 1.1 系统配置

在安装之前，需要先做好如下准备。3台CentOS 7.9主机如下：

```sh
cat /etc/hosts
192.168.96.151    node1
192.168.96.152    node2
192.168.96.153    node3
```

在**各个主机**上完成下面的系统配置。

- yum:

```sh
#备份本地 yum 源
$ mv /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo_bak 
# 获取阿里 yum 源配置文件
$ wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo 
#清理 yum
$ yum clean all
#更新软件版本并且更新现有软件
$ yum -y update
```

- 防火墙：

如果各个主机启用了防火墙策略，需要开放Kubernetes各个组件所需要的端口，可以查看[Installing kubeadm](https://kubernetes.io/docs/setup/independent/install-kubeadm/)中的"Check required ports"一节开放相关端口或者关闭主机的防火墙。

- 禁用SELINUX：

```sh
setenforce 0
```

```sh
vi /etc/selinux/config
SELINUX=disabled
```

- 加载需要的内核模块

创建/etc/modules-load.d/containerd.conf配置文件:

```sh
cat << EOF > /etc/modules-load.d/containerd.conf
overlay
br_netfilter
EOF
```

执行以下命令使配置生效:

```sh
modprobe overlay
modprobe br_netfilter
```

创建/etc/sysctl.d/99-kubernetes-cri.conf配置文件：

```sh
cat << EOF > /etc/sysctl.d/99-kubernetes-cri.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
user.max_user_namespaces=28633
EOF
```

执行以下命令使配置生效:

```sh
sysctl -p /etc/sysctl.d/99-kubernetes-cri.conf
```

-  配置服务器支持开启ipvs的前提条件

由于ipvs已经加入到了内核的主干，所以为kube-proxy开启ipvs的前提需要加载以下的内核模块：

```sh
ip_vs
ip_vs_rr
ip_vs_wrr
ip_vs_sh
nf_conntrack_ipv4 
```

在各个服务器节点上执行以下脚本:

```sh
cat > /etc/sysconfig/modules/ipvs.modules <<EOF
#!/bin/bash
modprobe -- ip_vs
modprobe -- ip_vs_rr
modprobe -- ip_vs_wrr
modprobe -- ip_vs_sh
modprobe -- nf_conntrack_ipv4
EOF
chmod 755 /etc/sysconfig/modules/ipvs.modules && bash /etc/sysconfig/modules/ipvs.modules && lsmod | grep -e ip_vs -e nf_conntrack_ipv4
```

> 注：内核4版本以上 nf_conntrack 替换 nf_conntrack_ipv4

上面脚本创建了的`/etc/sysconfig/modules/ipvs.modules`文件，保证在节点重启后能自动加载所需模块。 使用`lsmod | grep -e ip_vs -e nf_conntrack_ipv4`命令查看是否已经正确加载所需的内核模块。

接下来还需要确保各个节点上已经安装了ipset软件包，为了便于查看ipvs的代理规则，最好安装一下管理工具ipvsadm。

```sh
yum install -y ipset ipvsadm
```

如果以上前提条件如果不满足，则即使kube-proxy的配置开启了ipvs模式，也会退回到iptables模式。

### 1.2 部署容器运行时Containerd

在各个服务器节点上安装容器运行时Containerd。

下载Containerd的二进制包:

```sh
wget https://github.com/containerd/containerd/releases/download/v1.5.8/cri-containerd-cni-1.5.8-linux-amd64.tar.gz
```

`cri-containerd-cni-1.5.8-linux-amd64.tar.gz`压缩包中已经按照官方二进制部署推荐的目录结构布局好。 里面包含了systemd配置文件，containerd以及cni的部署文件。 将解压缩到系统的根目录`/`中:

```sh
tar -zxvf cri-containerd-cni-1.5.8-linux-amd64.tar.gz -C /

etc/
etc/systemd/
etc/systemd/system/
etc/systemd/system/containerd.service
etc/crictl.yaml
etc/cni/
etc/cni/net.d/
etc/cni/net.d/10-containerd-net.conflist
usr/
usr/local/
usr/local/sbin/
usr/local/sbin/runc
usr/local/bin/
usr/local/bin/critest
usr/local/bin/containerd-shim
usr/local/bin/containerd-shim-runc-v1
usr/local/bin/ctd-decoder
usr/local/bin/containerd
usr/local/bin/containerd-shim-runc-v2
usr/local/bin/containerd-stress
usr/local/bin/ctr
usr/local/bin/crictl
......
opt/cni/
opt/cni/bin/
opt/cni/bin/bridge
......
```



注意经测试cri-containerd-cni-1.5.8-linux-amd64.tar.gz包中包含的runc在CentOS 7下的动态链接有问题，这里从runc的github上单独下载runc，并替换上面安装的containerd中的runc

```sh
wget https://github.com/opencontainers/runc/releases/download/v1.1.0-rc.1/runc.amd64
```

接下来生成containerd的配置文件:

```sh
mkdir -p /etc/containerd
containerd config default > /etc/containerd/config.toml
```

根据文档[Container runtimes ](https://kubernetes.io/docs/setup/production-environment/container-runtimes/)中的内容，对于使用systemd作为init system的Linux的发行版，使用systemd作为容器的cgroup driver可以确保服务器节点在资源紧张的情况更加稳定，因此这里配置各个节点上containerd的cgroup driver为systemd。

修改前面生成的配置文件`/etc/containerd/config.toml`：

```sh
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
  ...
  [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
    SystemdCgroup = true
```

再修改`/etc/containerd/config.toml`中的

```sh
[plugins."io.containerd.grpc.v1.cri"]
  ...
  # sandbox_image = "k8s.gcr.io/pause:3.5"
  sandbox_image = "registry.aliyuncs.com/google_containers/pause:3.6"
```

配置containerd开机启动，并启动containerd

```sh
systemctl enable containerd --now
```

使用crictl测试一下，确保可以打印出版本信息并且没有错误信息输出:

```sh
crictl version
Version:  0.1.0
RuntimeName:  containerd
RuntimeVersion:  v1.5.8
RuntimeApiVersion:  v1alpha2
```

## 2.使用kubeadm部署Kubernetes

### 2.1 安装kubeadm和kubelet

下面在各节点安装kubeadm和kubelet：

```sh
cat <<EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=http://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=http://mirrors.aliyun.com/kubernetes/yum/doc/yum-key.gpg
        http://mirrors.aliyun.com/kubernetes/yum/doc/rpm-package-key.gpg
EOF
```

```sh
yum makecache fast
yum install kubelet kubeadm kubectl
```

运行`kubelet --help`可以看到原来kubelet的绝大多数命令行flag参数都被`DEPRECATED`了，官方推荐我们使用`--config`指定配置文件，并在配置文件中指定原来这些flag所配置的内容。具体内容可以查看这里[Set Kubelet parameters via a config file](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-config-file/)。这也是Kubernetes为了支持动态Kubelet配置（Dynamic Kubelet Configuration）才这么做的，参考[Reconfigure a Node’s Kubelet in a Live Cluster](https://kubernetes.io/docs/tasks/administer-cluster/reconfigure-kubelet/)。

kubelet的配置文件必须是json或yaml格式，具体可查看[这里](https://github.com/kubernetes/kubelet/blob/release-1.23/config/v1beta1/types.go)。

Kubernetes 1.8开始要求关闭系统的Swap，如果不关闭，默认配置下kubelet将无法启动。 关闭系统的Swap方法如下:

```sh
swapoff -a
```

修改 /etc/fstab 文件，注释掉 SWAP 的自动挂载，使用`free -m`确认swap已经关闭。

swappiness参数调整，修改/etc/sysctl.d/99-kubernetes-cri.conf添加下面一行：

```sh
vm.swappiness=0
```

执行`sysctl -p /etc/sysctl.d/99-kubernetes-cri.conf`使修改生效。

### 2.2 使用kubeadm init初始化集群

在各节点开机启动kubelet服务：

```sh
systemctl enable kubelet.service
```

使用`kubeadm config print init-defaults --component-configs KubeletConfiguration`可以打印集群初始化默认的使用的配置：

```sh
apiVersion: kubeadm.k8s.io/v1beta3
bootstrapTokens:
- groups:
  - system:bootstrappers:kubeadm:default-node-token
  token: abcdef.0123456789abcdef
  ttl: 24h0m0s
  usages:
  - signing
  - authentication
kind: InitConfiguration
localAPIEndpoint:
  advertiseAddress: 1.2.3.4
  bindPort: 6443
nodeRegistration:
  criSocket: /var/run/dockershim.sock
  imagePullPolicy: IfNotPresent
  name: node
  taints: null
---
apiServer:
  timeoutForControlPlane: 4m0s
apiVersion: kubeadm.k8s.io/v1beta3
certificatesDir: /etc/kubernetes/pki
clusterName: kubernetes
controllerManager: {}
dns: {}
etcd:
  local:
    dataDir: /var/lib/etcd
imageRepository: k8s.gcr.io
kind: ClusterConfiguration
kubernetesVersion: 1.23.0
networking:
  dnsDomain: cluster.local
  serviceSubnet: 10.96.0.0/12
scheduler: {}
---
apiVersion: kubelet.config.k8s.io/v1beta1
authentication:
  anonymous:
    enabled: false
  webhook:
    cacheTTL: 0s
    enabled: true
  x509:
    clientCAFile: /etc/kubernetes/pki/ca.crt
authorization:
  mode: Webhook
  webhook:
    cacheAuthorizedTTL: 0s
    cacheUnauthorizedTTL: 0s
cgroupDriver: systemd
clusterDNS:
- 10.96.0.10
clusterDomain: cluster.local
cpuManagerReconcilePeriod: 0s
evictionPressureTransitionPeriod: 0s
fileCheckFrequency: 0s
healthzBindAddress: 127.0.0.1
healthzPort: 10248
httpCheckFrequency: 0s
imageMinimumGCAge: 0s
kind: KubeletConfiguration
logging:
  flushFrequency: 0
  options:
    json:
      infoBufferSize: "0"
  verbosity: 0
memorySwap: {}
nodeStatusReportFrequency: 0s
nodeStatusUpdateFrequency: 0s
rotateCertificates: true
runtimeRequestTimeout: 0s
shutdownGracePeriod: 0s
shutdownGracePeriodCriticalPods: 0s
staticPodPath: /etc/kubernetes/manifests
streamingConnectionIdleTimeout: 0s
syncFrequency: 0s
volumeStatsAggPeriod: 0s
```

从默认的配置中可以看到，可以使用`imageRepository`定制在集群初始化时拉取k8s所需镜像的地址。基于默认配置定制出本次使用kubeadm初始化集群所需的配置文件kubeadm.yaml：

```sh
apiVersion: kubeadm.k8s.io/v1beta3
kind: InitConfiguration
localAPIEndpoint:
  advertiseAddress: 192.168.96.151
  bindPort: 6443
nodeRegistration:
  criSocket: /run/containerd/containerd.sock
  taints:
  - effect: PreferNoSchedule
    key: node-role.kubernetes.io/master
---
apiVersion: kubeadm.k8s.io/v1beta2
kind: ClusterConfiguration
kubernetesVersion: v1.22.0
imageRepository: registry.aliyuncs.com/google_containers
networking:
  podSubnet: 10.244.0.0/16
---
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
cgroupDriver: systemd
failSwapOn: false
---
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
mode: ipvs
```

这里定制了`imageRepository`为阿里云的registry，避免因gcr被墙，无法直接拉取镜像。`criSocket`设置了容器运行时为containerd。 同时设置kubelet的`cgroupDriver`为systemd，设置kube-proxy代理模式为ipvs。

在开始初始化集群之前可以使用`kubeadm config images pull --config kubeadm.yaml`预先在各个服务器节点上拉取所k8s需要的容器镜像。

```sh
kubeadm config images pull --config kubeadm.yaml
[config/images] Pulled registry.aliyuncs.com/google_containers/kube-apiserver:v1.23.1
[config/images] Pulled registry.aliyuncs.com/google_containers/kube-controller-manager:v1.23.1
[config/images] Pulled registry.aliyuncs.com/google_containers/kube-scheduler:v1.23.1
[config/images] Pulled registry.aliyuncs.com/google_containers/kube-proxy:v1.23.1
[config/images] Pulled registry.aliyuncs.com/google_containers/pause:3.6
[config/images] Pulled registry.aliyuncs.com/google_containers/etcd:3.5.1-0
[config/images] Pulled registry.aliyuncs.com/google_containers/coredns:v1.8.6
```

接下来使用kubeadm初始化集群，选择node1作为Master Node，在node1上执行下面的命令：

```sh
kubeadm init --config kubeadm.yaml
[init] Using Kubernetes version: v1.23.1
[preflight] Running pre-flight checks
[preflight] Pulling images required for setting up a Kubernetes cluster
[preflight] This might take a minute or two, depending on the speed of your internet connection
[preflight] You can also perform this action in beforehand using 'kubeadm config images pull'
[certs] Using certificateDir folder "/etc/kubernetes/pki"
[certs] Generating "ca" certificate and key
[certs] Generating "apiserver" certificate and key
[certs] apiserver serving cert is signed for DNS names [kubernetes kubernetes.default kubernetes.default.svc kubernetes.default.svc.cluster.local node1] and IPs [10.96.0.1 192.168.96.151]
[certs] Generating "apiserver-kubelet-client" certificate and key
[certs] Generating "front-proxy-ca" certificate and key
[certs] Generating "front-proxy-client" certificate and key
[certs] Generating "etcd/ca" certificate and key
[certs] Generating "etcd/server" certificate and key
[certs] etcd/server serving cert is signed for DNS names [localhost node1] and IPs [192.168.96.151 127.0.0.1 ::1]
[certs] Generating "etcd/peer" certificate and key
[certs] etcd/peer serving cert is signed for DNS names [localhost node1] and IPs [192.168.96.151 127.0.0.1 ::1]
[certs] Generating "etcd/healthcheck-client" certificate and key
[certs] Generating "apiserver-etcd-client" certificate and key
[certs] Generating "sa" key and public key
[kubeconfig] Using kubeconfig folder "/etc/kubernetes"
[kubeconfig] Writing "admin.conf" kubeconfig file
[kubeconfig] Writing "kubelet.conf" kubeconfig file
[kubeconfig] Writing "controller-manager.conf" kubeconfig file
[kubeconfig] Writing "scheduler.conf" kubeconfig file
[kubelet-start] Writing kubelet environment file with flags to file "/var/lib/kubelet/kubeadm-flags.env"
[kubelet-start] Writing kubelet configuration to file "/var/lib/kubelet/config.yaml"
[kubelet-start] Starting the kubelet
[control-plane] Using manifest folder "/etc/kubernetes/manifests"
[control-plane] Creating static Pod manifest for "kube-apiserver"
[control-plane] Creating static Pod manifest for "kube-controller-manager"
[control-plane] Creating static Pod manifest for "kube-scheduler"
[etcd] Creating static Pod manifest for local etcd in "/etc/kubernetes/manifests"
[wait-control-plane] Waiting for the kubelet to boot up the control plane as static Pods from directory "/etc/kubernetes/manifests". This can take up to 4m0s
[apiclient] All control plane components are healthy after 16.003580 seconds
[upload-config] Storing the configuration used in ConfigMap "kubeadm-config" in the "kube-system" Namespace
[kubelet] Creating a ConfigMap "kubelet-config-1.23" in namespace kube-system with the configuration for the kubelets in the cluster
NOTE: The "kubelet-config-1.23" naming of the kubelet ConfigMap is deprecated. Once the UnversionedKubeletConfigMap feature gate graduates to Beta the default name will become just "kubelet-config". Kubeadm upgrade will handle this transition transparently.
[upload-certs] Skipping phase. Please see --upload-certs
[mark-control-plane] Marking the node node1 as control-plane by adding the labels: [node-role.kubernetes.io/master(deprecated) node-role.kubernetes.io/control-plane node.kubernetes.io/exclude-from-external-load-balancers]
[mark-control-plane] Marking the node node1 as control-plane by adding the taints [node-role.kubernetes.io/master:PreferNoSchedule]
[bootstrap-token] Using token: o7d0h6.i9taufdl7u1un4va
[bootstrap-token] Configuring bootstrap tokens, cluster-info ConfigMap, RBAC Roles
[bootstrap-token] configured RBAC rules to allow Node Bootstrap tokens to get nodes
[bootstrap-token] configured RBAC rules to allow Node Bootstrap tokens to post CSRs in order for nodes to get long term certificate credentials
[bootstrap-token] configured RBAC rules to allow the csrapprover controller automatically approve CSRs from a Node Bootstrap Token
[bootstrap-token] configured RBAC rules to allow certificate rotation for all node client certificates in the cluster
[bootstrap-token] Creating the "cluster-info" ConfigMap in the "kube-public" namespace
[kubelet-finalize] Updating "/etc/kubernetes/kubelet.conf" to point to a rotatable kubelet client certificate and key
[addons] Applied essential addon: CoreDNS
[addons] Applied essential addon: kube-proxy

Your Kubernetes control-plane has initialized successfully!

To start using your cluster, you need to run the following as a regular user:

  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

Alternatively, if you are the root user, you can run:

  export KUBECONFIG=/etc/kubernetes/admin.conf

You should now deploy a pod network to the cluster.
Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
  https://kubernetes.io/docs/concepts/cluster-administration/addons/

Then you can join any number of worker nodes by running the following on each as root:

kubeadm join 192.168.96.151:6443 --token o7d0h6.i9taufdl7u1un4va \
	--discovery-token-ca-cert-hash sha256:6c55b14e9d71ef098ad0e8f249d85004c41b48063dbcd7692997930f9637f22b
```

上面记录了完成的初始化输出的内容，根据输出的内容基本上可以看出手动初始化安装一个Kubernetes集群所需要的关键步骤。 其中有以下关键内容：

- `[certs]`生成相关的各种证书
- `[kubeconfig]`生成相关的kubeconfig文件
- `[kubelet-start]` 生成kubelet的配置文件"/var/lib/kubelet/config.yaml"
- `[control-plane]`使用`/etc/kubernetes/manifests`目录中的yaml文件创建apiserver、controller-manager、scheduler的静态pod
- `[bootstraptoken]`生成token记录下来，后边使用`kubeadm join`往集群中添加节点时会用到
- 下面的命令是配置常规用户如何使用kubectl访问集群：

```sh
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

- 最后给出了将节点加入集群的命令`kubeadm join 192.168.96.151:6443 --token o7d0h6.i9taufdl7u1un4va \ --discovery-token-ca-cert-hash sha256:6c55b14e9d71ef098ad0e8f249d85004c41b48063dbcd7692997930f9637f22b`

查看一下集群状态，确认个组件都处于healthy状态，结果出现了错误:

```sh
kubectl get cs
Warning: v1 ComponentStatus is deprecated in v1.19+
NAME                 STATUS      MESSAGE                                                                                       ERROR
controller-manager   Unhealthy   Get "http://127.0.0.1:10252/healthz": dial tcp 127.0.0.1:10252: connect: connection refused
scheduler            Unhealthy   Get "http://127.0.0.1:10251/healthz": dial tcp 127.0.0.1:10251: connect: connection refused
etcd-0               Healthy     {"health":"true"}
```

controller-manager和scheduler为不健康状态，修改`/etc/kubernetes/manifests/`下的静态pod配置文件`kube-controller-manager.yaml`和`kube-scheduler.yaml`，删除这两个文件中命令选项中的`- --port=0`这行，重启kubelet，再次查看一切正常。

```sh
kubectl get cs
Warning: v1 ComponentStatus is deprecated in v1.19+
NAME                 STATUS    MESSAGE                         ERROR
scheduler            Healthy   ok
controller-manager   Healthy   ok
etcd-0               Healthy   {"health":"true","reason":""}
```

集群初始化如果遇到问题，可以使用`kubeadm reset`命令进行清理。

### 2.3 安装包管理器helm 3

Helm是Kubernetes的包管理器，后续流程也将使用Helm安装Kubernetes的常用组件。 这里先在master节点node1上按照helm。

```sh
wget https://get.helm.sh/helm-v3.7.2-linux-amd64.tar.gz
tar -zxvf helm-v3.7.2-linux-amd64.tar.gz
mv linux-amd64/helm  /usr/local/bin/
```

执行`helm list`确认没有错误输出。

### 2.4 部署Pod Network组件Calico

选择calico作为k8s的Pod网络组件，下面使用helm在k8s集群中按照calico。

下载`tigera-operator`的helm chart:

```sh
wget https://github.com/projectcalico/calico/releases/download/v3.21.2/tigera-operator-v3.21.2-1.tgz
```

查看这个chart的中可定制的配置:

```sh
helm show values tigera-operator-v3.21.2-1.tgz

imagePullSecrets: {}

installation:
  enabled: true
  kubernetesProvider: ""

apiServer:
  enabled: true

certs:
  node:
    key:
    cert:
    commonName:
  typha:
    key:
    cert:
    commonName:
    caBundle:

# Configuration for the tigera operator
tigeraOperator:
  image: tigera/operator
  version: v1.23.3
  registry: quay.io
calicoctl:
  image: quay.io/docker.io/calico/ctl
  tag: v3.21.2
```

定制的`values.yaml`如下:

```sh
# 可针对上面的配置进行定制,例如calico的镜像改成从私有库拉取。
# 这里只是个人本地环境测试k8s新版本，因此保留value.yaml为空即可
```

使用helm安装calico：

```sh
helm install calico tigera-operator-v3.21.2-1.tgz -f values.yaml
```

等待并确认所有pod处于Running状态:

```sh
watch kubectl get pods -n calico-system
NAME                                       READY   STATUS    RESTARTS   AGE
calico-kube-controllers-7f58dbcbbd-kdnlg   1/1     Running   0          2m34s
calico-node-nv794                          1/1     Running   0          2m34s
calico-typha-65f579bc5d-4pbfz              1/1     Running   0          2m34s
```

查看一下calico向k8s中添加的api资源:

```sh
kubectl api-resources | grep calico
bgpconfigurations                              crd.projectcalico.org/v1               false        BGPConfiguration
bgppeers                                       crd.projectcalico.org/v1               false        BGPPeer
blockaffinities                                crd.projectcalico.org/v1               false        BlockAffinity
caliconodestatuses                             crd.projectcalico.org/v1               false        CalicoNodeStatus
clusterinformations                            crd.projectcalico.org/v1               false        ClusterInformation
felixconfigurations                            crd.projectcalico.org/v1               false        FelixConfiguration
globalnetworkpolicies                          crd.projectcalico.org/v1               false        GlobalNetworkPolicy
globalnetworksets                              crd.projectcalico.org/v1               false        GlobalNetworkSet
hostendpoints                                  crd.projectcalico.org/v1               false        HostEndpoint
ipamblocks                                     crd.projectcalico.org/v1               false        IPAMBlock
ipamconfigs                                    crd.projectcalico.org/v1               false        IPAMConfig
ipamhandles                                    crd.projectcalico.org/v1               false        IPAMHandle
ippools                                        crd.projectcalico.org/v1               false        IPPool
ipreservations                                 crd.projectcalico.org/v1               false        IPReservation
kubecontrollersconfigurations                  crd.projectcalico.org/v1               false        KubeControllersConfiguration
networkpolicies                                crd.projectcalico.org/v1               true         NetworkPolicy
networksets                                    crd.projectcalico.org/v1               true         NetworkSet
```

这些api资源是属于calico的，因此不建议使用kubectl来管理，推荐按照calicoctl来管理这些api资源。 将calicoctl安装为kubectl的插件:

```fallback
cd /usr/local/bin
curl -o kubectl-calico -O -L  "https://github.com/projectcalico/calicoctl/releases/download/v3.21.2/calicoctl" 
chmod +x kubectl-calico
```

验证插件正常工作:

```fallback
kubectl calico -h
```

### 2.5 验证k8s DNS是否可用

```fallback
kubectl run curl --image=radial/busyboxplus:curl -it
If you don't see a command prompt, try pressing enter.
[ root@curl:/ ]$
```

进入后执行`nslookup kubernetes.default`确认解析正常:

```fallback
nslookup kubernetes.default
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local

Name:      kubernetes.default
Address 1: 10.96.0.1 kubernetes.default.svc.cluster.local
```

### 2.6 向Kubernetes集群中添加Node节点

下面将node2, node3添加到Kubernetes集群中，分别在node2, node3上执行:

```
kubeadm join 192.168.96.151:6443 --token o7d0h6.i9taufdl7u1un4va \  --discovery-token-ca-cert-hash sha256:6c55b14e9d71ef098ad0e8f249d85004c41b48063dbcd7692997930f9637f22b 
```

node2和node3加入集群很是顺利，在master节点上执行命令查看集群中的节点：

```fallback
kubectl get node
NAME    STATUS   ROLES                  AGE     VERSION
node1   Ready    control-plane,master   29m     v1.23.1
node2   Ready    <none>                 5m28s   v1.23.1
node3   Ready    <none>                 5m4s    v1.23.1
```

## 3.Kubernetes常用组件部署

### 3.1 使用Helm部署ingress-nginx

为了便于将集群中的服务暴露到集群外部，需要使用Ingress。接下来使用Helm将ingress-nginx部署到Kubernetes上。 Nginx Ingress Controller被部署在Kubernetes的边缘节点上。

这里将node1(192.168.96.151)作为边缘节点，打上Label：

```fallback
kubectl label node node1 node-role.kubernetes.io/edge=
```

下载ingress-nginx的helm chart:

```
wget https://github.com/kubernetes/ingress-nginx/releases/download/helm-chart-4.0.13/ingress-nginx-4.0.13.tgz 
```

查看`ingress-nginx-4.0.13.tgz`这个chart的可定制配置:

```
helm show values ingress-nginx-4.0.13.tgz 
```

对values.yaml配置定制如下:

```yml
controller:
  ingressClassResource:
    name: nginx
    enabled: true
    default: true
    controllerValue: "k8s.io/ingress-nginx"
  admissionWebhooks:
    enabled: false
  replicaCount: 1
  image:
    # registry: k8s.gcr.io
    # image: ingress-nginx/controller
    # tag: "v1.1.0"
    registry: docker.io
    image: unreachableg/k8s.gcr.io_ingress-nginx_controller
    tag: "v1.1.0"
    digest: sha256:4f5df867e9367f76acfc39a0f85487dc63526e27735fa82fc57d6a652bafbbf6
  hostNetwork: true
  nodeSelector:
    node-role.kubernetes.io/edge: ''
  affinity:
    podAntiAffinity:
        requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchExpressions:
            - key: app
              operator: In
              values:
              - nginx-ingress
            - key: component
              operator: In
              values:
              - controller
          topologyKey: kubernetes.io/hostname
  tolerations:
      - key: node-role.kubernetes.io/master
        operator: Exists
        effect: NoSchedule
      - key: node-role.kubernetes.io/master
        operator: Exists
        effect: PreferNoSchedule
```

nginx ingress controller的副本数replicaCount为1，将被调度到node1这个边缘节点上。这里并没有指定nginx ingress controller service的externalIPs，而是通过`hostNetwork: true`设置nginx ingress controller使用宿主机网络。 因为k8s.gcr.io被墙，这里替换成unreachableg/k8s.gcr.io_ingress-nginx_controller提前拉取一下镜像:

```
crictl pull unreachableg/k8s.gcr.io_ingress-nginx_controller:v1.1.0 
```

```
helm install ingress-nginx ingress-nginx-4.0.13.tgz --create-namespace -n ingress-nginx -f values.yaml 
```

```fallback
kubectl get pod -n ingress-nginx
NAME                                        READY   STATUS    RESTARTS   AGE
ingress-nginx-controller-7f574989bc-xwbf4   1/1     Running   0          117s
```

测试访问`http://192.168.96.151`返回默认的nginx 404页，则部署完成。

### 3.2 使用Helm部署dashboard

先部署metrics-server：

```
wget https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.5.2/components.yaml 
```

修改components.yaml中的image为`docker.io/unreachableg/k8s.gcr.io_metrics-server_metrics-server:v0.5.2`。 修改components.yaml中容器的启动参数，加入`--kubelet-insecure-tls`。

```
kubectl apply -f components.yaml 
```

metrics-server的pod正常启动后，等一段时间就可以使用`kubectl top`查看集群和pod的metrics信息:

```fallback
kubectl top node --use-protocol-buffers=true
NAME    CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
node1   219m         5%     3013Mi          39%
node2   102m         2%     1576Mi          20%
node3   110m         2%     1696Mi          21%

kubectl top pod -n kube-system --use-protocol-buffers=true
NAME                                    CPU(cores)   MEMORY(bytes)
coredns-59d64cd4d4-9mclj                4m           17Mi
coredns-59d64cd4d4-fj7xr                4m           17Mi
etcd-node1                              25m          154Mi
kube-apiserver-node1                    80m          465Mi
kube-controller-manager-node1           17m          61Mi
kube-proxy-hhlhc                        1m           21Mi
kube-proxy-nrhq7                        1m           19Mi
kube-proxy-phmrw                        1m           17Mi
kube-scheduler-node1                    4m           24Mi
kubernetes-dashboard-5cb95fd47f-6lfnm   3m           36Mi
metrics-server-9ddcc8ddf-jvlzs          5m           21Mi
```

接下来使用helm部署k8s的dashboard，添加chart repo:

```fallback
helm repo add kubernetes-dashboard https://kubernetes.github.io/dashboard/
helm repo update
```

查看chart的可定制配置:

```
helm show values kubernetes-dashboard/kubernetes-dashboard 
```

对value.yaml定制配置如下:

```yml
image:
  repository: kubernetesui/dashboard
  tag: v2.4.0
ingress:
  enabled: true
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
  hosts:
  - k8s.example.com
  tls:
    - secretName: example-com-tls-secret
      hosts:
      - k8s.example.com
metricsScraper:
  enabled: true
```

先创建存放`k8s.example.com`ssl证书的secret:

```fallback
kubectl create secret tls example-com-tls-secret \
  --cert=cert.pem \
  --key=key.pem \
  -n kube-system
```

使用helm部署dashboard:

helm install kubernetes-dashboard kubernetes-dashboard/kubernetes-dashboard \
-n kube-system \
-f values.yaml

确认上面的命令部署成功。

创建管理员sa:

```fallback
kubectl create serviceaccount kube-dashboard-admin-sa -n kube-system

kubectl create clusterrolebinding kube-dashboard-admin-sa \
--clusterrole=cluster-admin --serviceaccount=kube-system:kube-dashboard-admin-sa
```

获取集群管理员登录dashboard所需token:

```fallback
kubectl -n kube-system get secret | grep kube-dashboard-admin-sa-token
kube-dashboard-admin-sa-token-rcwlb              kubernetes.io/service-account-token   3      68s

kubectl describe -n kube-system secret/kube-dashboard-admin-sa-token-rcwlb 
Name:         kube-dashboard-admin-sa-token-rcwlb
Namespace:    kube-system
Labels:       <none>
Annotations:  kubernetes.io/service-account.name: kube-dashboard-admin-sa
              kubernetes.io/service-account.uid: fcdf27f6-f6f9-4f76-b64e-edc91fb1479b

Type:  kubernetes.io/service-account-token

Data
====
namespace:  11 bytes
token:      eyJhbGciOiJSUzI1NiIsImtpZCI6IkYxWTd5aDdzYWsyeWJVMFliUUhJMXI4YWtMZFd4dGFDT1N4eEZoam9HLUEifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJrdWJlLWRhc2hib2FyZC1hZG1pbi1zYS10b2tlbi1yY3dsYiIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50Lm5hbWUiOiJrdWJlLWRhc2hib2FyZC1hZG1pbi1zYSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6ImZjZGYyN2Y2LWY2ZjktNGY3Ni1iNjRlLWVkYzkxZmIxNDc5YiIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDprdWJlLXN5c3RlbTprdWJlLWRhc2hib2FyZC1hZG1pbi1zYSJ9.R3l19_Nal4B2EktKFSJ7CgOqAngG_MTgzHRRjWdREN7dLALyfiRXYIgZQ90hxM-a9z2sPXBzfJno4OGP4fPX33D8h_4fgxfpVLjKqjdlZ_HAks_6sV9PBzDNXb_loNW8ECfsleDgn6CZin8Vx1w7sgkoEIKq0H-iZ8V9pRV0fTuOZcB-70pV_JX6H6WBEOgRIAZswhAoyUMvH1qNl47J5xBNwKRgcqP57NCIODo6FiClxfY3MWo2vz44R5wYCuBJJ70p6aBWixjDSxnp5u9mUP0zMF_igICl_OfgKuPyaeuIL83U8dS5ovEwPPGzX5mHUgaPH7JLZmKRNXJqLhTweA
ca.crt:     1066 bytes
```

使用上面的token登录k8s dashboard。

[![dashboard](https://blog.frognew.com/images/2021/06/k8s-1.21-dashboard.png)](https://blog.frognew.com/images/2021/06/k8s-1.21-dashboard.png)

## FAQ

- calico: [BIRD is not ready: BGP not established](https://www.jianshu.com/p/4b175e733cd3)

  一种是通过正则指定网卡，类似这样:

  ```csharp
  - name: IP_AUTODETECTION_METHOD
  value: "interface=ens.*"  # ens 根据实际网卡开头配置
  ```

  另一种是从部署节点到到达目的节点的,类似这样：

  ```bash
  # Using IP addresses
  IP_AUTODETECTION_METHOD=can-reach=8.8.8.8
  IP6_AUTODETECTION_METHOD=can-reach=2001:4860:4860::8888
  
  # Using domain names
  IP_AUTODETECTION_METHOD=can-reach=www.google.com
  IP6_AUTODETECTION_METHOD=can-reach=www.google.com
  ```

  如果是通过 Installation 安装的，需要修改一个CRD Installation

- 

## 参考

- [Installing kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)
- [Creating a cluster with kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm//)
- https://github.com/containerd/containerd
- https://pkg.go.dev/k8s.io/kubernetes/cmd/kubeadm/app/apis/kubeadm/v1beta2
- https://docs.projectcalico.org/