---
title: "Goroute queue and schedule, how to play?"
date: 2024-01-05T16:01:23+08:00
lastmod: 2024-01-05T16:01:23+08:00
draft: true
tags: ["go","concurrent"]
categories: ["go"]
author: "yesplease"
---

# Go 协程队列与调度机制深度解析

## 引言：为什么需要理解 Go 的调度器？

Go 语言作为一门现代化的编程语言，其最引以为傲的特性之一就是原生支持高并发。而实现高并发的核心秘密，就在于其精心设计的 goroutine 调度系统。

想象一下，你的 Go 程序同时处理成千上万个并发任务，每个任务都是一个独立的 goroutine。操作系统线程（OS Thread）是昂贵的资源，创建和销毁都有很大的开销。如果每个 goroutine 都对应一个 OS 线程，那么系统的资源很快就会被耗尽。

Go 的调度器采用了一种称为 **M:N 模型** 的设计：M 个 goroutine 映射到 N 个 OS 线程上。这种设计使得我们可以在少量 OS 线程上运行大量 goroutine，从而实现高效的并发。

- **为什么 Go 调度器如此重要？**
  1. **资源效率**：避免了线程创建和销毁的开销
  2. **调度灵活**：用户态调度，不依赖操作系统
  3. **性能优化**：针对 Go 语言的特性进行了专门优化
  4. **并发友好**：天生适合 I/O 密集型和网络编程

- **调度器要解决的核心问题：**
  1. 如何公平地分配 CPU 时间给所有 goroutine？
  2. 如何避免某些 goroutine 饥饿？
  3. 如何处理 I/O 阻塞和计算密集型任务？
  4. 如何最大化 CPU 利用率？

本文将深入探讨 Go 调度器的内部机制，包括 GMP 模型、队列结构、调度算法，以及如何在实际编程中充分利用这些特性。

## Go 调度器的发展历程

Go 的调度器并非一蹴而就，而是经过了多次演进和优化：

### 1.0 时代的调度器

Go 1.0 之前的调度器相对简单，存在一些明显的问题：
- 单一全局锁，所有调度操作都需要获取全局锁
- 调度粒度较粗，性能不够理想
- 内存局部性较差，CPU 缓存命中率低

### 1.1 时代的调度器

Go 1.1 引入了基于工作的窃取调度器：
- 去掉了全局锁，采用分布式锁设计
- 引入了 P（Processor）的概念，每个 P 有自己的本地队列
- 实现了工作窃取算法，提高了负载均衡能力
- 减少了线程之间的竞争

### 现代调度器

当前版本的 Go 调度器在 1.1 的基础上进行了进一步优化：
- 更智能的调度策略
- 更好的内存局部性
- 更高效的垃圾回收配合
- 针对 NUMA 架构的优化

## GMP 模型详解

Go 调度器的核心是 **GMP 模型**，这三个字母分别代表：

### G - Goroutine

Goroutine 是 Go 语言中的并发执行单元，可以理解为轻量级的线程。

**G 的结构体简化表示：**
```go
type g struct {
    // 栈相关
    stack       stack      // 栈内存 [stack.lo, stack.hi)
    stackguard0 uintptr    // 栈保护，用于栈扩张检查

    // 调度相关
    sched       gobuf      // 调度信息，保存 goroutine 的执行上下文
    atomicstatus  uint32   // 原子状态
    goid        int64      // goroutine 唯一 ID
    schedlink   *g        // 用于链接到某个调度队列

    // 其他字段
    m           *m        // 当前绑定的 M
    ...
}
```

**关键特性：**
1. **轻量级**：初始栈大小只有 2KB，可以动态扩缩
2. **用户态**：创建和调度完全在用户空间完成
3. **非抢占式**：协作式调度，只有在特定时间点才会被调度
4. **可恢复**：通过 `gobuf` 保存执行上下文，可以随时暂停和恢复

### M - Machine

M 代表操作系统的线程，是真正的执行单元。

