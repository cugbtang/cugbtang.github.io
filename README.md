# yesplease's Technical Blog

A personal technical blog built with Hugo, focusing on Go programming, DevOps, Kubernetes, and software engineering.

![GitHub Actions](https://github.com/cugbtang/myBlog/actions/workflows/gh-pages.yml/badge.svg)

## Online Access

- Blog URL: [https://cugbtang.github.io/myBlog/](https://cugbtang.github.io/myBlog/)

## Features

- **Modern Static Site**: Built with [Hugo](https://gohugo.io/), fast and secure
- **Responsive Design**: Based on [Jane theme](https://github.com/xianmin/hugo-theme-jane), works on all devices
- **Multilingual Support**: Supports both Chinese and English content
- **Auto Deployment**: Automated build and deployment to GitHub Pages using GitHub Actions
- **Content Organization**: Clear categorization and series structure

## Content Categories

Blog content is organized by technical domains:

### Main Technical Areas
- **Go Programming**: Basics, application development, advanced features, tools, compilation, profiling
- **DevOps**: Git, Jenkins, SSH, and other operations tools and practices
- **Kubernetes**: Container orchestration, cluster management, application deployment
- **Microservices**: Architecture design, service governance, distributed systems
- **Container Technology**: Docker, containerization best practices
- **Software Engineering**: API design, system architecture, engineering practices
- **Frontend Development**: Vue.js and related technologies
- **LLM**: Large language models and related applications

### Fundamentals
- **Why Series**: Computer science fundamentals (algorithms, computer organization, networking, operating systems, databases, etc.)

## Local Development

### Requirements
- [Hugo Extended](https://gohugo.io/getting-started/installing/) (version >= 0.152.2)
- [Dart Sass](https://sass-lang.com/install) (for theme styles compilation)
- Git

### Installation Steps

1. **Clone repository**
   ```bash
   git clone https://github.com/cugbtang/myBlog.git
   cd myBlog
   ```

2. **Initialize theme**
   ```bash
   git submodule update --init --recursive
   ```

3. **Install dependencies**
   ```bash
   # Install Dart Sass (Ubuntu)
   sudo snap install dart-sass

   # For other systems, refer to Sass documentation
   ```

4. **Local development server**
   ```bash
   hugo server
   ```
   Visit http://localhost:1313 for local preview

### Creating New Articles

1. **Create new article using Hugo command**
   ```bash
   hugo new post/category/article-name.md
   ```

2. **Article Front Matter template**
   ```yaml
   ---
   title: "Article Title"
   date: 2024-01-01T10:00:00+08:00
   lastmod: 2024-01-01T10:00:00+08:00
   draft: true  # Set to false to publish
   tags: ["tag1", "tag2"]
   categories: ["category"]
   author: "yesplease"
   ---

   Article content...
   ```

## Deployment Process

This project uses GitHub Actions for automated deployment to GitHub Pages:

1. **Push code to master branch**
2. **GitHub Actions triggers build automatically**
3. **Build static site with Hugo**
4. **Deploy to gh-pages branch**
5. **Auto-publish to GitHub Pages**

### Workflow File
- `.github/workflows/gh-pages.yml` - Auto-deployment configuration

## Project Structure

```
myBlog/
├── content/                    # All content files
│   ├── post/                  # Blog posts
│   │   ├── go/               # Go programming
│   │   ├── devops/           # DevOps
│   │   ├── kubernetes/       # Kubernetes
│   │   └── ...              # Other categories
│   ├── why/                  # Fundamentals series
│   ├── _index.md            # English homepage
│   ├── _index.zh-cn.md      # Chinese homepage
│   └── about.md             # About page
├── themes/                   # Hugo themes
│   └── jane/                # Jane theme
├── static/                   # Static assets
├── layouts/                  # Custom layouts
├── hugo.toml                # Hugo configuration
├── .github/workflows/       # GitHub Actions config
└── README.md               # Project documentation
```

## Configuration

Main configuration file: `hugo.toml`

```toml
baseURL = "http://localhost:1313/"
title = "yesplease's blog"
theme = "jane"
hasCJKLanguage = true     # Supports Chinese/Japanese/Korean
defaultContentLanguage = "en"  # Default language
```

## Writing Guidelines

### Article Naming
- Series articles: `series-{topic}-{number}.md`
- Standalone articles: Use descriptive English or Chinese filenames
- Avoid spaces, use hyphens for separation

### Content Format
- Use Markdown syntax
- Code blocks with language specification
- Proper heading hierarchy
- Add relevant tags and categories

### Image Management
- Store images in `static/images/` directory
- Use relative paths for references
- Optimize image size for faster loading

## Contributing

Welcome to contribute in following ways:

1. **Report Issues**: Submit bugs or suggestions on [Issues](https://github.com/cugbtang/myBlog/issues) page
2. **Content Suggestions**: Discuss technical topics or propose writing ideas
3. **Technical Sharing**: Share your technical articles via Pull Request

### Pull Request Process
1. Fork this repository
2. Create feature branch (`git checkout -b feature/amazing-article`)
3. Commit changes (`git commit -m 'Add amazing article'`)
4. Push to branch (`git push origin feature/amazing-article`)
5. Open Pull Request

## License

Blog content is licensed under [Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License](https://creativecommons.org/licenses/by-nc-nd/4.0/).

Theme uses [MIT License](https://github.com/xianmin/hugo-theme-jane/blob/master/LICENSE.md).

## Contact

- **GitHub**: [@cugbtang](https://github.com/cugbtang)
- **Email**: cugbtang@sina.com
- **Blog**: [yesplease's blog](https://cugbtang.github.io/myBlog/)

---

*Last updated: December 2024*
*Built with ❤️*