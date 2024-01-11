---
title: "Go Proverbs, how to play?"
date: 2024-01-01T16:01:23+08:00
lastmod: 2024-01-01T16:01:23+08:00
draft: false
tags: ["go","test"]
categories: ["go"]
author: "yesplease"
---

- Don't communicate by sharing memory, share memory by communicating.
```go
package main

import "fmt"

func main() {
    channel := make(chan int) // 创建一个通道

    go func() {
        value := 42
        channel <- value // 将值发送到通道
    }()

    receivedValue := <-channel // 从通道接收值
    fmt.Println(receivedValue) // 输出：42
}
```
- Concurrency is not parallelism
```go
package main

import (
    "fmt"
    "sync"
    "time"
)

func printNumbers(wg *sync.WaitGroup) {
    defer wg.Done()

    for i := 0; i < 5; i++ {
        fmt.Println(i)
        time.Sleep(100 * time.Millisecond)
    }
}

func printLetters(wg *sync.WaitGroup) {
    defer wg.Done()

    for i := 'a'; i < 'e'; i++ {
        fmt.Printf("%c\n", i)
        time.Sleep(100 * time.Millisecond)
    }
}

func main() {
    var wg sync.WaitGroup

    wg.Add(2)
    go printNumbers(&wg)
    go printLetters(&wg)

    wg.Wait()
}

```
- Channels orchestrate; mutexes serialize
```go
package main

import (
    "fmt"
    "sync"
)

func increment(counter *int, wg *sync.WaitGroup) {
    defer wg.Done()

    for i := 0; i < 1000; i++ {
        *counter++
    }
}

func main() {
    var wg sync.WaitGroup
    counter := 0

    wg.Add(2)
    go increment(&counter, &wg)
    go increment(&counter, &wg)

    wg.Wait()

    fmt.Println(counter) // 输出：2000
}

```
- The bigger the interface, the weaker the abstraction
```go
package main

import "fmt"

type Animal interface {
    Eat()
    Sleep()
}

type Dog struct{}

func (d Dog) Eat() {
    fmt.Println("Dog is eating")
}

func (d Dog) Sleep() {
    fmt.Println("Dog is sleeping")
}

type Cat struct{}

func (c Cat) Eat() {
    fmt.Println("Cat is eating")
}

func (c Cat) Sleep() {
    fmt.Println("Cat is sleeping")
}

func main() {
    animals := []Animal{Dog{}, Cat{}}

    for _, animal := range animals {
        animal.Eat()
        animal.Sleep()
    }
}

```
- Make the zero value useful
```go
package main

import "fmt"

type Person struct {
    Name string
    Age  int
}

func main() {
    var person Person
    fmt.Println(person.Name) // 输出空字符串
    fmt.Println(person.Age)  // 输出0

    person.Name = "Alice"
    person.Age = 30
    fmt.Println(person.Name) // 输出：Alice
    fmt.Println(person.Age)  // 输出：30
}

```
- Don't just check errors, handle them gracefully
```go
package main

import (
    "fmt"
    "os"
)

func main() {
    file, err := os.Open("example.txt")
    if err != nil {
        fmt.Println("Error opening file:", err)
        return
    }
    defer file.Close()

    // 在这里进行文件操作
    fmt.Println("File opened successfully")
}

```
- Don't panic
```go
package main

import "fmt"

func main() {
    defer func() {
        if r := recover(); r != nil {
            fmt.Println("Recovered from panic:", r)
        }
    }()

    panic("Something went wrong") // 引发恐慌
}

```