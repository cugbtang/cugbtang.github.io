---
title: "gcr.io 镜像，how to play?"
date: 2022-04-15T16:01:23+08:00
lastmod: 2022-04-15T16:01:23+08:00
draft: false
tags: ["image", "FAQ"]
categories: ["cloudnative"]
author: "yesplease"
---

# 常用镜像仓库

## DockerHub镜像仓库

- Docker Hub 官方镜像仓库 (https://hub.docker.com/)

## Google 镜像仓库

- https://gcr.io/google-containers/
- https://gcr.io/kubernetes-helm/
- https://gcr.io/google-containers/pause

## CoreOS 镜像仓库

- https://quay.io/repository/coreos/

## Elastic 镜像仓库

- https://www.docker.elastic.co/

## RedHat 镜像仓库

- https://catalog.redhat.com/software/containers/search

## 阿里云镜像仓库

- https://cr.console.aliyun.com/

## 华为云镜像仓库

- https://console.huaweicloud.com/swr/


# 国内可以访问的镜像源

部分国外镜像仓库无法访问，但国内有对应镜像源，可以从以下镜像源拉取到本地然后重新打标签即可：

## 阿里云镜像仓库

可以拉取 k8s.gcr.io 镜像

示例：

```
docker pull k8s.gcr.io/pause:3.2
# 改为
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/pause:3.2
```

## Docker Hub 镜像仓库

可以拉取 k8s.gcr.io 镜像

示例：

```
docker pull k8s.gcr.io/pause:3.1
docker pull k8s.gcr.io/kube-apiserver:v1.17.3
# 改为
docker pull willdockerhub/pause:3.1
docker pull willdockerhub/kube-apiserver:v1.17.3
```

## 七牛云镜像仓库

可以拉取 k8s.gcr.io 镜像

示例：

```
docker pull quay.io/kubernetes-ingress-controller/nginx-ingress-controller:0.30.0
# 改为
docker pull quay-mirror.qiniu.com/kubernetes-ingress-controller/nginx-ingress-controller:0.30.0
```

## Docker Hub 搜索镜像

很多国外镜像已经有热心网友上传到了 Docker Hub，例如 `gcr.io/kubernetes-helm/tiller:v2.16.5` 这个镜像，直接搜索关键字，找到排序靠前的然后在 Docker Hub 确认并拉取即可。

示例：

```
# docker search tiller
NAME                                    DESCRIPTION                                     STARS               OFFICIAL            AUTOMATED
jessestuart/tiller                      Nightly multi-architecture (amd64, arm64, ar  19                                      [OK]
sapcc/tiller                            Mirror of https://gcr.io/kubernetes-helm/til  9                                       
ist0ne/tiller                           https://gcr.io/kubernetes-helm/tiller           ....

```
gcr.io镜像
根据开源项目anjia0532/gcr.io_mirror，作者将gcr.io相关镜像pull下来，然后push到docker官方仓库，相关转换语法如下：
```
gcr.io/namespace/image_name:image_tag 
# 等价于
anjia0532/namespace.image_name:image_tag# 特别的
k8s.gcr.io/{image}/{tag} <==> gcr.io/google-containers/{image}/{tag} <==> anjia0532/google-containers.{image}/{tag}
```
- 方法一
K8S的exapmle里的yaml默认是k8s.gcr.io的镜像，为了方便运行我们可以预先拉取相关镜像：

```
# vim pull-google.sh

  image=$1echo $1img=`echo $image | sed 's/k8s\.gcr\.io/anjia0532\/google-containers/g;s/gcr\.io/anjia0532/g;s/\//\./g;s/ /\n/g;s/_/-/g;s/anjia0532\./anjia0532\//g' | uniq | awk '{print ""$1""}'`echo "docker pull $img"docker pull $imgecho  "docker tag $img $image"docker tag $img $image

# chmod +x  pull-google.sh && cp  pull-google.sh /usr/local/bin/pull-google-container 
```

就可以愉快的使用pull-google-container 命令了
```
# pull-google-container gcr.io/google-samples/gb-frontend:v4
gcr.io/google-samples/gb-frontend:v4
docker pull anjia0532/google-samples.gb-frontend:v4
v4: Pulling from anjia0532/google-samples.gb-frontend
Digest: sha256:aaa5b327ef3b4cb705513ab674fa40df66981616950c7de4912a621f9ee03dd4
Status: Image is up to date for anjia0532/google-samples.gb-frontend:v4
docker tag anjia0532/google-samples.gb-frontend:v4 gcr.io/google-samples/gb-frontend:v4
```
- 方法二
除了预先拉取镜像，我们还可以将k8s.gcr.io 替换为可执行镜像
为了方便替换，我们编写一个repair_yaml 脚本：
```
vim /usr/local/bin/repair_yaml
  cp $1 "$1.bak"cat $1.bak | sed 's/k8s\.gcr\.io\/\(.*\)\//anjia0532\/google-containers.\1./g;s/gcr\.io\/\(.*\)\//anjia0532\/\1./g;s/google_/google-/g;' > $1rm -f "$1.bak"
# chmod +x /usr/local/bin/repair_yaml

# repair_yaml frontend-deployment.yaml 
# cat frontend-deployment.yaml 
```

## DockerHub镜像国内加速

### 阿里云镜像加速

```
sudo mkdir -p /etc/docker
tee /etc/docker/daemon.json <<-'EOF'
{"registry-mirrors": ["https://uyah70su.mirror.aliyuncs.com"]
}
EOF
```

### DaoCloud DockerHub镜像加速

```
curl -sSL https://get.daocloud.io/daotools/set_mirror.sh | sh -s http://f1361db2.m.daocloud.io
```

### 西北农林大学DockerHub镜像加速

```
sudo mkdir -p /etc/docker
tee /etc/docker/daemon.json <<-'EOF'
{"registry-mirrors": ["https://dockerhub.mirrors.nwafu.edu.cn/"]
}
EOF
```

### 华为云DockerHub镜像加速

```
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<- 'EOF'
{"registry-mirrors": ["https://7bafc985f90c43b887a96c2b846cf984.mirror.swr.myhuaweicloud.com"]
}
EOF
```

然后重新启动 Docker 服务：

```
sudo systemctl daemon-reload && sudo systemctl restart docker
```

## 验证加速器是否生效

执行 `docker info` 命令，如果从结果中看到了如下内容，说明配置成功。

```
$ docker info | grep Mirrors -A1
Registry Mirrors:https://uyah70su.mirror.aliyuncs.com/
```

## 验证镜像拉取速度

```
$ time docker pull centos
```



