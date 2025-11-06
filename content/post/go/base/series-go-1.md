---
title: "Go fundamentals, how to play?"
date: 2024-01-02T16:01:23+08:00
lastmod: 2024-01-02T16:01:23+08:00
draft: false
tags: ["go","test"]
categories: ["go"]
author: "yesplease"
---

Go Fundamentals 是更多的Go基础知识，涵盖了数据结构（基础数据结构、数组、slice、map）、语言基础（函数、接口、反射）、关键字和并发等方面。掌握这些概念和技术将帮助您编写高效、可靠和复杂的Go程序。

### 数据结构
1. 数据类型（Data Types）：
   - Go语言有基本数据类型，包括布尔型、数字型、字符串和字符型。
   - 可以使用var关键字来声明变量，也可以使用:=运算符进行变量初始化和类型推断。

    ```go
    // 声明变量
    var age int
    var name string
    var isMarried bool

    // 初始化变量
    age = 30
    name = "Alice"
    isMarried = true

    // 自动类型推断
    age := 30
    name := "Alice"
    isMarried := true
    ```
2. 数组和切片（Arrays and Slices）：
   - Go语言有数组和切片两种类型，用于存储元素的序列。
   - 数组是固定长度的序列，可以通过索引来访问元素。
   - 切片是动态长度的序列，可以使用append函数来添加元素。

    ```go
    // 定义数组和切片
    numbers := [5]int{1, 2, 3, 4, 5}
    letters := []string{"A", "B", "C"}

    // 访问数组元素
    fmt.Println(numbers[0])
    fmt.Println(numbers[3])

    // 添加切片元素
    letters = append(letters, "D")
    fmt.Println(letters)
    ```

3. 映射（Maps）：
   - Go语言使用映射来存储键值对。
   - 可以使用make函数创建映射，使用[]运算符访问键值对。
   - 映射是无序的，但是可以使用range关键字迭代映射中的所有键值对。

    ```go
    // 创建映射
    ages := make(map[string]int)
    ages["Alice"] = 30
    ages["Bob"] = 25

    // 访问映射元素
    fmt.Println(ages["Alice"])
    fmt.Println(ages["Bob"])

    // 迭代映射
    for name, age := range ages {
        fmt.Println(name, age)
    }
    ```
### 语言基础
1. 控制结构（Control Structures）：
   - Go语言有if/else语句、for循环、switch语句等控制结构。
   - if/else语句可以嵌套，可以用来检查多个条件。
   - for循环可以用来迭代数组、切片和映射，也可以用来执行无限循环。
   - switch语句可以用来匹配多个表达式的值。

    ```go
    // if/else语句
    if age > 18 {
        fmt.Println("You are an adult")
    } else if age > 12 {
        fmt.Println("You are a teenager")
    } else {
        fmt.Println("You are a child")
    }

    // for循环
    for i := 0; i < 5; i++ {
        fmt.Println(i)
    }

    // 迭代数组
    numbers := []int{1, 2, 3, 4, 5}
    for _, number := range numbers {
        fmt.Println(number)
    }

    // switch语句
    switch age {
    case 0:
        fmt.Println("You are a baby")
    case 1, 2:
        fmt.Println("You are a toddler")
    case 3, 4, 5:
        fmt.Println("You are a preschooler")
    default:
        fmt.Println("You are not young anymore")
    }
    ```

2. 函数（Functions）：
   - Go语言使用函数作为基本的代码块。
   - 函数可以接受任意数量的参数，并且也可以返回多个值。
   - 可以使用匿名函数来创建闭包。

    ```go
    // 定义函数
    func add(a, b int) int {
        return a + b
    }

    // 调用函数
    sum := add(1, 2)
    fmt.Println(sum)

    // 返回多个值
    func divide(a, b float64) (float64, error) {
        if b == 0 {
            return 0, errors.New("Division by zero")
        }
        return a / b, nil
    }

    result, err := divide(10.0, 0.0)
    if err != nil {
        fmt.Println(err)
    } else {
        fmt.Println(result)
    }

    // 匿名函数和闭包
    func increase() func() int {
        i := 0
        return func() int {
            i += 1
            return i
        }
    }

    counter := increase()
    fmt.Println(counter()) // 1
    fmt.Println(counter()) // 2
    ```

3. 结构体（Structs）：
   - Go语言使用结构体来定义自定义类型。
   - 结构体由字段(field)组成，每个字段都有一个名称和类型。
   - 可以使用点操作符来访问结构体的字段。

    ```go
    // 定义结构体
    type Person struct {
        Name string
        Age  int
    }

    // 创建结构体实例
    person := Person{Name: "Alice", Age: 30}

    // 访问结构体字段
    fmt.Println(person.Name)
    fmt.Println(person.Age)
    ```

