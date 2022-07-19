---
title: "kubernetes1.24.0, Why use docker  in production environment ?"
date: 2022-03-15T16:01:23+08:00
lastmod: 2022-03-15T16:01:23+08:00
draft: false
tags: ["kubernetes", "cri"]
categories: ["kubernetes", "cloudnative"]
author: "yesplease"
---

## kubernetes1.24.0, Why use docker  in production environment ?



## if you consider

Mirantis and Docker have [committed](https://www.mirantis.com/blog/mirantis-to-take-over-support-of-kubernetes-dockershim-2/) to maintaining a replacement adapter for Docker Engine, and to maintain that adapter even after the in-tree dockershim is removed from Kubernetes. The replacement adapter is named [`cri-dockerd`](https://github.com/Mirantis/cri-dockerd).

- Download the cri-dockerd binary package or compile the source code yourself

  ```sh
  # download file
  wget https://github.com/Mirantis/cri-dockerd/releases/download/v0.2.0/cri-dockerd-v0.2.0-linux-amd64.tar.gz
  # unzip file
  tar -xvf cri-dockerd-v0.2.0-linux-amd64.tar.gz
  # Copy the binary file to the specified directory
  cp cri-dockerd /usr/bin/
  ```

  

- Configure startup files

  ```sh
  vim /usr/lib/systemd/system/cri-docker.service
  [Unit]
  Description=CRI Interface for Docker Application Container Engine
  Documentation=https://docs.mirantis.com
  After=network-online.target firewalld.service docker.service
  Wants=network-online.target
  Requires=cri-docker.socket
  
  [Service]
  Type=notify
  
  ExecStart=/usr/bin/cri-dockerd --container-runtime-endpoint=unix:///var/run/cri-docker.sock --network-plugin=cni --cni-bin-dir=/opt/cni/bin \
            --cni-conf-dir=/etc/cni/net.d --image-pull-progress-deadline=30s --pod-infra-container-image=docker.io/juestnow/pause:3.6 \
            --docker-endpoint=unix:///var/run/docker.sock --cri-dockerd-root-directory=/var/lib/docker
  ExecReload=/bin/kill -s HUP $MAINPID
  TimeoutSec=0
  RestartSec=2
  Restart=always
  
  # Note that StartLimit* options were moved from "Service" to "Unit" in systemd 229.
  # Both the old, and new location are accepted by systemd 229 and up, so using the old location
  # to make them work for either version of systemd.
  StartLimitBurst=3
  
  # Note that StartLimitInterval was renamed to StartLimitIntervalSec in systemd 230.
  # Both the old, and new name are accepted by systemd 230 and up, so using the old name to make
  # this option work for either version of systemd.
  StartLimitInterval=60s
  
  # Having non-zero Limit*s causes performance problems due to accounting overhead
  # in the kernel. We recommend using cgroups to do container-local accounting.
  LimitNOFILE=infinity
  LimitNPROC=infinity
  LimitCORE=infinity
  
  # Comment TasksMax if your systemd version does not support it.
  # Only systemd 226 and above support this option.
  TasksMax=infinity
  Delegate=yes
  KillMode=process
  
  [Install]
  WantedBy=multi-user.target
  
  # Generate socket file
  vim /usr/lib/systemd/system/cri-docker.socket
  [Unit]
  Description=CRI Docker Socket for the API
  PartOf=cri-docker.service
  
  [Socket]
  ListenStream=/var/run/cri-dockerd.sock
  SocketMode=0660
  SocketUser=root
  SocketGroup=docker
  
  [Install]
  WantedBy=sockets.target
  # start up cri-dockerd
  systemctl daemon-reload
  systemctl start cri-docker
  # set startup
  systemctl enable cri-docker
  # view startup status
  systemctl status cri-docker
  ```

- Download cri-tools to verify whether cri-docker is normal

  ```sh
  # Download binaries
  wget https://github.com/kubernetes-sigs/cri-tools/releases/download/v1.24.0/crictl-v1.24.0-linux-amd64.tar.gz
  # unzip
  tar -xvf crictl-v1.24.0-linux-amd64.tar.gz
  # Copy the binaries to the specified directory
  cp crictl /usr/bin/
  # Create configuration file
  vim /etc/crictl.yaml
  runtime-endpoint: "unix:///var/run/cri-docker.sock"
  image-endpoint: "unix:///var/run/cri-docker.sock"
  timeout: 10
  debug: false
  pull-image-on-create: true
  disable-pull-on-run: false
  # Test if you can access docker
  # View running containers
  crictl ps
  # View pulled images
  crictl images
  # pull image
  crictl pull busybox
  [root@k8s-node-4 ~]# crictl pull busybox
  Image is up to date for busybox@sha256:5acba83a746c7608ed544dc1533b87c737a0b0fb730301639a0179f9344b1678
  # Return true, cri-dockerd access to docker is complete
  ```

  

- 1

## REF

[Thursday, February 17, 2022 - Updated: Dockershim Removal FAQ](https://kubernetes.io/blog/2022/02/17/dockershim-faq/)

