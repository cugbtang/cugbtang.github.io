---
title: "Go function interface, how to play?"
date: 2024-01-05T16:01:23+08:00
lastmod: 2024-01-05T16:01:23+08:00
draft: false
tags: ["go","function","interface"]
categories: ["go"]
author: "yesplease"
---

## 接口型函数

在 Go 语言中，函数也可以作为接口的一部分，这种称为函数接口（Function Interface）的概念让我们可以更加灵活地定义接口和实现。

通过函数接口，我们可以将函数作为接口的方法，这样就可以将不同的函数赋值给接口变量，并通过接口变量来调用这些函数。这种方式类似于将函数当作一种行为或特性来对待，使得我们可以更加方便地实现多态性和组合性。

使用函数接口，我们可以定义一个接口，然后让不同的函数去实现这个接口，从而实现统一的调用方式。这种方式非常适合于需要根据不同情况动态选择具体实现的场景，让代码更加灵活、可扩展和易于维护。

总的来说，函数接口是 Go 语言中一种非常有用的特性，它让我们可以将函数作为一种行为来对待，更加灵活地定义接口和实现，从而实现代码的解耦和灵活性。

### 1、例子
```go
// A Getter loads data for a key.
type Getter interface {
	Get(key string) ([]byte, error)
}

// A GetterFunc implements Getter with a function.
type GetterFunc func(key string) ([]byte, error)

// Get implements Getter interface function
func (f GetterFunc) Get(key string) ([]byte, error) {
	return f(key)
}
```
### 2、为什么这么设计

一般有接口参与的设计会增加使用的通用性。

我们想象这么一个使用场景，GetFromSource 的作用是从某数据源获取结果，接口类型 Getter 是其中一个参数，代表某数据源。
```go
func GetFromSource(getter Getter, key string) []byte {
	buf, err := getter.Get(key)
	if err == nil {
		return buf
	}
	return nil
}
```
- 方式一：GetterFunc 类型的函数作为参数
```go
//匿名
GetFromSource(GetterFunc(func(key string) ([]byte, error) {
	return []byte(key), nil
}), "hello")

// 普通
func test(key string) ([]byte, error) {
	return []byte(key), nil
}

func main() {
    GetFromSource(GetterFunc(test), "hello")
}
```

- 方式二：实现了 Getter 接口的结构体作为参数
```go
type DB struct{ url string}

func (db *DB) Query(sql string, args ...string) string {
	// ...
	return "hello"
}

func (db *DB) Get(key string) ([]byte, error) {
	// ...
	v := db.Query("SELECT NAME FROM TABLE WHEN NAME= ?", key)
	return []byte(v), nil
}

func main() {
	GetFromSource(new(DB), "hello")
}
```