**M 的结构体简化表示：**
```go
type m struct {
    g0      *g     // g0 是调度用的 goroutine
    curg    *g     // 当前正在运行的 goroutine
    p       *p     // 当前绑定的 P
    nextp   *p     // 唤醒时绑定的 P
    id      int64  // M 的唯一 ID
    spinning bool  // 是否在寻找工作
    ...
}
```

**关键特性：**
1. **系统线程**：对应一个真实的 OS 线程
2. **调度核心**：负责执行 goroutine 的调度逻辑
3. **g0 特殊性**：每个 M 都有一个特殊的 g0，用于执行调度逻辑
4. **数量可变**：M 的数量可以根据负载动态调整

### P - Processor

P 是 Go 调度器的精髓，是逻辑处理器。

**P 的结构体简化表示：**
```go
type p struct {
    id          int32
    status      uint32    // P 的状态
    // 本地队列
    runqhead    uint32    // 本地队列头
    runqtail    uint32    // 本地队列尾
    runq        [256]guintptr  // 本地运行的 goroutine 队列
    // 运行时状态
    m           *m        // 当前绑定的 M
    mcache      *mcache   // 内存分配缓存
    // 全局队列相关
    runnext     guintptr  // 下一个要运行的 goroutine
    ...
}
```

**关键特性：**
1. **本地队列**：每个 P 有自己的本地 goroutine 队列（256 个槽位）
2. **内存缓存**：每个 P 有自己的内存分配器缓存
3. **数量固定**：P 的数量通常等于 CPU 核心数（可通过 GOMAXPROCS 调整）
4. **负载均衡**：通过工作窃取实现负载均衡

### GMP 三者关系


**关系说明：**
- P 的数量由 GOMAXPROCS 决定，通常等于 CPU 核心数
- M 的数量是动态的，可以大于 P 的数量
- G 的数量可以远大于 P 和 M 的数量
- 每个活跃的 M 都必须绑定一个 P 才能执行 G
- P 的本地队列存放待执行的 G，当本地队列为空时会从其他 P 窃取 G

## Goroutine 队列结构详解

Go 调度器的性能关键在于其精心设计的队列结构。队列是存储待执行 goroutine 的数据结构，Go 调度器采用了多层次的队列设计。

### 本地运行队列（Local Run Queue）

每个 P 都有一个本地运行队列，这是 Go 调度器的核心设计。

**队列结构：**
```go
type p struct {
    // 本地队列：环形缓冲区
    runqhead uint32        // 队列头指针
    runqtail uint32        // 队列尾指针
    runq     [256]guintptr  // 固定大小的数组，存储 goroutine 指针
    runnext  guintptr       // 下一个要运行的 goroutine（优先级最高）
}
```

**关键特性：**
1. **固定大小**：本地队列最多存储 256 个 goroutine
2. **环形缓冲区**：使用头尾指针实现高效的入队出队操作
3. **无锁设计**：每个 P 的本地队列只能被绑定的 M 访问，无需加锁
4. **CPU 缓存友好**：数据局部性好，提高 CPU 缓存命中率

**队列操作示意图：**
```
初始状态：
[0]   [1]   [2]   ...   [255]  <- runq 数组
 ↑                           ↑
runqhead = 0              runqtail = 0

入队3个goroutine后：
[G1]  [G2]  [G3]  ...   [255]
 ↑                    ↑
runqhead = 0        runqtail = 3

出队1个goroutine后：
[G1]  [G2]  [G3]  ...   [255]
       ↑            ↑
   runqhead = 1    runqtail = 3
```

### runnext 特殊处理

`runnext` 是一个特殊的字段，用于存储下一个要立即运行的 goroutine。

**为什么需要 runnext？**
1. **优先级最高**：比本地队列中的 goroutine 优先执行
2. **减少队列操作**：避免频繁的入队出队操作
3. **性能优化**：对于刚创建或刚被唤醒的 goroutine，直接设置 runnext

