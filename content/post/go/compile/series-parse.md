
# parse
cmd/compile/internal/syntax (lexer, parser, syntax tree)

## 一、lexer、parse
- token化
```go
type token uint

//go:generate stringer -type token -linecomment tokens.go

const (
  _    token = iota
  _EOF     
  ...
  )
```
其中有一句：
```go
// Make sure we have at most 64 tokens so we can use them in a set.
const _ uint64 = 1 << (tokenCount - 1)
```
该段代码的目的是确保我们最多只使用 64 个令牌（tokens），以便将它们作为位集合（bit set）使用。

常量 _ 被赋值为 1 << (tokenCount - 1)。这里 tokenCount 可能表示用于语法分析或其他操作的令牌数量。通过将 1 左移 tokenCount - 1 位，可以得到一个只有第 tokenCount - 1 位被设置为 1 的数值。

这个常量的作用是创建一个具有 64 位的位集合，其中只有第 tokenCount - 1 位被设置为 1，而其他位都为 0。这样的位集合可以用来进行位运算和标记操作，例如使用按位与（bitwise AND）将特定位设置为 1，或者使用按位或（bitwise OR）从标志位中提取信息。

通过控制令牌数目在 64 以内，并将其表示为位集合，在编写解析器或进行其他类型的符号处理时，可以更高效地使用位运算和存储空间。在这种情况下，使用 64 个位作为位集合的大小通常是一种经验性的限制，可以满足大多数常见的情况。

- 自上而下的递归下降（Top-Down Recursive-Descent）算法

>自上而下的递归下降算法是根据语法规则从上到下递归地构建语法树或执行语义动作的解析方法。它之所以称为“自上而下”，是因为从整个输入开始的最高级别的非终结符出发，逐步地向下展开和解析，直到达到终结符。

>这种算法的核心思想是先构建高层次的语法结构，然后根据具体的语法规则和当前的输入，递归地调用下一层次的解析函数。因此，解析过程自于起始符号的推导，从上到下逐步展开、深入解析，直到达到终结符。

>另一个方面，“递归下降”表示每个非终结符的解析函数内部可以递归地调用其他非终结符的解析函数。每个非终结符对应一个解析函数，这些解析函数按照相应的规则进行递归调用，从而实现对整个语法规则的逐个解析。
```go
package main

import (
	"fmt"
	"strconv"
	"strings"
)

var input string
var index int

func main() {
	input = "2 + 3 * (4 - 1)"
	index = 0

	result := expression()
	fmt.Println("解析结果：", result)
}

func expression() int {
	value := term()

	for index < len(input) && (input[index] == '+' || input[index] == '-') {
		operator := input[index]
		index++
		operand := term()

		if operator == '+' {
			value += operand
		} else {
			value -= operand
		}
	}

	return value
}

func term() int {
	value := factor()

	for index < len(input) && (input[index] == '*' || input[index] == '/') {
		operator := input[index]
		index++
		operand := factor()

		if operator == '*' {
			value *= operand
		} else {
			value /= operand
		}
	}

	return value
}

func factor() int {
	if input[index] == '(' {
		index++
		value := expression()

		if input[index] == ')' {
			index++
			return value
		} else {
			panic("语法错误：缺少右括号")
		}
	} else {
		start := index
		for index < len(input) && strings.ContainsRune("0123456789", rune(input[index])) {
			index++
		}
		number, err := strconv.Atoi(input[start:index])
		if err != nil {
			panic("语法错误：无效数字")
		}
		return number
	}
}

```

- 变量捕获

```go
go tool compile -m=2 main.go | grep capturing
```
- 逃逸分析
>Go 编译器在编译过程中会进行逃逸分析（Escape Analysis）来确定变量的生命周期和内存管理方式。逃逸分析的目标是尽可能地在栈上分配内存，减少对堆的使用，从而提高程序的性能和效率。



## 学习点
- 基于领域，定义一个赋予意义化的类型
- 领域内的常量初始化，利用iota
- 善于使用位标识，位运算

