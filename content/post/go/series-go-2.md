---
title: "Go test, how to play?"
date: 2024-01-04T16:01:23+08:00
lastmod: 2024-01-04T16:01:23+08:00
draft: false
tags: ["go","test"]
categories: ["go"]
author: "yesplease"
---

# go 测试

go test 后面接着的应该是一个包名
go test 可以生成覆盖率的profile文件，这个文件可以被go tool cover工具解析(go tool cover -func=cover.out/go tool cover -html=cover.out)


## 1、Go top-level test:
- 优点
    ```
    go test会将每个TestXxx放在单独的goroutine中执行，保持相互的隔离；
    某个TestXxx用例未过，通过Errorf，甚至是Fatalf输出错误结果，都不会影响到其他TestXxx的执行；
    某个TestXxx用例中的某个结果判断未过，如果通过Errorf输出错误结果，则该TestXxx会继续执行；
    不过，如果TestXxx使用的是Fatal/Fatalf，这会导致该TestXxx的执行在调用Fatal/Fatalf的位置立即结束，TestXxx函数体内的后续测试代码将不会得到执行；
    默认各个TestXxx按声明顺序逐一执行，即便它们是在各自的goroutine中执行的；
    通过go test -shuffle=on可以让各个TestXxx按随机次序执行，这样可以检测出各个TestXxx之间是否存在执行顺序的依赖，我们要避免在测试代码中出现这种依赖；
    通过“go test -run=正则式”的方式，可以选择执行某些TestXxx。
    各个TestXxx函数可以调用t.Parallel方法(即testing.T.Parallel方法)来将TestXxx加入到可并行执行的用例集合中，注意：加入到并行执行集合后，这些TestXxx的执行顺序就不确定了。
    ```
- 示例
    ```go
    // Go top-level test
    func Add(a, b int) int {
        return a + b
    }

    // 测试代码
    func TestAdd(t *testing.T) {
        got := Add(2, 3)
        if got != 5 {
            t.Errorf("Add(2, 3) got %d, want 5", got)
        }
    }

    func TestAddZero(t *testing.T) {
        got := Add(2, 0)
        if got != 2 {
            t.Errorf("Add(2, 0) got %d, want 2", got)
        }
    }

    func TestAddOppositeNum(t *testing.T) {
        got := Add(2, -2)
        if got != 0 {
            t.Errorf("Add(2, -2) got %d, want 0", got)
        }
    }
    ```

- Go最佳实践的表驱动(table-driven)测试

    ```go
        func TestAddWithTable(t *testing.T) {
            cases := []struct {
                name string
                a    int
                b    int
                r    int
            }{
                {"2+3", 2, 3, 5},
                {"2+0", 2, 0, 2},
                {"2+(-2)", 2, -2, 0},
                //... ...
            }

            for _, caze := range cases {
                got := Add(caze.a, caze.b)
                if got != caze.r {
                    t.Errorf("%s got %d, want %d", caze.name, got, caze.r)
                }
            }
        }
    ```
- 基于top-level test+表驱动的测试,可以满足大多数Gopher的常规单测需求,不足：
    ```
    表内的cases顺序执行，无法shuffle;
    表内所有cases在同一个goroutine中执行，隔离性差；
    如果使用fatal/fatalf，那么一旦某个case失败，后面的测试表项(cases)将不能得到执行；
    表内test case无法并行(parallel)执行；
    测试用例的组织只能平铺，不够灵活，无法建立起层次。
    ```

## 2、Go 1.7版本引入了subtest！
- 优点

    ```
    go subtest也会放在单独的goroutine中执行，保持相互的隔离；
    某个Subtest用例未过，通过Errorf，甚至是Fatalf输出错误结果，都不会影响到同一TestXxx下的其他Subtest的执行；
    某个Subtest中的某个结果判断未过，如果通过Errorf输出错误结果，则该Subtest会继续执行；
    不过，如果subtest使用的是Fatal/Fatalf，这会导致该subtest的执行在调用Fatal/Fatalf的位置立即结束，subtest函数体内的后续测试代码将不会得到执行；
    默认各个TestXxx下的subtest将按声明顺序逐一执行，即便它们是在各自的goroutine中执行的；
    到目前为止，subtest不支持shuffle方式的随机序执行；
    通过“go test -run=TestXxx/正则式[/...]”的方式，我们可以选择执行TestXxx下的某个或某些subtest；
    各个subtest可以调用t.Parallel方法(即testing.T.Parallel方法)来将subtest加入到可并行执行的用例集合中，注意：加入到并行执行集合后，这些subTest的执行顺序就不确定了。
    ```

    ```
    更细粒度的测试：通过将测试用例分成多个小测试函数，可以更容易地定位问题和调试。
    可读性更好：subtest可以让测试代码更加清晰和易于理解。
    更灵活的测试：subtest可以根据需要进行组合和排列，以满足不同的测试需求。
    更有层次的组织测试代码：通过subtest可以设计出更有层次的测试代码组织形式，更方便地共享资源和在某一组织层次上设置setup与teardown
    ```
