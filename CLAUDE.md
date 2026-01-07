# CLAUDE.md

这个仓库是我的技术博客空间

## Project Overview

This is a Hugo-based personal blog using the "Jane" theme (hugo-theme-jane). The blog contains technical articles primarily focused on Go programming, DevOps, Kubernetes, and software engineering topics.

### Content Structure
- **Content**: `content/` - All blog posts and pages
  - `post/` - Blog posts organized by categories:
    - `go/` - Go programming articles (base, app, deep, tools, compile, profiling)
    - `devops/` - DevOps topics (Git, Jenkins, SSH, etc.)
    - `kubernetes/` - Kubernetes articles
    - `micro/` - Microservices
    - `container/` - Containerization
    - `engineer/` - Software engineering
    - `vue/` - Vue.js articles
    - `llm/` - LLM-related content
    - `coding/` - Claude Code documentation, technical translations with analogies, and practical demonstrations
  - `why/` - Educational articles about fundamental CS topics
  - `_index.md` and `_index.zh-cn.md` - Home pages for English and Chinese


### Content Organization
Posts are organized into series and categories:
- Series: Follow naming pattern `series-{topic}-{number}.md`
- Categories: Organized in subdirectories under `content/post/`
- Multilingual: Separate files for English and Chinese versions

### Coding Category Guidelines
The `coding/` category is dedicated to:
1. **Claude Code Documentation**: Tutorials, usage guides, and best practices for Claude Code
2. **Technical Translations**: Translated content enhanced with:
   - Simple analogies to explain complex concepts
   - Practical demonstrations and code examples
   - Contextual explanations beyond literal translation
3. **Learning Resources**: Articles focused on effective learning techniques, demonstration design, and knowledge transfer

**Content Structure for Coding Articles**:
- Include practical code examples with step-by-step explanations
- Use analogies to bridge abstract concepts with concrete understanding
- Provide interactive elements where readers can modify and experiment
- Focus on "why" and "how" rather than just "what"
- Include real-world applications and use cases