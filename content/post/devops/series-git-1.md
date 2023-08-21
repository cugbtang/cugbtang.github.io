---
title: "git 部分功能需要先上线，怎么办？"
date: 2023-07-30T16:01:23+08:00
lastmod: 2023-07-30T16:01:23+08:00
draft: false
tags: ["devops", "git"]
categories: ["devops", "cloudnative"]
author: "yesplease"
---

## git 部分功能需要先上线，怎么办？


## 一、场景描述

 在这个项目中，代码的提交和合并都是在develop分支上进行的， 之前已经基于某个commit打了tag v1.0.0。然而，这次由于迭代过程中需要提前上线部分功能，我们需要将这部分功能的commit摘出来，并打上一个tag v1.1.0 作为标识。



## 二、问问 gpt[^1]

首先，我们可以使用Git命令行或者图形化界面工具来处理这个需求。假设我们当前的工作目录在develop分支上。

- 确保你的本地develop分支是最新的，可以执行以下命令拉取最新的代码：
```sh
git pull origin develop
```
- 查看git log，找到需要提前上线的commit的哈希值或者commit消息。

- 使用以下命令将指定的commit摘出来并创建一个新的分支（例如feature-branch）：
```sh
git checkout -b feature-branch <commit>
```
这将创建一个新的分支，并将代码库中指定的commit复制到该分支上。

- 使用以下命令将涉及到这次提前发布需要的commit提交应用到feature-branch分支：
```sh
git cherry-pick <commit1> <commit2> <commit1> <commit1>
```
其中，`<commit>` 可以是提交的哈希值或者提交消息。

- 接下来，我们需要打上一个tag来标识这个版本。使用以下命令创建一个tag（例如v1.1.0）：
```sh
git tag v1.1.0
```
这将在当前commit上创建一个tag。

- 最后，将创建的分支和tag推送到远程仓库：
```sh
git push origin feature-branch
git push origin v1.1.0
```
这将把新的分支和tag推送到远程仓库中，以便团队成员可以访问和查看。

## 三、小结：

 - 基于某个commit checkout
 - cherry-pick[^2]

## 四、参考

[^1]: [gpt]()

[^2]: [git-cherry-pick](https://www.git-scm.com/docs/git-cherry-pick)