- 示例
    ```go
    // subtest
    func TestAddWithSubtest(t *testing.T) {
        cases := []struct {
            name string
            a    int
            b    int
            r    int
        }{
            {"2+3", 2, 3, 5},
            {"2+0", 2, 0, 2},
            {"2+(-2)", 2, -2, 0},
            //... ...
        }

        for _, caze := range cases {
            t.Run(caze.name, func(t *testing.T) {
                t.Log("g:", curGoroutineID())
                got := Add(caze.a, caze.b)
                if got != caze.r {
                    t.Errorf("got %d, want %d", got, caze.r)
                }
            })
        }
    }

    func curGoroutineID() int {
        var buf [64]byte
        n := runtime.Stack(buf[:], false)
        id := ""
        for i := 6; i < n; i++ {
            if buf[i] == 0x20 {
                id = string(buf[6:i])
                break
            }
        }
        gid, _ := strconv.Atoi(id)
        return gid
    }

    ```

Go testing包没有引入testsuite(测试套件)或testcase(测试用例)的概念，只有Test和SubTest

## 3、testify

testify的suite包为我们提供了一种基于suite/case结构组织测试代码的方式




- assert/require（十分全面的测试断言包）
    ```

    // testify
    func TestAssert(t *testing.T) {
        // Equal断言
        assert.Equal(t, 4, Add(1, 3), "The result should be 4")

        sl1 := []int{1, 2, 3}
        sl2 := []int{1, 2, 3}
        sl3 := []int{2, 3, 4}
        assert.Equal(t, sl1, sl2, "sl1 should equal to sl2 ")

        p1 := &sl1
        p2 := &sl2
        assert.Equal(t, p1, p2, "the content which p1 point to should equal to which p2 point to")

        err := errors.New("demo error")
        assert.EqualError(t, err, "demo error")

        // assert.Exactly(t, int32(123), int64(123)) // failed! both type and value must be same

        // 布尔断言
        assert.True(t, 1+1 == 2, "1+1 == 2 should be true")
        assert.Contains(t, "Hello World", "World")
        assert.Contains(t, []string{"Hello", "World"}, "World")
        assert.Contains(t, map[string]string{"Hello": "World"}, "Hello")
        assert.ElementsMatch(t, []int{1, 3, 2, 3}, []int{1, 3, 3, 2})

        // 反向断言
        assert.NotEqual(t, 4, Add(2, 3), "The result should not be 4")
        assert.NotEqual(t, sl1, sl3, "sl1 should not equal to sl3 ")
        assert.False(t, 1+1 == 3, "1+1 == 3 should be false")
        assert.Never(t, func() bool { return false }, time.Second, 10*time.Millisecond) //1秒之内condition参数都不为true，每10毫秒检查一次
        assert.NotContains(t, "Hello World", "Go")
    }

    func TestAdd1(t *testing.T) {
        result := Add(1, 3)
        assert.Equal(t, 4, result, "The result should be 4")
        result = Add(2, 2)
        assert.Equal(t, 4, result, "The result should be 4")
        result = Add(2, 3)
        assert.Equal(t, 5, result, "The result should be 5")
        result = Add(0, 3)
        assert.Equal(t, 3, result, "The result should be 3")
        result = Add(-1, 1)
        assert.Equal(t, 0, result, "The result should be 0")
    }

    func TestAdd2(t *testing.T) {
        assert := assert.New(t)

        result := Add(1, 3)
        assert.Equal(4, result, "The result should be 4")
        result = Add(2, 2)
        assert.Equal(4, result, "The result should be 4")
        result = Add(2, 3)
        assert.Equal(5, result, "The result should be 5")
        result = Add(0, 3)
        assert.Equal(3, result, "The result should be 3")
        result = Add(-1, 1)
        assert.Equal(0, result, "The result should be 0")
    }
    ```

