---
title: "Go tools, how to play?"
date: 2024-01-05T16:01:23+08:00
lastmod: 2024-01-05T16:01:23+08:00
draft: false
tags: ["go","test"]
categories: ["go"]
author: "yesplease"
---


- Delve是一个基于命令行的Go语言调试器，它提供了类似于GDB的功能，支持设置断点、单步执行、查看变量值、调用堆栈等操作。相比于GDB，Delve更加方便易用，支持直接在命令行中输入Go表达式进行求值。Delve还支持VSCode和GoLand等集成开发环境中的调试器扩展。

- GDB是GNU Debugger的简称，是一个UNIX系统下的命令行调试器。它能够调试多种编程语言，包括C、C++、Go等。GDB是一个非常强大的调试工具，支持设置断点、单步执行、查看变量值、调用堆栈等操作。但是，相比于Delve，它的使用起来略显复杂。

- gopls是Go语言提供的一个语言服务器，提供了自动补全、代码重构、跳转定义、查找引用等功能。它可与各种编辑器和集成开发环境集成，如VSCode、GoLand、Emacs等。

- dlv是Delve的缩写，也是一个基于命令行的Go语言调试器，它是Delve的CLI版本。dlv支持所有Delve所支持的调试功能，与Delve相比，它更加轻量级，适合在终端中使用。

