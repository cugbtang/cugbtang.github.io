# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Hugo-based personal blog using the "Jane" theme (hugo-theme-jane). The blog contains technical articles primarily focused on Go programming, DevOps, Kubernetes, and software engineering topics.

## Development Commands

### Local Development
```bash
# Start the local development server
hugo server

# Build the site (outputs to public/ directory)
hugo --minify

# Build with draft posts included
hugo server --buildDrafts
```

### Requirements
- Hugo (extended version) - v0.152.2 (as specified in GitHub Actions)
- Dart Sass for SCSS compilation

## Code Architecture

### Key Configuration
- **Main config**: `hugo.toml` - Site configuration, theme settings, menus, and parameters
- **Theme**: `themes/jane/` - Customized Jane theme with Pico CSS
- **Style settings**: `themes/jane/assets/sass/_settings.scss` - Theme customization including colors, fonts, and layout

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
  - `why/` - Educational articles about fundamental CS topics
  - `_index.md` and `_index.zh-cn.md` - Home pages for English and Chinese

### Theme Customization
The Jane theme is customized via:
- **Theme color**: Currently set to 'jade' in `_settings.scss`
- **Font settings**: Custom font families for logo, titles, and body text
- **Layout settings**: Article max width, header heights, mobile breakpoints
- **Multilingual support**: Both English and Chinese content supported

### Front Matter
Posts use TOML front matter with standard Hugo fields:
```toml
+++
date = '{{ .Date }}'
draft = true
title = '{{ replace .File.ContentBaseName "-" " " | title }}'
+++
```

### Content Organization
Posts are organized into series and categories:
- Series: Follow naming pattern `series-{topic}-{number}.md`
- Categories: Organized in subdirectories under `content/post/`
- Multilingual: Separate files for English and Chinese versions

## Deployment

### GitHub Actions
- **Workflow**: `.github/workflows/gh-pages.yml`
- **Trigger**: Push to master branch
- **Process**:
  1. Checkout with submodules (themes)
  2. Setup Hugo v0.152.2 extended
  3. Install Dart Sass
  4. Build with `hugo --minify`
  5. Deploy to GitHub Pages from `./public`

### Theme-Specific Features
- **Reading experience**: Optimized for readability with clean typography
- **Responsive design**: Mobile-friendly with responsive breakpoints
- **Syntax highlighting**: Uses Chroma for code highlighting
- **Photo galleries**: PhotoSwipe integration for image galleries
- **TOC support**: Automatic table of contents generation
- **Multilingual**: Full i18n support with Chinese translations

## Important Notes

- The theme uses Pico CSS for styling with customizable color schemes
- Content is organized in series - maintain consistent naming when adding new posts
- The site supports both English and Chinese content
- All custom styles should be added through the `_settings.scss` file to maintain theme compatibility
- The `public/` directory is generated and should not be committed to version control