- suite（提供了一个类xUnit的Suite/Case的测试代码组织形式的实现方案）

    ```go

    type ExampleSuite struct {
        suite.Suite
        indent int
    }

    func (suite *ExampleSuite) indents() (result string) {
        for i := 0; i < suite.indent; i++ {
            result += "----"
        }
        return
    }

    func (suite *ExampleSuite) SetupSuite() {
        fmt.Println("Suite setup")
    }

    func (suite *ExampleSuite) TearDownSuite() {
        fmt.Println("Suite teardown")
    }

    func (suite *ExampleSuite) SetupTest() {
        suite.indent++
        fmt.Println(suite.indents(), "Test setup")
    }

    func (suite *ExampleSuite) TearDownTest() {
        fmt.Println(suite.indents(), "Test teardown")
        suite.indent--
    }

    func (suite *ExampleSuite) BeforeTest(suiteName, testName string) {
        suite.indent++
        fmt.Printf("%sBefore %s.%s\n", suite.indents(), suiteName, testName)
    }

    func (suite *ExampleSuite) AfterTest(suiteName, testName string) {
        fmt.Printf("%sAfter %s.%s\n", suite.indents(), suiteName, testName)
        suite.indent--
    }

    func (suite *ExampleSuite) SetupSubTest() {
        suite.indent++
        fmt.Println(suite.indents(), "SubTest setup")
    }

    func (suite *ExampleSuite) TearDownSubTest() {
        fmt.Println(suite.indents(), "SubTest teardown")
        suite.indent--
    }

    func (suite *ExampleSuite) TestCase1() {
        suite.indent++
        defer func() {
            fmt.Println(suite.indents(), "End TestCase1")
            suite.indent--
        }()

        fmt.Println(suite.indents(), "Begin TestCase1")

        suite.Run("case1-subtest1", func() {
            suite.indent++
            fmt.Println(suite.indents(), "Begin TestCase1.Subtest1")
            fmt.Println(suite.indents(), "End TestCase1.Subtest1")
            suite.indent--
        })
        suite.Run("case1-subtest2", func() {
            suite.indent++
            fmt.Println(suite.indents(), "Begin TestCase1.Subtest2")
            fmt.Println(suite.indents(), "End TestCase1.Subtest2")
            suite.indent--
        })
    }

    func (suite *ExampleSuite) TestCase2() {
        suite.indent++
        defer func() {
            fmt.Println(suite.indents(), "End TestCase2")
            suite.indent--
        }()
        fmt.Println(suite.indents(), "Begin TestCase2")

        suite.Run("case2-subtest1", func() {
            suite.indent++
            fmt.Println(suite.indents(), "Begin TestCase2.Subtest1")
            fmt.Println(suite.indents(), "End TestCase2.Subtest1")
            suite.indent--
        })
    }

    func TestExampleSuite(t *testing.T) {
        suite.Run(t, new(ExampleSuite))
    }
    ```
- mock（不建议用mock。 但结合mockery工具和testify mock，我们可以针对接口为被测目标自动生成testify的mock部分代码，这会大大提交mock test的编写效率）
    ```go

    // mock
    type User struct {
        ID   int
        Name string
        Age  int
    }

    type UserRepository interface {
        CreateUser(user *User) (int, error)
        GetUserById(id int) (*User, error)
    }

    type UserService struct {
        repo UserRepository
    }

    func NewUserService(repo UserRepository) *UserService {
        return &UserService{repo: repo}
    }

    func (s *UserService) CreateUser(name string, age int) (*User, error) {
        user := &User{Name: name, Age: age}
        id, err := s.repo.CreateUser(user)
        if err != nil {
            return nil, err
        }
        user.ID = id
        return user, nil
    }

    func (s *UserService) GetUserById(id int) (*User, error) {
        return s.repo.GetUserById(id)
    }

    type UserRepositoryMock struct {
        mock.Mock
    }

    func (m *UserRepositoryMock) CreateUser(user *User) (int, error) {
        args := m.Called(user)
        return args.Int(0), args.Error(1)
    }

    func (m *UserRepositoryMock) GetUserById(id int) (*User, error) {
        args := m.Called(id)
        return args.Get(0).(*User), args.Error(1)
    }

    func TestUserService_CreateUser(t *testing.T) {
        repo := new(UserRepositoryMock)
        service := NewUserService(repo)

        user := &User{Name: "Alice", Age: 30}
        repo.On("CreateUser", user).Return(1, nil)

        createdUser, err := service.CreateUser(user.Name, user.Age)

        assert.NoError(t, err)
        assert.Equal(t, 1, createdUser.ID)
        assert.Equal(t, "Alice", createdUser.Name)
        assert.Equal(t, 30, createdUser.Age)

        repo.AssertExpectations(t)
    }
    ```
