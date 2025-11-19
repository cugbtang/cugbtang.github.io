# Skill创建帮助文档

## 概述

Claude Skills 是Claude Code的扩展功能，允许用户创建自定义工具来处理特定任务。本文档提供了最简单的Claude Skill创建步骤。

## 前置要求

- Claude Code环境已配置
- 对JSON和YAML配置文件有基本了解
- 了解基本的编程概念（Python/JavaScript等）

## 最简创建步骤

### 步骤1: 创建Skill配置文件

在项目根目录创建 `.claude/skills/` 目录结构：

```bash
mkdir -p .claude/skills
```

创建技能配置文件 `my-skill.yaml`：

```yaml
name: my-skill
description: "我的自定义技能"
version: "1.0.0"
author: "Your Name"
commands:
  - name: hello
    description: "输出问候语"
    pattern: "^hello\\s+(.+)$"
    handler: "hello_handler"
```

### 步骤2: 创建技能处理程序

在同一目录下创建Python处理程序 `my-skill.py`：

```python
import json
import sys

def hello_handler(args):
    """
    处理hello命令
    Args:
        args (list): 命令行参数列表
    Returns:
        dict: 处理结果
    """
    if len(args) > 0:
        name = args[0]
        return {
            "status": "success",
            "message": f"你好, {name}!"
        }
    else:
        return {
            "status": "error",
            "message": "请提供你的名字"
        }

def main():
    """主函数，处理命令行输入"""
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "缺少命令参数"}))
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else []

    if command == "hello":
        result = hello_handler(args)
    else:
        result = {"status": "error", "message": f"未知命令: {command}"}

    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

### 步骤3: 注册技能

在项目根目录创建或编辑 `.claude/config.json`：

```json
{
  "skills": [
    {
      "name": "my-skill",
      "path": ".claude/skills/my-skill.yaml",
      "enabled": true
    }
  ]
}
```

### 步骤4: 测试技能

重启Claude Code，然后测试你的技能：

```bash
# 在Claude Code中使用
/hello world
```

或者直接运行脚本测试：

```bash
python .claude/skills/my-skill.py hello world
```

## 进阶配置

### 添加更多命令

在 `my-skill.yaml` 中添加更多命令：

```yaml
commands:
  - name: hello
    description: "输出问候语"
    pattern: "^hello\\s+(.+)$"
    handler: "hello_handler"
  - name: calculate
    description: "执行简单计算"
    pattern: "^calc\\s+(\\d+)\\s*([+\\-*/])\\s*(\\d+)$"
    handler: "calculate_handler"
```

在Python文件中添加对应的处理函数：

```python
def calculate_handler(args):
    """处理计算命令"""
    if len(args) != 3:
        return {"status": "error", "message": "格式: calc 数字1 运算符 数字2"}

    try:
        num1 = float(args[0])
        operator = args[1]
        num2 = float(args[2])

        if operator == '+':
            result = num1 + num2
        elif operator == '-':
            result = num1 - num2
        elif operator == '*':
            result = num1 * num2
        elif operator == '/':
            result = num1 / num2 if num2 != 0 else "错误：除零"
        else:
            return {"status": "error", "message": "不支持的操作符"}

        return {
            "status": "success",
            "result": f"{num1} {operator} {num2} = {result}"
        }
    except ValueError:
        return {"status": "error", "message": "请输入有效的数字"}
```

### 添加依赖管理

创建 `requirements.txt` 文件：

```
requests==2.31.0
pyyaml==6.0
```

更新配置文件以支持依赖：

```yaml
name: my-skill
description: "我的自定义技能"
version: "1.0.0"
author: "Your Name"
dependencies:
  - requirements.txt
commands:
  - name: hello
    description: "输出问候语"
    pattern: "^hello\\s+(.+)$"
    handler: "hello_handler"
