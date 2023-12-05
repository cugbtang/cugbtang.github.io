---
title: "micro, how to play api?"
date: 2023-11-29T15:44:23+08:00
lastmod: 2023-11-29T16:44:23+08:00
draft: false
tags: [ "api", "IDL"]
categories: ["api"]
author: "yesplease"
---

# API工程化：基于Proto的IDL管理和文档生成

在现代软件开发中，API工程化变得愈发重要。使用Proto作为接口定义语言（IDL），可以帮助团队更好地管理API和生成相关文档。本文将介绍一种基于Proto的IDL管理方式以及如何生成API文档。

## Proto的管理方式

在管理Proto文件时，可以采用多种方式，包括代码仓库、独立仓库、集中仓库和镜像仓库。其中，集中仓库的方式被提倡，有以下优点：
- 方便跨部门协作：将所有Proto文件放在同一个仓库中，可以方便不同团队之间的协作。
- 版本管理：使用git对Proto文件进行版本控制，确保修改和变更可追溯。
- 规范化检查：使用API lint工具对Proto文件进行规范化检查，确保符合规范和最佳实践。
- API设计评审：通过提交变更的diff，进行API设计评审，提高代码质量和设计性能。
- 权限管理：通过设定目录的OWNERS文件，对不同团队或个人设置读写权限，保护API的安全性。

另外，可以使用Proto的git submodule方式，将Proto文件作为仓库的子模块进行管理。这种方式可以实现以下功能：
- 将Proto文件作为代码仓库的一部分，保持其作为源数据的唯一性。
- 使用本地构建工具protoc依赖go module下的相对路径，方便在不同项目中引用Proto文件。
- 基于分支创建新的Proto文件，通过切换子模块分支生成相关代码，确保各个版本之间的兼容性。
- 维护Makefile来处理Proto文件的编译和构建工作，统一化处理流程。
- 使用声明式依赖方式，在yaml文件中指定protoc版本和Proto文件的依赖关系。

## IDL项目结构

良好的IDL项目结构能够提高团队协作和代码维护的效率。建议将目录结构和package对齐，以便更好地组织和管理Proto文件以及生成的代码。

典型的IDL项目结构如下：
```
├── api/
│   ├── user/
│   │   └── user.proto
│   ├── order/
│   │   └── order.proto
│   └── common/
│       └── common.proto
├── pkg/
│   ├── user/
│   │   └── user.go
│   ├── order/
│   │   └── order.go
│   └── common/
│       └── common.go
```

在这个结构中，`api/`目录存放所有的Proto文件，按照业务功能划分为子目录。`pkg/`目录存放生成的代码，与`api/`目录一一对应。通过这种结构，可以清晰地区分Proto文件和生成的代码，便于团队进行开发和维护。

## IDL错误处理

在编写API时，处理错误是非常重要的一部分。为了使不同的API、协议和错误上下文之间保持一致的体验，建议使用简单的协议无关错误模型。具体做法包括：
- 使用一小组标准错误，覆盖大量资源。
- 合理传播错误：如果你的API服务依赖其他服务，不应该盲目地将这些服务的错误传播给客户端。推荐的做法包括：
  - 隐藏实现详细信息和机密信息，避免暴露敏感数据。
  - 根据错误责任方调整错误处理，对于感兴趣的翻译错误提供有意义的信息，对于不感兴趣的错误提供通用的"Unknown"错误提示。

通过以上方式，可以统一错误处理的规范，并提供更好的错误信息给客户端，提高用户体验和调试效率。

## IDL文档生成

为了方便使用和理解API，生成API文档是必不可少的。可以使用基于OpenAPI插件和Proto注释的方式生成文档，具体步骤如下：
- 在Proto文件中添加注释，描述每个接口的用途、参数和返回值等信息。
- 使用OpenAPI插件，解析Proto文件和注释，生成OpenAPI规范的yaml文件。
- 在项目的Makefile中添加生成API文档的脚本，执行`make api`命令即可生成对应的OpenAPI文档。
- 可以通过GitLab或VS Code插件直接查看和编辑生成的OpenAPI文档，方便团队进行微服务治理、调试和测试等工作。

通过以上方式，团队可以轻松生成和维护API文档，提高开发效率和团队协作能力。

本文介绍了基于Proto的IDL管理和文档生成的方法，包括Proto的管理方式、IDL项目结构、错误处理和文档生成等内容。通过合理规划和使用这些方法，可以提高API工程化水平，推动团队的协作和开发效率。

总结：

在API工程化中，Proto的管理方式、IDL项目结构、错误处理和文档生成是非常重要的一部分。通过集中管理Proto文件、规范项目结构、统一错误处理和生成易于理解的API文档，可以提高团队的开发效率和 API的质量。同时，不断优化和改进这些方法，可以实现持续集成和交付，适应快速迭代的开发环境。希望本文对您有所启发，让您的API工程化之路更加顺利！

## 参考
- [API工程化分享 - 毛剑](https://www.bilibili.com/video/BV17m4y1f7qc/?spm_id_from=333.880.my_history.page.click&vd_source=9573f6b9b39a65fed99157eefcfdfb74)
- [https://github.com/go-kratos/kratos](https://github.com/go-kratos/kratos)
- [https://github.com/googleapis/googleapis/blob/master/google/rpc/error_details.proto#L112](https://github.com/googleapis/googleapis/blob/master/google/rpc/error_details.proto#L112)
- [https://github.com/pkg/errors](https://github.com/pkg/errors)
- [https://mp.weixin.qq.com/s/cBXZjg_R8MLFDJyFtpjVVQ](https://mp.weixin.qq.com/s/cBXZjg_R8MLFDJyFtpjVVQ)