## 4、Test Double(尽量使用fake object，而不是mock object)

fake object也是Go testing中最为常用的一类（fake object最容易理解，它是被测系统SUT(System Under Test)依赖的外部协作者的“替身”）
```
以Go的标准库为例，我们在src/database/sql
Go标准库中还有net/dnsclient_unix_test.go中的fakeDNSServer
```
stub可以理解为一种fake object的特例。(一个内置了预期值/响应值且可以在多个测试间复用的替身object)
```
Go标准库中的net/http/httptest就是一个提供创建stub的典型的测试辅助包
httptest还常用来做http.Handler的测试
```

fake建立困难但使用简单。而mock object则是一种建立简单，使用简单程度因被测目标与外部协作者交互复杂程度而异的test double

mock object要与接口类型联合使用
```
我们与fake object的交互方式与与真实外部协作者交互的方式相同，这让其显得更简单，更容易使用，也降低了测试的复杂性；
fake objet的行为更像真正的协作者，可以给开发人员更多的信心；
当真实协作者更新时，我们不需要更新使用fake object时设置的expection和结果验证条件，因此，使用fake object时，重构代码往往比使用其他test double更容易。

fake object的创建和维护可能很费时，就像上面的fakeDriver，源码有近2k行；
fake object可能无法提供与真实组件相同的功能覆盖水平，这与fake object的提供方式有关。
fake object的实现需要维护，每当真正的协作者更新时，都必须更新fake object。
```

借助类似ChatGPT/copilot的工具快速构建出一个fake object


如果要更高的可信度和更高的功能覆盖水平，我们还可以借助docker来构建“真实版/无阉割版”的fake object。
借助github上开源的testcontainers-go可以更为简便的构建出一个fake object，并且testcontainer提供了常见的外部协作者的封装实现，比如：MySQL、Redis、Postgres等。
testcontainer更多也会被用在集成测试或冒烟测试上

## 5、竞争检测(race detection)
```
$ go test -race mypkg    // to test the package
$ go run -race mysrc.go  // to run the source file
$ go build -race mycmd   // to build the command
$ go install -race mypkg // to install the package
```

## 6、fuzz
The unit test has limitations, namely that each input must be added to the test by the developer. One benefit of fuzzing is that it comes up with inputs for your code, and may identify edge cases that the test cases you came up with didn’t reach.
```go
//reverse.go
package main

import (
	"fmt"
)

func main() {
    input := "The quick brown fox jumped over the lazy dog"
    rev := Reverse(input)
    doubleRev := Reverse(rev)
    fmt.Printf("original: %q\n", input)
    fmt.Printf("reversed: %q\n", rev)
    fmt.Printf("reversed again: %q\n", doubleRev)
}

func Reverse(s string) (string) {

	r := []rune(s)
	for i, j := 0, len(r)-1; i < len(r)/2; i, j = i+1, j-1 {
		r[i], r[j] = r[j], r[i]
	}
	return string(r)
}

//reverse_test.go
package main

import (
    "testing"
    "unicode/utf8"
)

func TestReverse(t *testing.T) {
    testcases := []struct {
        in, want string
    }{
        {"Hello, world", "dlrow ,olleH"},
        {" ", " "},
        {"!12345", "54321!"},
    }
    for _, tc := range testcases {
        rev := Reverse(tc.in)
        if rev != tc.want {
                t.Errorf("Reverse: %q, want %q", rev, tc.want)
        }
    }
}

func FuzzReverse(f *testing.F) {
    testcases := []string{"Hello, world", " ", "!12345"}
    for _, tc := range testcases {
        f.Add(tc)  // Use f.Add to provide a seed corpus
    }
    f.Fuzz(func(t *testing.T, orig string) {
        rev := Reverse(orig)
        doubleRev := Reverse(rev)
		t.Logf("Number of runes: orig=%d, rev=%d, doubleRev=%d", utf8.RuneCountInString(orig), utf8.RuneCountInString(rev), utf8.RuneCountInString(doubleRev))
		if orig != doubleRev {
			t.Errorf("Before: %q, after: %q", orig, doubleRev)
		}
		if utf8.ValidString(orig) && !utf8.ValidString(rev) {
			t.Errorf("Reverse produced invalid UTF-8 string %q", rev)
		}
    })
}
```
## 6、使用场景
net/http/httptest包提供了许多帮助函数，用于测试那些发送或处理Http请求的代码。


## 引用
- [单测时尽量用fake object](https://tonybai.com/2023/04/20/provide-fake-object-for-external-collaborators/)
- [fuzz](https://go.dev/doc/tutorial/fuzz)