```

## 调试技巧

### 1. 查看技能状态

```bash
# 检查技能是否正确加载
.claude/skills/my-skill.py status
```

### 2. 启用详细日志

在 `.claude/config.json` 中添加：

```json
{
  "skills": [
    {
      "name": "my-skill",
      "path": ".claude/skills/my-skill.yaml",
      "enabled": true,
      "debug": true
    }
  ],
  "logging": {
    "level": "debug"
  }
}
```

### 3. 测试正则表达式

```python
import re

pattern = r"^hello\s+(.+)$"
test_input = "hello world"
match = re.match(pattern, test_input)
print(match.groups())  # 应该输出: ('world',)
```

## 常见问题

### Q: 技能无法加载
**A:** 检查以下几点：
- 配置文件路径是否正确
- YAML/JSON格式是否有效
- Python脚本是否有语法错误
- 依赖是否正确安装

### Q: 正则表达式不匹配
**A:** 使用在线正则表达式测试工具验证你的模式，确保转义字符正确。

### Q: 权限问题
**A:** 确保Python脚本有执行权限：
```bash
chmod +x .claude/skills/my-skill.py
```

## 示例项目

### 文件结构
```
my-project/
├── .claude/
│   ├── config.json
│   └── skills/
│       ├── my-skill.yaml
│       ├── my-skill.py
│       └── requirements.txt
└── 其他项目文件...
```

### 完整示例

**my-skill.yaml**
```yaml
name: example-skill
description: "示例技能，包含问候和计算功能"
version: "1.0.0"
author: "Example Author"
dependencies:
  - requirements.txt
commands:
  - name: hello
    description: "输出个性化问候语"
    pattern: "^hello\\s+(.+)$"
    handler: "hello_handler"
  - name: calc
    description: "执行基本数学运算"
    pattern: "^calc\\s+(\\d+)\\s*([+\\-*/])\\s*(\\d+)$"
    handler: "calculate_handler"
  - name: time
    description: "显示当前时间"
    pattern: "^time$"
    handler: "time_handler"
```

**my-skill.py**
```python
import json
import sys
from datetime import datetime

def hello_handler(args):
    """处理问候命令"""
    if args:
        return {"status": "success", "message": f"你好, {args[0]}! 欢迎使用Claude Skills."}
    return {"status": "error", "message": "请提供你的名字"}

def calculate_handler(args):
    """处理计算命令"""
    if len(args) != 3:
        return {"status": "error", "message": "用法: calc 数字1 运算符 数字2"}

    try:
        num1, op, num2 = float(args[0]), args[1], float(args[2])

        operations = {
            '+': lambda a, b: a + b,
            '-': lambda a, b: a - b,
            '*': lambda a, b: a * b,
            '/': lambda a, b: a / b if b != 0 else None
        }

        if op not in operations:
            return {"status": "error", "message": f"不支持的操作符: {op}"}

        if op == '/' and num2 == 0:
            return {"status": "error", "message": "错误：除零"}

        result = operations[op](num1, num2)
        return {"status": "success", "result": f"{num1} {op} {num2} = {result}"}

    except ValueError:
        return {"status": "error", "message": "请输入有效的数字"}

def time_handler(args):
    """处理时间命令"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"status": "success", "current_time": current_time}

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "缺少命令"}))
        return

    command = sys.argv[1]
    args = sys.argv[2:]

    handlers = {
        'hello': hello_handler,
        'calc': calculate_handler,
        'time': time_handler
    }

    if command in handlers:
        result = handlers[command](args)
    else:
        result = {"status": "error", "message": f"未知命令: {command}"}

    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

## 总结

创建Claude Skill的基本步骤：
1. 创建 `.claude/skills/` 目录
2. 编写YAML配置文件定义技能
3. 实现Python处理程序
4. 在配置文件中注册技能
5. 测试并调试

通过以上步骤，你可以快速创建功能丰富的Claude Skills来扩展Claude Code的能力。