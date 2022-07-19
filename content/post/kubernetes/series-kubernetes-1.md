---
title: "Kubernetes, how to deploy?"
date: 2022-05-01T16:01:23+08:00
lastmod: 2022-05-01T16:01:23+08:00
draft: false
tags: ["kubernetes", "deploy"]
categories: ["kubernetes", "cloudnative"]
author: "yesplease"
---

汇总kubernetes部署的方案：

- kubernetes < 1.20 + centos7 + docker + iptables + flannel
- kubernetes < 1.20 + centos7 + docker + ipvs + calico

- 1.20 <kubernetes < 1.24 + centos7 + docker + ipvs + calico
- kubernetes > 1.24 + centos7 + containerd + ipvs + calico
- kubernetes > 1.24 + centos7 + cri-o + ipvs + calico
- kubernetes > 1.24 + centos7 + cri-dockerd + docker + ipvs + calico