**使用场景：**
```go
// 当创建新的 goroutine 时
func newproc1(fn *funcval, argp *uint8, narg int32, callergp *g) {
    // ... 创建新 goroutine ...

    // 尝试将新 goroutine 放入 runnext
    if pp.runnext == 0 {
        pp.runnext.set(newg)
    } else {
        // 如果 runnext 已被占用，放入本地队列
        runqput(pp, newg, true)
    }
}
```

### 全局运行队列（Global Run Queue）

当所有 P 的本地队列都满了，或者需要全局调度时，goroutine 会被放入全局队列。

**全局队列结构：**
```go
var schedt struct {
    // 全局队列：链表结构
    runq     guintptr  // 全局队列头
    runqsize int32     // 全局队列大小
    // ... 其他字段
}
```

**关键特性：**
1. **链表结构**：可以存储任意数量的 goroutine
2. **全局锁保护**：访问全局队列需要获取全局锁
3. **负载均衡**：用于在不同 P 之间分配 goroutine
4. **后备存储**：当本地队列满时的后备方案

**全局队列与本地队列的关系：**
```
P1 本地队列: [G1, G2, G3] ←→ P2 本地队列: [G4, G5, G6]
                              ↓
                        全局队列: [G7, G8, G9, G10...]
                              ↑
P3 本地队列: [G11, G12] ←→ P4 本地队列: [G13, G14, G15]
```

### 等待队列（Wait Queue）

等待队列用于存储因某种原因（如 channel 操作、mutex 等）而阻塞的 goroutine。

**等待队列结构：**
```go
type sudog struct {
    g    *g          // 等待的 goroutine
    elem unsafe.Pointer  // 等待的数据元素（如 channel 数据）
    next *sudog      // 下一个等待的 goroutine
    prev *sudog      // 上一个等待的 goroutine
    // ... 其他字段
}
```

**使用场景：**
1. **Channel 操作**：发送/接收操作阻塞时
2. **Mutex 竞争**：多个 goroutine 竞争同一个锁
3. **网络 I/O**：等待网络数据到达
4. **定时器**：等待定时器到期

### 队列操作算法

#### 入队操作（runqput）

```go
// 将 goroutine 放入 P 的本地队列
func runqput(pp *p, gp *g, next bool) {
    if next {
        // 尝试放入 runnext
        retryNext:
        oldnext := pp.runnext
        if !pp.runnext.cas(oldnext, guintptr(unsafe.Pointer(gp))) {
            goto retryNext
        }
        if oldnext == 0 {
            return
        }
        // 如果 runnext 原本有 goroutine，将其放入本地队列
        gp = oldnext.ptr()
    }

    // 放入本地队列
    h := atomic.Load(&pp.runqhead) // load-acquire, synchronize with consumers
    t := pp.runqtail

    if t-h < uint32(len(pp.runq)) {
        // 队列未满，直接放入
        pp.runq[t%uint32(len(pp.runq))] = guintptr(unsafe.Pointer(gp))
        atomic.Store(&pp.runqtail, t+1) // store-release, makes goroutine available
        return
    }

    // 队列已满，放入全局队列
    runqputslow(pp, gp, h, t)
}
```

#### 出队操作（runqget）

```go
// 从 P 的本地队列获取 goroutine
func runqget(pp *p) *g {
    // 首先检查 runnext
    for {
        next := pp.runnext
        if next == 0 {
            break
        }
        if pp.runnext.cas(next, 0) {
            return next.ptr()
        }
    }

    // 检查本地队列
    for {
        h := atomic.Load(&pp.runqhead) // load-acquire, synchronize with other consumers
        t := pp.runqtail
        if h == t {
            return nil  // 队列为空
        }

        gp := pp.runq[h%uint32(len(pp.runq))].ptr()
        if atomic.Cas(&pp.runqhead, h, h+1) { // cas-release, commits consume
            return gp
        }
    }
}
```

#### 工作窃取（runqsteal）

