---
title: "Go concurrent, how to play?"
date: 2024-01-05T16:01:23+08:00
lastmod: 2024-01-05T16:01:23+08:00
draft: false
tags: ["go","concurrent"]
categories: ["go"]
author: "yesplease"
---

## Introduction

首先，让我们来理解一下 goroutine。Goroutine 是一种轻量级的线程，由 Go 运行时环境管理。在 Go 语言中，你可以通过关键字 go 来启动一个新的 goroutine，而不需要手动创建线程。这意味着你可以很容易地并发地执行多个任务，而不必担心线程管理的复杂性。

其次，Go 语言还引入了 channel 的概念，用于在不同的 goroutine 之间进行通信和数据交换。Channel 可以被用来发送和接收数值，这样不同的 goroutine 就可以安全地共享数据，而无需担心竞态条件和锁的问题。

通过使用 goroutine 和 channel，你可以很方便地编写并发程序，实现并行执行任务、协作处理数据等操作。这种并发模型使得 Go 语言在处理大规模并发任务时表现出色，并且相对容易理解和维护。

## concurrent
- goroutine
- channel
- select
- sync
- atomic
- context
- sync/atomic
- sync/pool
- sync/waitgroup
- sync/map
- sync/once
- sync/cond
- sync/

## 安全并发
```go
package main

import (
	"fmt"
	"sync"
	"time"
)

func main() {
	var cond sync.Cond
	var wg sync.WaitGroup

	wg.Add(2)

	// 初始化 sync.Cond
	cond = *sync.NewCond(&sync.Mutex{})

	go func() {
		defer wg.Done()

		// 等待条件变量
		cond.L.Lock()
		cond.Wait()
		cond.L.Unlock()

		fmt.Println("Goroutine 1: Condition received")
	}()

	go func() {
		defer wg.Done()

		time.Sleep(2 * time.Second)

		// 发送信号通知其他协程
		cond.L.Lock()
		cond.Signal()
		cond.L.Unlock()

		fmt.Println("Goroutine 2: Condition sent")
	}()

	wg.Wait()
}

```
