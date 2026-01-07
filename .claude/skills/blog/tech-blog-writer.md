# 技术博客文档编写Skill

## 概述
这是一个专门为计算机、全栈开发和前沿技术博客设计的Claude Code skill。它帮助用户高效编写技术博客文档，遵循Hugo+Jane主题的最佳实践。

## 项目上下文
- **博客平台**: Hugo静态网站生成器
- **主题**: Jane主题 (hugo-theme-jane)
- **内容分类**: Go编程、DevOps、Kubernetes、微服务、容器、软件工程、Vue.js、LLM等
- **内容结构**: 系列文章（series-{topic}-{number}.md格式）
- **多语言支持**: 英文和中文内容

## 核心功能

### 1. 文章创建助手
根据Hugo front matter格式创建新博客文章，包含：
- 自动生成front matter（title, date, draft状态, tags, categories, author）
- 支持系列文章编号
- 根据分类自动选择正确的目录路径
- 多语言内容支持

### 2. 技术内容结构模板
提供标准化的技术文章结构：
- 问题陈述/引言
- 核心概念解释
- 代码示例和解释
- 实践应用场景
- 总结和扩展阅读

### 3. 代码示例集成
支持多种编程语言的代码示例：
- Go代码示例（支持并发、接口、反射等高级特性）
- JavaScript/TypeScript示例
- Shell脚本
- 配置文件和Dockerfile
- API示例（REST、GraphQL等）

### 4. 系列文章管理
- 系列文章命名规范（series-{topic}-{number}）
- 系列文章间的链接和导航
- 系列目录维护

### 5. 多媒体集成
- 图片插入和优化
- 图表和流程图支持
- 视频嵌入（如需）

## 使用指南

### 基本文章创建流程
1. 确定文章主题和技术分类
2. 选择文章类型（独立文章或系列文章）
3. 提供文章大纲或主要要点
4. 生成front matter和文章结构
5. 填充详细内容，包括代码示例
6. 添加标签和分类
7. 预览和优化

### 技术分类对应目录
- Go编程: `content/post/go/{base|app|deep|tools|compile|profiling}/`
- DevOps: `content/post/devops/`
- Kubernetes: `content/post/kubernetes/`
- 微服务: `content/post/micro/`
- 容器技术: `content/post/container/`
- 软件工程: `content/post/engineer/`
- Vue.js: `content/post/vue/`
- LLM: `content/post/llm/`
- Claude Code: `content/post/coding/`

### Front Matter模板
```yaml
---
title: "文章标题"
date: YYYY-MM-DDTHH:MM:SS+08:00
lastmod: YYYY-MM-DDTHH:MM:SS+08:00
draft: true/false
tags: ["标签1", "标签2"]
categories: ["分类"]
author: "yesplease"
---
```

### 代码示例最佳实践
1. 提供完整的可运行代码片段
2. 添加详细的注释和解释
3. 展示输入/输出示例
4. 解释关键概念和技术要点
5. 提供实际应用场景

## 高级功能

### 1. 技术概念解释
- 使用类比简化复杂概念
- 提供实际应用场景
- 对比不同技术方案
- 解释技术演进路径

### 2. 学习路径设计
- 结构化学习内容
- 循序渐进的知识传递
- 实践项目指导
- 扩展阅读推荐

### 3. 演示和实验设计
- 交互式代码示例
- 逐步实现指导
- 调试和问题解决示例
- 性能优化指导

### 4. 翻译和本地化
- 技术术语一致性
- 文化适配
- 本地化示例
- 多语言内容同步

## 质量保证

### 内容质量标准
- 技术准确性
- 代码正确性和最佳实践
- 清晰的解释和示例
- 一致的结构和格式
- 适当的深度和广度

### 技术审查要点
- 代码安全性
- 性能考虑
- 兼容性和可移植性
- 现代技术标准遵循
- 文档完整性

## 集成工具

### Hugo相关命令
```bash
# 启动开发服务器
hugo server --buildDrafts --port 1313

# 构建网站
hugo

# 创建新内容
hugo new post/category/article-name.md
```

### 预览和测试
- 本地Hugo服务器预览
- 语法和格式检查
- 链接验证
- 响应式设计测试

## 示例场景

### 场景1：编写Go并发教程
1. 创建系列文章：`series-go-concurrent-1.md`
2. 包含goroutine基础概念
3. 提供channel使用示例
4. 演示select语句
5. 展示实际应用案例

### 场景2：Kubernetes部署指南
1. 创建系列文章：`series-kubernetes-deploy-1.md`
2. 解释Pod、Service、Deployment概念
3. 提供YAML配置示例
4. 展示部署流程
5. 故障排除指南

### 场景3：前端技术栈教程
1. 创建Vue.js组件教程
2. 包含现代前端工具链
3. 提供TypeScript示例
4. 展示构建和部署流程
5. 性能优化技巧

## 持续改进

### 反馈机制
- 读者反馈收集
- 技术更新跟踪
- 内容质量评估
- 格式和结构优化

### 内容策略
- 技术趋势跟踪
- 读者需求分析
- 内容深度调整
- 互动元素增强

---

**使用提示**: 当需要编写技术博客文档时，参考此skill提供的结构和最佳实践，确保内容质量和技术准确性。