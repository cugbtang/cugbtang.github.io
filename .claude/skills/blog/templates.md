# 技术博客模板库

## 基础文章模板

### 模板1：技术教程文章
```markdown
---
title: "技术主题教程"
date: YYYY-MM-DDTHH:MM:SS+08:00
lastmod: YYYY-MM-DDTHH:MM:SS+08:00
draft: true
tags: ["标签1", "标签2", "标签3"]
categories: ["技术分类"]
author: "yesplease"
---

## 引言
简要介绍技术主题，说明学习的重要性和应用场景。

## 核心概念
解释技术的基本概念和原理。

## 基础用法
展示基本的使用方法和示例代码。

```go
// Go示例代码
package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}
```

## 高级特性
介绍更高级的功能和使用技巧。

## 实际应用
展示在实际项目中的应用案例。

## 最佳实践
总结使用该技术的最佳实践。

## 总结
回顾主要内容，提供进一步学习的方向。

## 参考资源
- 官方文档链接
- 相关教程和文章
- 开源项目示例
```

### 模板2：问题解决方案
```markdown
---
title: "解决[具体问题]"
date: YYYY-MM-DDTHH:MM:SS+08:00
lastmod: YYYY-MM-DDTHH:MM:SS+08:00
draft: true
tags: ["问题解决", "调试", "故障排除"]
categories: ["技术分类"]
author: "yesplease"
---

## 问题描述
详细描述遇到的问题和现象。

## 环境信息
- 操作系统：
- 编程语言版本：
- 相关工具版本：
- 依赖库版本：

## 问题分析
分析问题可能的原因。

## 排查步骤
记录排查问题的详细步骤。

## 解决方案
提供最终的解决方案和实现代码。

```bash
# 解决方案示例
$ command --to-fix-problem
```

## 预防措施
建议如何避免类似问题的发生。

## 总结
总结问题解决的经验教训。
```

## 系列文章模板

### 模板3：系列文章第一篇
```markdown
---
title: "系列名称 - 第一部分：基础概念"
date: YYYY-MM-DDTHH:MM:SS+08:00
lastmod: YYYY-MM-DDTHH:MM:SS+08:00
draft: true
tags: ["系列标签", "技术标签"]
categories: ["技术分类"]
author: "yesplease"
---

> 本系列文章索引：
> 1. [第一部分：基础概念](/post/category/series-topic-1/) ← 当前文章
> 2. [第二部分：进阶应用](/post/category/series-topic-2/)
> 3. [第三部分：实战项目](/post/category/series-topic-3/)

## 系列介绍
介绍本系列文章的目的和学习目标。

## 基础概念
详细解释相关的基础概念。

## 安装和配置
提供安装和配置步骤。

## 第一个示例
创建第一个简单的示例。

## 下一步
预告下一篇文章的内容。
```

### 模板4：系列文章中间篇
```markdown
---
title: "系列名称 - 第N部分：具体主题"
date: YYYY-MM-DDTHH:MM:SS+08:00
lastmod: YYYY-MM-DDTHH:MM:SS+08:00
draft: true
tags: ["系列标签", "技术标签"]
categories: ["技术分类"]
author: "yesplease"
---

> 本系列文章索引：
> 1. [第一部分：基础概念](/post/category/series-topic-1/)
> 2. [第二部分：进阶应用](/post/category/series-topic-2/)
> 3. [第N部分：具体主题](/post/category/series-topic-N/) ← 当前文章
> 4. [下一部分：继续主题](/post/category/series-topic-N+1/)

## 回顾
简要回顾前几篇文章的主要内容。

## 新概念介绍
介绍本篇文章要讲解的新概念。

## 详细讲解
深入讲解技术细节。

## 代码示例
提供详细的代码示例和解释。

## 实践练习
提供读者可以动手实践的练习。

## 下一步
预告下一篇文章的内容。
```

## 技术分类特定模板

### Go编程模板
```markdown
---
title: "Go技术主题"
date: YYYY-MM-DDTHH:MM:SS+08:00
lastmod: YYYY-MM-DDTHH:MM:SS+08:00
draft: true
tags: ["go", "golang", "特定技术"]
categories: ["go"]
author: "yesplease"
---

## Go特性介绍
介绍相关的Go语言特性。

## 代码示例
```go
package main

import (
    "fmt"
    "sync"
)

