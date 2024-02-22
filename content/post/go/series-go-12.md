---
title: "Go function option vs builder, how to play?"
date: 2024-01-05T16:01:23+08:00
lastmod: 2024-01-05T16:01:23+08:00
draft: false
tags: ["go","concurrent"]
categories: ["go"]
author: "yesplease"
---


## Go 构建对象模式

Function Option 是一种通过函数选项来配置函数参数的方式。通过在函数中定义多个接受选项参数的函数，可以根据需要选择性地传递这些选项，而不是像传统方式那样传递一长串参数。这样可以使函数调用更清晰易读，避免参数传递顺序混乱的问题。

Builder 模式则是一种用于构建复杂对象的设计模式。在 Go 中，Builder 通常通过链式调用一系列方法来构建对象，并在最后通过一个构建方法返回所需的对象实例。这种方式可以让我们以一种流畅的方式来构建对象，同时也可以灵活地添加或修改构建过程中的步骤。

Function Option 更适合于需要配置多个参数的函数，而 Builder 更适合于需要构建复杂对象的情况。两者都能提高代码的可读性和灵活性，使得代码更易于维护和扩展。


### 简单的构造函数
```go
type Option struct {
	A string
	B string
	C int
}
func newOption(a, b string, c int) *Option {
	return &amp;Option{
		A: a,
		B: b,
		C: c,
	}
}
```

### function option
场景：
1、我们可能需要为Option的字段指定默认值
2、Option的字段成员可能会发生变更

```go
type OptionFunc func(*Option)

func WithA(a string) OptionFunc {
	return func(o *Option) {
		o.A = a
	}
}

func WithB(b string) OptionFunc {
	return func(o *Option) {
		o.B = b
	}
}

func WithC(c int) OptionFunc {
	return func(o *Option) {
		o.C = c
	}
}

var (
	defaultOption = &amp;Option{
		A: &quot;A&quot;,
		B: &quot;B&quot;,
		C: 100,
	}
)

func newOption(opts ...OptionFunc) (opt *Option) {
	opt = defaultOption
	for _, o := range opts {
		o(opt)
	}
	return
}
```

### builder

```go
type Builder struct {
	opt *Option
}

func NewBuilder() *Builder {
	return &Builder{
		opt: &Option{},
	}
}

func (b *Builder) WithA(a string) *Builder {
	b.opt.A = a
	return b
}

func (b *Builder) WithB(b2 string) *Builder {
	b.opt.B = b2
	return b
}

func (b *Builder) WithC(c int) *Builder {
	b.opt.C = c
	return b
}

func (b *Builder) Build() *Option {
	return b.opt
}

builder := NewBuilder()
option := builder.WithA("new A").WithB("new B").WithC(200).Build()
fmt.Printf("%+v\n", option)

```