```go
// 从其他 P 窃取 goroutine
func runqsteal(pp, p2 *p, stealRunNextG bool) *g {
    t := p2.runqtail
    n := t - p2.runqhead
    if n == 0 {
        if stealRunNextG {
            // 尝试窃取 runnext
            if next := p2.runnext; next != 0 {
                if p2.runnext.cas(next, 0) {
                    return next.ptr()
                }
            }
        }
        return nil
    }

    // 计算窃取数量：一半的 goroutine
    n = n/2 + n%2

    // 执行窃取操作
    h := atomic.Load(&p2.runqhead)
    if t-h < n {
        return nil
    }

    // 批量窃取 goroutine
    for i := uint32(0); i < n; i++ {
        gp := p2.runq[(h+i)%uint32(len(p2.runq))].ptr()
        runqput(pp, gp, false)
    }

    atomic.Store(&p2.runqhead, h+n)
    return gp
}
```

### 队列的性能优化

Go 调度器的队列设计充分考虑了性能优化：

**1. 无锁本地队列**
- 每个 P 的本地队列只能被绑定的 M 访问
- 避免了多线程竞争，提高性能

**2. 批量操作**
- 工作窃取时批量移动 goroutine
- 减少锁的获取和释放次数

**3. CPU 缓存友好**
- 固定大小的数组结构
- 数据局部性好，提高缓存命中率

**4. 负载均衡**
- 工作窃取算法确保负载均衡
- 防止某些 P 过于繁忙而其他 P 空闲

**5. 优先级处理**
- runnext 提供高优先级通道
- 新创建或刚唤醒的 goroutine 优先执行

## 调度策略与工作窃取机制

Go 调度器的智能之处在于其复杂的调度策略和工作窃取机制。这些机制确保了 goroutine 的高效执行和系统的负载均衡。

### 调度触发时机

Go 的调度是协作式的，只在特定的时间点才会触发调度。

#### 1. 函数调用前（prologue）

当 Go 函数被调用时，编译器会在函数开头插入检查代码：

```go
func someFunction() {
    // 编译器插入的调度检查
    if goroutinePreempt() {
        // 需要调度，让出 CPU
        gosched()
    }

    // 函数的实际逻辑
    // ...
}
```

#### 2. 函数调用后（epilogue）

函数返回时也会检查是否需要调度：

```go
func someFunction() {
    // 函数逻辑

    // 编译器插入的调度检查
    morestack()
}
```

#### 3. 系统调用阻塞

当 goroutine 执行系统调用时，会触发调度：

```go
func main() {
    go func() {
        // 网络请求会触发调度
        http.Get("https://example.com")
    }()

    // 当前 goroutine 可以继续执行
}
```

#### 4. Channel 操作

Channel 的发送和接收操作都可能触发调度：

```go
ch := make(chan int, 1)

// 发送操作可能阻塞，触发调度
ch <- 42

// 接收操作可能阻塞，触发调度
value := <-ch
```

#### 5. 内存分配

大块内存分配时可能触发调度：

```go
func allocateLargeMemory() {
    // 分配大块内存可能触发 GC，进而触发调度
    data := make([]byte, 100*1024*1024) // 100MB
    // ...
}
```

### 工作窃取算法详解

工作窃取是 Go 调度器的核心算法，用于实现负载均衡。

#### 工作窃取的触发条件

当 P 的本地队列为空时，会尝试从其他 P 窃取工作：

```go
func findrunnable() (gp *g) {
    // ... 其他逻辑

    // 本地队列为空，尝试工作窃取
    for i := 0; i < int(gomaxprocs); i++ {
        p2 := allp[pp.id+uint32(i)%uint32(gomaxprocs)]
        if gp := runqsteal(pp, p2, stealRunNextG); gp != nil {
            return gp
        }
    }

    // ... 继续寻找工作
}
```

#### 工作窃取的策略

**1. 随机选择目标**
```go
// 随机选择一个 P 进行窃取
p2 := allp[pp.id+uint32(i)%uint32(gomaxprocs)]
```

**2. 窃取一半的工作**
```go
// 计算窃取数量：一半的 goroutine
n := n/2 + n%2
```