func main() {
    var wg sync.WaitGroup

    for i := 0; i < 5; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            fmt.Printf("Goroutine %d\n", id)
        }(i)
    }

    wg.Wait()
}
```

## 性能考虑
讨论性能优化和相关考虑。

## 最佳实践
Go语言的最佳实践建议。
```

### DevOps模板
```markdown
---
title: "DevOps实践指南"
date: YYYY-MM-DDTHH:MM:SS+08:00
lastmod: YYYY-MM-DDTHH:MM:SS+08:00
draft: true
tags: ["devops", "ci-cd", "自动化"]
categories: ["devops"]
author: "yesplease"
---

## DevOps概念
解释DevOps的核心概念。

## 工具链介绍
介绍相关的DevOps工具。

## 配置文件示例
```yaml
# Jenkins pipeline示例
pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                sh 'go build ./...'
            }
        }
        stage('Test') {
            steps {
                sh 'go test ./...'
            }
        }
        stage('Deploy') {
            steps {
                sh './deploy.sh'
            }
        }
    }
}
```

## 实施步骤
详细的实施步骤和注意事项。

## 监控和优化
监控指标和优化建议。
```

### Kubernetes模板
```markdown
---
title: "Kubernetes部署指南"
date: YYYY-MM-DDTHH:MM:SS+08:00
lastmod: YYYY-MM-DDTHH:MM:SS+08:00
draft: true
tags: ["kubernetes", "k8s", "容器编排"]
categories: ["kubernetes"]
author: "yesplease"
---

## Kubernetes概念
解释相关的Kubernetes概念。

## 资源配置
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: example-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: example
  template:
    metadata:
      labels:
        app: example
    spec:
      containers:
      - name: app
        image: example/app:latest
        ports:
        - containerPort: 8080
```

## 部署步骤
详细的部署步骤。

## 故障排除
常见问题和解决方法。

## 优化建议
性能优化和安全建议。
```

## 内容增强模板

### 代码解释模板
```markdown
## 代码解析

### 代码片段
```go
// 代码示例
func example() {
    // 代码内容
}
```

### 逐行解释
1. **第1行**: 解释第一行的作用和意义
2. **第2行**: 解释第二行的作用和意义
3. **第3行**: 解释第三行的作用和意义

### 关键概念
- 概念1: 解释
- 概念2: 解释
- 概念3: 解释

### 实际应用
说明在实际项目中如何应用这个代码模式。
```

### 对比分析模板
```markdown
## 技术对比

### 方案A
**优点**:
- 优点1
- 优点2

**缺点**:
- 缺点1
- 缺点2

### 方案B
**优点**:
- 优点1
- 优点2

**缺点**:
- 缺点1
- 缺点2

### 选择建议
根据不同的使用场景提供选择建议：
- 场景1: 建议使用方案A，因为...
- 场景2: 建议使用方案B，因为...
- 场景3: 可以根据具体需求选择...
```

### 学习路径模板
```markdown
## 学习路径

### 初学者阶段
1. **第一步**: 学习基础概念
   - 资源推荐
   - 练习题目
2. **第二步**: 完成简单项目
   - 项目示例
   - 实现指导

### 进阶阶段
1. **深入理解**: 学习高级特性
2. **实践项目**: 完成复杂项目

### 专家阶段
1. **源码分析**: 深入理解实现原理
2. **性能优化**: 学习优化技巧
3. **贡献社区**: 参与开源项目
```

## 实用工具函数

### Front Matter生成函数
```bash
# 生成当前日期的front matter
generate_front_matter() {
    local title="$1"
    local tags="$2"
    local category="$3"
    local date=$(date +"%Y-%m-%dT%H:%M:%S+08:00")

    echo "---"
    echo "title: \"$title\""
    echo "date: $date"
    echo "lastmod: $date"
    echo "draft: true"
    echo "tags: [$tags]"
    echo "categories: [\"$category\"]"
    echo "author: \"yesplease\""
    echo "---"
    echo ""
}
```

### 系列文章链接生成
```bash
# 生成系列文章导航
generate_series_nav() {
    local series_name="$1"
    local total_parts="$2"
    local current_part="$3"
    local category="$4"

    echo "> 本系列文章索引："
    for ((i=1; i<=total_parts; i++)); do
        if [ $i -eq $current_part ]; then
            echo "> $i. [第$i部分：...](/post/$category/series-$series_name-$i/) ← 当前文章"
        else
            echo "> $i. [第$i部分：...](/post/$category/series-$series_name-$i/)"
        fi
    done
    echo ""
}
```