---
title: "Go Effective, how to play?"
date: 2024-01-03T16:01:23+08:00
lastmod: 2024-01-03T16:01:23+08:00
draft: false
tags: ["go","test"]
categories: ["go"]
author: "yesplease"
---

## 1、介绍
Effective Go是Go语言官方提供的一份指南，旨在帮助开发人员写出高效、清晰和可读性强的Go代码。下面我会针对每个观点进行阐述，并给出相应的代码示例。
## 2、目的
使Go成为最佳的大规模软件工程环境
## 3、实践

1. Names（命名）：
   - Go语言推荐使用短小的名称，且遵循驼峰命名法。
   - 使用具有描述性的名称，避免使用缩写或简写。
   - 避免使用下划线来命名变量、函数或方法。
   - 对于包级别的变量，使用首字母大写来表示该变量是可导出的。

    ```go
    // Good example
    package main

    import "fmt"

    func main() {
        message := "Hello, World!"
        fmt.Println(message)
    }
    ```

2. Defer（延迟执行）：
   - 使用defer关键字可以确保某个函数在当前函数返回之前被执行。
   - 延迟执行的函数参数会在defer语句被执行时求值，并保存起来，直到包含它的函数返回之前才会被调用。

    ```go
    // Good example
    package main

    import "fmt"

    func main() {
        defer fmt.Println("World!")
        fmt.Print("Hello, ")
    }
    ```

3. Initialization（初始化）：
   - 尽量在变量声明时进行初始化。
   - 对于结构体类型，可以使用结构体字面量进行初始化。
   - 初始化可能发生在包级别、函数级别或代码块级别。

    ```go
    // Good example
    package main

    import "fmt"

    func main() {
        var name string = "Alice"
        age := 30

        person := struct {
            Name string
            Age  int
        }{
            Name: name,
            Age:  age,
        }

        fmt.Println(person)
    }
    ```

4. Methods（方法）：
   - 在Go中，方法是特定类型的函数。
   - 可以给自定义类型定义方法。
   - 使用接收者(receiver)来将函数与类型关联。

    ```go
    // Good example
    package main

    import "fmt"

    type Rectangle struct {
        Width  float64
        Height float64
    }

    func (r Rectangle) Area() float64 {
        return r.Width * r.Height
    }

    func main() {
        rect := Rectangle{Width: 10, Height: 5}
        area := rect.Area()
        fmt.Println("Area:", area)
    }
    ```

5. Interfaces（接口）：
   - 接口是一种抽象类型，用于定义对象的行为。
   - Go语言使用隐式实现，即无需显式声明实现某个接口。
   - 接口可以嵌套在其他接口中。

    ```go
    // Good example
    package main

    import "fmt"

    type Shape interface {
        Area() float64
    }

    type Rectangle struct {
        Width  float64
        Height float64
    }

    func (r Rectangle) Area() float64 {
        return r.Width * r.Height
    }

    func PrintArea(s Shape) {
        fmt.Println("Area:", s.Area())
    }

    func main() {
        rect := Rectangle{Width: 10, Height: 5}
        PrintArea(rect)
    }
    ```

6. Errors（错误处理）：
   - Go语言使用返回值来表示函数的执行状态。
   - 函数可以返回一个error类型的值，用于指示发生的错误。
   - 使用错误的工厂函数来创建错误，并提供清晰的错误消息。

    ```go
    // Good example
    package main

    import (
        "errors"
        "fmt"
    )

    func Divide(a, b float64) (float64, error) {
        if b == 0 {
            return 0, errors.New("division by zero")
        }
        return a / b, nil
    }

    func main() {
        result, err := Divide(10, 0)
        if err != nil {
            fmt.Println("Error:", err)
            return
        }
        fmt.Println("Result:", result)
    }
    ```

7. Concurrency（并发）：
   - Go语言提供了轻量级的协程(goroutine)来实现并发编程。
   - 使用goroutine和通道(channel)来协调不同协程之间的通信。
   - 使用select语句可以在多个通道上等待事件。
   - 并发控制的利器：golang.org/x/sync/errgroup

    ```go
    // Good example
    package main

    import (
        "fmt"
        "time"
    )

    func printNumbers() {
        for i := 0; i < 5; i++ {
            time.Sleep(500 * time.Millisecond)
            fmt.Println(i)
        }
    }

    func printLetters() {
        letters := []string{"A", "B", "C", "D", "E"}
        for _, letter := range letters {
            time.Sleep(500 * time.Millisecond)
            fmt.Println(letter)
        }
    }

    func main() {
        go printNumbers()
        go printLetters()

        time.Sleep(3 * time.Second)
    }
    ```

8. Embedding（嵌入）：
   - 在Go中，结构体可以通过嵌入其他类型来继承其字段和方法。
   - 嵌入的类型可以使用点操作符直接访问其字段和方法。

    ```go
    // Good example
    package main

    import "fmt"

    type Person struct {
        Name string
        Age  int
    }

    type Employee struct {
        Person
        Salary float64
    }

    func main() {
        emp := Employee{
            Person: Person{Name: "Alice", Age: 30},
            Salary: 5000,
        }

        fmt.Println("Name:", emp.Name)
        fmt.Println("Age:", emp.Age)
        fmt.Println("Salary:", emp.Salary)
    }
 
    ```

9、develop modules
- test
- profile