**3. 批量移动**
```go
// 批量窃取 goroutine
for i := uint32(0); i < n; i++ {
    gp := p2.runq[(h+i)%uint32(len(p2.runq))].ptr()
    runqput(pp, gp, false)
}
```

#### 工作窃取的优势

1. **负载均衡**：自动平衡不同 P 的工作负载
2. **减少竞争**：避免了全局队列的竞争
3. **响应快速**：空闲的 P 可以快速获得工作
4. **扩展性好**：随着 CPU 核心数增加，性能线性提升

### 调度策略详解

Go 调度器采用了多种调度策略来优化性能：

#### 1. 时间片策略

每个 goroutine 有一个时间片，通常为 10ms 左右：

```go
const timeSlice = 10 * time.Millisecond

func execute(gp *g) {
    start := time.Now()

    for {
        // 执行 goroutine
        gp.fn()

        // 检查时间片是否用完
        if time.Since(start) >= timeSlice {
            gosched()
            break
        }
    }
}
```

#### 2. 优先级策略

不同状态的 goroutine 有不同的优先级：

```go
// goroutine 状态定义
const (
    _Gidle = iota
    _Grunnable
    _Grunning
    _Gsyscall
    _Gwaiting
    _Gmoribund_unused
    _Gdead
    _Genqueue_unused
    _Gcopystack
)

// 调度优先级
func schedule() {
    // 优先级顺序：runnext > 本地队列 > 全局队列 > 工作窃取
    if gp := pp.runnext.ptr(); gp != nil {
        return gp  // 最高优先级
    }

    if gp := runqget(pp); gp != nil {
        return gp  // 次高优先级
    }

    if gp := globrunqget(pp, 0); gp != nil {
        return gp  // 较低优先级
    }

    // 最后尝试工作窃取
    return findrunnable()
}
```

#### 3. CPU 亲和性策略

尽量让 goroutine 在同一个 P 上执行：

```go
func newproc1(fn *funcval, argp *uint8, narg int32, callergp *g) {
    // 尝试将新 goroutine 放入当前 P 的本地队列
    pp := getg().m.p.ptr()

    if pp.runnext == 0 {
        pp.runnext.set(newg)
    } else {
        runqput(pp, newg, true)
    }
}
```

#### 4. I/O 策略

I/O 操作会解绑 P，让其他 goroutine 使用：

```go
func entersyscall() {
    pp := getg().m.p.ptr()

    // 解绑 P
    pp.m = 0
    setm(nil)

    // 让其他 M 可以使用这个 P
    wakep()
}

func exitsyscall() {
    // 尝试重新绑定 P
    if !exitsyscallfast() {
        // 失败则放入全局队列
        exitsyscallslow()
    }
}
```

### 调度器的关键函数

#### schedule() 函数

这是调度的核心函数，决定下一个要执行的 goroutine：

```go
func schedule() {
    _g_ := getg()

    if _g_.m.locks != 0 {
        throw("schedule: holding locks")
    }

    // 调度循环
    for {
        gp := getg().m.p.ptr().runnext
        if gp.ptr() != nil {
            // 执行 runnext 中的 goroutine
            casgstatus(gp.ptr(), _Grunnable, _Grunning)
            execute(gp.ptr(), true)
            return
        }

        // 从本地队列获取
        gp, inheritTime := runqget(_g_.m.p.ptr())
        if gp != nil {
            casgstatus(gp, _Grunnable, _Grunning)
            execute(gp, inheritTime)
            return
        }

        // 从全局队列获取
        if gp := globrunqget(_g_.m.p.ptr(), 0); gp != nil {
            casgstatus(gp, _Grunnable, _Grunning)
            execute(gp, inheritTime)
            return
        }

        // 工作窃取
        if gp := findrunnable(); gp != nil {
            casgstatus(gp, _Grunnable, _Grunning)
            execute(gp, inheritTime)
            return
        }

        // 没有找到工作，停止当前 M
        stopm()
    }
}
```

