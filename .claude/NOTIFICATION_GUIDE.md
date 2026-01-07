# Claude对话系统通知功能指南

## 功能概述

这个功能可以在Claude Code对话需要用户输入时，通过系统通知提醒用户。当Claude等待你的回复时，会弹出Windows系统消息框进行提醒。

## 实现原理

1. **触发机制**: 使用Claude Code的hooks系统
   - `UserPromptSubmit` hook: 当用户提交问题后触发，发送"等待输入"通知
   - `PreToolUse` hook: 当Claude开始使用工具时触发，清除"等待输入"状态

2. **通知方式**: 使用Windows原生API
   - MessageBox弹窗
   - 声音提醒（备选）
   - 窗口闪烁（备选）

3. **状态管理**: 使用标志文件记录等待状态
   - `~/.claude_waiting_input`: 等待输入标志文件

## 文件结构

```
.claude/
├── windows_notify.py        # Windows通知主脚本
├── simple_notify.py         # 备用通知脚本（支持多种方式）
├── notify.py                # 完整通知脚本（跨平台）
├── settings.local.json      # Claude Code配置（已集成hooks）
└── NOTIFICATION_GUIDE.md    # 本指南
```

## 使用方法

### 1. 手动测试通知

```bash
# 发送测试通知
python .claude/windows_notify.py notify --title "测试标题" --message "测试消息"

# 模拟开始等待输入
python .claude/windows_notify.py start-wait

# 模拟结束等待输入
python .claude/windows_notify.py end-wait

# 检查等待状态
python .claude/windows_notify.py check
```

### 2. 自动工作流程

功能已通过hooks自动集成到Claude Code中：

1. **你提问后** → Claude处理问题 → 系统弹出通知"Claude对话等待输入"
2. **Claude开始工作**（使用工具）→ 清除等待状态
3. **Claude回复完成后** → 再次等待你的输入 → 再次弹出通知

## 配置详情

### hooks配置（settings.local.json）

```json
"hooks": {
  "UserPromptSubmit": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "python \"${PROJECT_ROOT}/.claude/windows_notify.py\" start-wait"
        }
      ]
    }
  ],
  "PreToolUse": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "python \"${PROJECT_ROOT}/.claude/windows_notify.py\" end-wait"
        }
      ]
    }
  ]
}
```

## 自定义设置

### 修改通知内容

编辑`.claude/windows_notify.py`中的默认值：

```python
def send_notification(title="Claude对话等待输入", message="请返回Claude界面继续对话"):
    # 修改这里的title和message默认值
```

### 调整hooks触发时机

在`settings.local.json`中修改hooks配置：

- `UserPromptSubmit`: 用户提交问题时触发
- `PreToolUse`: Claude使用工具前触发
- `PostToolUse`: Claude使用工具后触发
- `SessionStart`: 会话开始时触发
- `SessionEnd`: 会话结束时触发

## 故障排除

### 1. 通知不弹出
- 检查Python是否正确安装：`python --version`
- 检查脚本权限：确保可以执行Python脚本
- 检查hooks是否启用：确保`settings.local.json`配置正确

### 2. 通知频繁弹出
- 检查等待状态标志文件：`~/.claude_waiting_input`
- 手动清除状态：`python .claude/windows_notify.py end-wait`

### 3. 编码问题（显示乱码）
- 脚本已使用UTF-8编码
- 确保终端支持UTF-8显示

### 4. 备选方案
如果Windows MessageBox不工作，可以：
1. 使用备用脚本：`python .claude/simple_notify.py notify`
2. 安装win10toast库：`pip install win10toast`

## 技术细节

### windows_notify.py使用的Windows API

1. **MessageBoxW**: 显示系统消息框
2. **Beep**: 播放提示音
3. **FlashWindowEx**: 闪烁任务栏窗口
4. **GetConsoleWindow**: 获取控制台窗口句柄

### 状态管理机制

```python
# 创建等待标志
flag_file = Path.home() / '.claude_waiting_input'

# 检查等待状态
flag_file.exists()  # True表示正在等待输入
```

## 扩展功能

### 添加声音提醒
取消注释`windows_notify.py`中的Beep相关代码。

### 添加窗口闪烁
取消注释`windows_notify.py`中的FlashWindowEx相关代码。

### 支持其他操作系统
使用`notify.py`脚本，它支持Windows、Linux和macOS。

## 注意事项

1. **不要删除标志文件**: 系统依赖`~/.claude_waiting_input`文件管理状态
2. **hooks可能被拦截**: 某些安全软件可能阻止hooks执行
3. **会话恢复**: 如果Claude Code异常退出，可能需要手动清除等待状态
4. **多会话支持**: 当前实现支持单会话，多会话需要扩展状态管理

## 测试验证

已通过测试的功能：
- ✅ Windows MessageBox通知
- ✅ hooks自动触发
- ✅ 状态标志文件管理
- ✅ 编码正确处理

---

**最后更新**: 2026-01-06
**适用环境**: Windows + MINGW64 + Python 3.12+
**测试状态**: 功能正常，你已收到测试弹窗