4. 指针（Pointers）：
   - Go语言具有指针类型，用于指向变量的内存地址。
   - 可以使用&运算符来获取变量的地址，使用*运算符来访问指针指向的值。

    ```go
    // 定义指针变量
    var agePointer *int

    // 获取变量的地址，并将地址赋值给指针变量
    age := 30
    agePointer = &age

    // 通过指针访问变量的值
    fmt.Println(*agePointer) // 输出30
    ```
5. 方法（Methods）：
   - Go语言中的方法是一种特殊类型的函数，它与结构体关联在一起。
   - 方法可以在结构体上定义，并且可以通过结构体的实例调用。

    ```go
    // 定义结构体
    type Rectangle struct {
        width  float64
        height float64
    }

    // 定义方法
    func (r Rectangle) Area() float64 {
        return r.width * r.height
    }

    // 创建结构体实例
    rectangle := Rectangle{width: 10, height: 5}

    // 调用方法
    area := rectangle.Area()
    fmt.Println(area)
    ```

6. 接口（Interfaces）：
    - 接口是一种抽象类型，它定义了一组方法的集合。
    - Go语言中的接口可以被任意类型实现，只要实现了接口中定义的方法即可。
    - 接口可以用来实现多态性，允许将不同类型的值赋给同一个接口类型的变量。

    ```go
    // 定义接口
    type Shape interface {
        Area() float64
    }

    // 实现接口
    type Rectangle struct {
        width  float64
        height float64
    }

    func (r Rectangle) Area() float64 {
        return r.width * r.height
    }

    // 创建接口类型的变量
    var shape Shape

    // 将结构体实例赋给接口变量
    shape = Rectangle{width: 10, height: 5}

    // 调用接口方法
    area := shape.Area()
    fmt.Println(area)
    ```

### 关键字
1. **select**：用于选择不同的通信操作。

    ```go
    c1 := make(chan int)
    c2 := make(chan string)

    go func() {
        time.Sleep(1 * time.Second)
        c1 <- 10
    }()

    go func() {
        time.Sleep(2 * time.Second)
        c2 <- "Hello"
    }()

    select {
    case i := <-c1:
        fmt.Println("Received from c1:", i)
    case s := <-c2:
        fmt.Println("Received from c2:", s)
    }
    ```

2. **panic**：用于抛出一个运行时异常。

    ```go
    func divide(a, b int) int {
        if b == 0 {
            panic("division by zero")
        }
        return a / b
    }

    func main() {
        defer func() {
            if r := recover(); r != nil {
                fmt.Println("Recovered from panic:", r)
            }
        }()

        result := divide(10, 0)
        fmt.Println("Result:", result)
    }
    ```

3. **recover**：用于恢复一个运行时异常。

    ```go
    func divide(a, b int) int {
        if b == 0 {
            panic("division by zero")
        }
        return a / b
    }

    func main() {
        defer func() {
            if r := recover(); r != nil {
                fmt.Println("Recovered from panic:", r)
            }
        }()

        result := divide(10, 0)
        fmt.Println("Result:", result)
    }
    ```

4. **make**：用于创建一个切片、映射或通道等引用类型的对象。

    ```go
    s := make([]int, 3)
    fmt.Println(s)

    m := make(map[string]int)
    m["one"] = 1
    m["two"] = 2
    fmt.Println(m)

    c := make(chan int, 1)
    c <- 10
    fmt.Println(<-c)
    ```

5. **new**：用于创建一个值类型的对象并返回其指针。

    ```go
    p := new(int)
    fmt.Println(*p)

    *p = 10
    fmt.Println(*p)
    ```

6. **defer**：用于延迟执行一个函数，通常用于释放资源或恢复状态等操作。

    ```go
    func main() {
        defer fmt.Println("This will be printed last")
        fmt.Println("This will be printed first")
    }
    ```

7. **switch**：用于基于不同条件执行不同的代码块。

    ```go
    day := "Monday"

    switch day {
    case "Monday":
        fmt.Println("Today is Monday")
    case "Tuesday":
        fmt.Println("Today is Tuesday")
    default:
        fmt.Println("Today is another day")
    }
    ```

8. **range**：用于遍历数组、切片、映射等数据结构。

    ```go
    numbers := []int{1, 2, 3, 4, 5}

    for index, value := range numbers {
        fmt.Println(index, value)
    }

    for key, value := range m {
        fmt.Println(key, value)
    }
    ```


### 并发

1. 并发（Concurrency）：
    - Go语言内置支持并发编程，使用goroutine和channel来实现。
    - goroutine是一种轻量级的线程，可以同时执行多个任务。
    - channel是用于goroutine之间通信的管道，可以发送和接收数据。

    ```go
    // 创建goroutine
    go func() {
        fmt.Println("Hello from goroutine!")
    }()

    // 创建有缓冲的channel
    ch := make(chan int, 1)

    // 发送和接收数据
    ch <- 10
    result := <- ch
    fmt.Println(result)
    ```



以上是Go Fundamentals的简要介绍和代码举例。这些基本概念是Go编程的核心，熟练掌握它们可以帮助您编写清晰、高效和可读性强的代码。