#### findrunnable() 函数

寻找可运行的 goroutine：

```go
func findrunnable() (gp *g) {
    _g_ := getg()
    _g_.m.spinning = true  // 标记为正在寻找工作

    // 尝试从其他 P 窃取工作
    for i := 0; i < int(gomaxprocs); i++ {
        p2 := allp[_g_.m.p.ptr().id+uint32(i)%uint32(gomaxprocs)]
        if gp := runqsteal(_g_.m.p.ptr(), p2, stealRunNextG); gp != nil {
            return gp
        }
    }

    // 尝试从全局队列获取
    if gp := globrunqget(_g_.m.p.ptr(), 0); gp != nil {
        return gp
    }

    // 尝试从网络轮询器获取
    if netpollinited() && gp := netpoll(false); gp != nil {
        injectglist(gp)
        return gp
    }

    // 仍然没有工作，停止并休眠
    stopm()
    return nil
}
```

### 调度器的性能监控

Go 提供了多种方式监控调度器的性能：

#### 1. GODEBUG 环境变量

```bash
# 查看调度器详细信息
GODEBUG=scheddetail=1,schedtrace=1000 go run main.go

# 输出示例：
SCHED 1000ms: gomaxprocs=4 idleprocs=2 threads=5 spinningthreads=1 idlethreads=1 runqueue=0 gcwaiting=0 nmspinning=1
```

#### 2. runtime 包的调试函数

```go
package main

import (
    "fmt"
    "runtime"
    "time"
)

func main() {
    // 查看当前 Goroutine 数量
    fmt.Printf("NumGoroutine: %d\n", runtime.NumGoroutine())

    // 查看当前的 GOMAXPROCS
    fmt.Printf("GOMAXPROCS: %d\n", runtime.GOMAXPROCS(0))

    // 定期监控
    for i := 0; i < 10; i++ {
        fmt.Printf("[%d] Goroutines: %d, Cgo calls: %d\n",
            i, runtime.NumGoroutine(), runtime.NumCgoCall())
        time.Sleep(time.Second)
    }
}
```

#### 3. pprof 性能分析

```go
package main

import (
    "log"
    "net/http"
    _ "net/http/pprof"
)

func main() {
    go func() {
        log.Println(http.ListenAndServe("localhost:6060", nil))
    }()

    // 运行你的程序
    select {}
}
```

访问 `http://localhost:6060/debug/pprof/goroutine?debug=2` 可以查看详细的 goroutine 信息。

### 调度器的优化技巧

#### 1. 合理设置 GOMAXPROCS

```go
// 通常不需要设置，Go 会自动设置
// 但在某些情况下可以手动优化
runtime.GOMAXPROCS(runtime.NumCPU())
```

#### 2. 避免过多的 goroutine 创建

```go
// 不好的做法：为每个请求创建 goroutine
func badHandler(w http.ResponseWriter, r *http.Request) {
    go func() {
        // 处理请求
    }()
}

// 好的做法：使用 worker pool
type WorkerPool struct {
    jobs chan Job
    workers int
}

func (wp *WorkerPool) Start() {
    for i := 0; i < wp.workers; i++ {
        go wp.worker()
    }
}

func (wp *WorkerPool) worker() {
    for job := range wp.jobs {
        job.Process()
    }
}
```

#### 3. 避免在热路径上创建 goroutine

```go
// 不好的做法：在循环中创建 goroutine
for i := 0; i < 1000; i++ {
    go func(i int) {
        // 处理
    }(i)
}

// 好的做法：批量处理
func batchProcess(items []Item) {
    var wg sync.WaitGroup
    batchSize := 100

    for i := 0; i < len(items); i += batchSize {
        end := i + batchSize
        if end > len(items) {
            end = len(items)
        }

        wg.Add(1)
        go func(start, end int) {
            defer wg.Done()
            for j := start; j < end; j++ {
                process(items[j])
            }
        }(i, end)
    }

    wg.Wait()
}
```

