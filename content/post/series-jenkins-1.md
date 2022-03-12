---
title: "Jenkins, how to play?"
date: 2018-03-01T16:01:23+08:00
lastmod: 2018-03-01T16:01:23+08:00
draft: false
tags: ["cicd", "jenkins"]
categories: ["cicd", "jenkins"]
author: "yesplease"
---
# how to play jenkins?



> 社区源码、文档[^footnote1]等托管在 GitHub 上。
[^footnote1]: https://github.com/jenkins-zh/jenkins-zh/wiki
>
> 其中基础设施部分在 [`jenkins-infra`](https://github.com/jenkins-infra)；
>
> 核心库以及插件在 [`jenkinsci`](https://github.com/jenkinsci/)[^footnote2]；
[^footnote2]: https://github.com/jenkinsci/
>
> Jenkins 中文本地化相关的项目在 [`jenkins-zh`](https://github.com/jenkins-zh) 
>
> 集中玩耍地地方[^footnote3]
[^footnote3]: https://github.com/jenkins-zh/jenkins-zh/issues



## 搜集玩法



- 1、官方建议容器化部署（docker/kubernetes）

  > 建议使用的Docker映像是[`jenkinsci/blueocean` image](https://hub.docker.com/r/jenkinsci/blueocean/)(来自 the [Docker Hub repository](https://hub.docker.com/))。 该镜像包含当前的[长期支持 (LTS) 的Jenkins版本](https://www.jenkins.io/download) （可以投入使用） ，捆绑了所有Blue Ocean插件和功能。这意味着你不需要单独安装Blue Ocean插件。

  ```sh
  docker run \
    -u root \
    --rm \
    -d \
    -p 8080:8080 \
    -p 50000:50000 \
    -v jenkins-data:/var/jenkins_home \
    -v /var/run/docker.sock:/var/run/docker.sock \
    jenkinsci/blueocean
  ```

  能玩一段时间了。。。

  

- 2、前面都是铺垫，玩了一段时间，发现原生镜像中缺这少那的，尤其是插件，看看**官方**怎么说：

  > Keep in mind that the process described above will automatically download the official Jenkins Docker image if this hasn’t been done before.

  - Create Dockerfile with the following content:

    ```sh
    FROM jenkinsci/blueocean
    USER root
    RUN apt-get update && apt-get install -y lsb-release
    RUN curl -fsSLo /usr/share/keyrings/docker-archive-keyring.asc \
      https://download.docker.com/linux/debian/gpg
    RUN echo "deb [arch=$(dpkg --print-architecture) \
      signed-by=/usr/share/keyrings/docker-archive-keyring.asc] \
      https://download.docker.com/linux/debian \
      $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
    RUN apt-get update && apt-get install -y docker-ce-cli
    USER jenkins
    RUN jenkins-plugin-cli --plugins "blueocean:1.25.3 docker-workflow:1.28"
    ```

    

  - Build a new docker image from this Dockerfile and assign the image a meaningful name, e.g. "myjenkins-blueocean:2.319.3-1":

    ```sh
    docker build -t myjenkins-blueocean:2.319.3-1 .
    ```

- 3、同时，也可以站在巨人的肩膀上，有一些实践者把**常用的插件**已经内置到镜像发布了，比如 `kubespheredev/ks-jenkins`

- 4、程序员用界面？命令行起飞 

  > [利用 jcli 管理 Jenkins](https://www.jenkins.io/zh/blog/2019/08/30/jenkins-cli/)
  >
  > vs
  >
  > [原生Jenkins CLI ](https://www.jenkins.io/doc/book/managing/cli/)

  ```sh
  # 例如，本地敏捷调试
  # 安装
  wget -q https://ghproxy.com/https://github.com/jenkins-zh/jenkins-cli/releases/latest/download/jcli-linux-amd64.tar.gz|tar -zxvf && sudo mv jcli /usr/local/bin/
  # 配置
  jcli config gen
  # 都走默认就🆗
  
  # 启动
  jcli center start -m docker --image kubespheredev/ks-jenkins --version 2.249.1 --c-user root --port 8080 --setup-wizard=false
  ```

  

- 5、国内插件源

  >  `https://updates.jenkins-zh.cn/update-center.json`

- 6、划重点，就是 **pipeline**（前面的插件已经铺垫过）。what？？？

  > #### pipeline ==~ “持续交付即代码”
  >
  > Jenkins Pipeline 的定义通常被写入到一个文本文件（称为 `Jenkinsfile` ）中，该文件可以被放入项目的源代码控制库中。
  >
  > official recommended  how to play:  **all in Jenkinsfile!!!**

  - [get started with Pipeline](https://www.jenkins.io/doc/book/pipeline/getting-started) - covers how to [define a Jenkins Pipeline](https://www.jenkins.io/doc/book/pipeline/getting-started#defining-a-pipeline) (i.e. your `Pipeline`) through [Blue Ocean](https://www.jenkins.io/doc/book/pipeline/getting-started#through-blue-ocean), through the [classic UI](https://www.jenkins.io/doc/book/pipeline/getting-started#through-the-classic-ui) or in [SCM](https://www.jenkins.io/doc/book/pipeline/getting-started#defining-a-pipeline-in-scm),
  - [create and use a `Jenkinsfile`](https://www.jenkins.io/doc/book/pipeline/jenkinsfile) - covers use-case scenarios on how to craft and construct your `Jenkinsfile`,
  - work with [branches and pull requests](https://www.jenkins.io/doc/book/pipeline/multibranch),
  - [use Docker with Pipeline](https://www.jenkins.io/doc/book/pipeline/docker) - covers how Jenkins can invoke Docker containers on agents/nodes (from a `Jenkinsfile`) to build your Pipeline projects,
  - [extend Pipeline with shared libraries](https://www.jenkins.io/doc/book/pipeline/shared-libraries),
  - use different [development tools](https://www.jenkins.io/doc/book/pipeline/development) to facilitate the creation of your Pipeline, and
  - work with [Pipeline syntax](https://www.jenkins.io/doc/book/pipeline/syntax) - this page is a comprehensive reference of all Declarative Pipeline syntax.

  

  > （片段生成器+声明式+。。。反正就是生成）https://jenkins地址/job/test/pipeline-syntax/ 
  >
  > +
  >
  > [【官方词典】](https://www.jenkins.io/doc/book/pipeline/)

  ![image-20220302150354810](https://raw.githubusercontent.com/cugbtang/image-repo/master/PicGo/20220302150355.png)

- 7、**官方**把架子打好了，让我们发挥是吧，那有木有前辈累计的模板，或者我有新颖的使用方式方法想分享给大家呢：

  > enjoy your play: 

  [【官方例子】](https://github.com/jenkinsci/pipeline-examples)

  [【DevOps Workspace】](https://github.com/devops-ws)

- 8、又玩了一段时间，发现jenkins最好是作为自动化的引擎，通过接口集成到 PASS 上。

  > Use Pipeline through API

  [one example](https://github.com/go-atomci/workflow)


##  都在玩儿plugin

- Jenkins Configuration as Code[^footnote4]
[^footnote4]: https://github.com/jenkinsci/configuration-as-code-plugin/tree/master/demos

  > 虽然新部署的 Jenkins 实例自动为我们安装了所有所需的插件，并配置好了初始化 Job 等工作，但在开始使用它之前，我们仍需要完成一系列手动工作，如配置 Jenkins 的 “Configure System” 页面

  > 如果你是一名 Jenkins 管理员，那么你一定不会对这个页面感到陌生，每次部署完一个新的 Jenkins 实例，在可以使用之前，我们往往都需要在该页面作出一些相应的配置。该页面除了包含 Jenkins 自身的一些基本配置信息外，同时还包括了当前系统中所安装的插件的配置信息。也就是说，当你的 Jenkins 安装的插件越多，该页面的配置项就有可能会越多。

  ```yaml
  云时代 这个插件用处就少些了，所有的配置都放在
  ```

  
