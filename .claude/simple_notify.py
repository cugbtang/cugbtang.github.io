#!/usr/bin/env python3
"""
简单的Windows系统通知工具
适用于MINGW64环境
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def send_windows_notification_simple(title="Claude对话等待输入", message="请返回Claude界面继续对话"):
    """发送简单的Windows系统通知"""
    try:
        # 方法1: 使用powershell显示toast通知（Windows 8+）
        ps_script = f'''
        Add-Type -AssemblyName System.Windows.Forms
        $notification = New-Object System.Windows.Forms.NotifyIcon
        $notification.Icon = [System.Drawing.SystemIcons]::Information
        $notification.BalloonTipTitle = "{title}"
        $notification.BalloonTipText = "{message}"
        $notification.BalloonTipIcon = "Info"
        $notification.Visible = $true
        $notification.ShowBalloonTip(5000)
        Start-Sleep -Seconds 6
        $notification.Dispose()
        '''

        result = subprocess.run(
            ['powershell.exe', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=10,
            encoding='utf-8'
        )

        if result.returncode == 0:
            print(f"[OK] 系统通知已发送: {title}")
            return True
        else:
            print(f"[ERROR] PowerShell通知失败: {result.stderr}")

    except Exception as e:
        print(f"[ERROR] 通知发送异常: {e}")

    # 方法2: 备用方案 - 使用msg命令（需要用户登录到控制台会话）
    try:
        result = subprocess.run(
            ['msg', '*', f"{title}: {message}"],
            capture_output=True,
            text=True,
            timeout=5,
            encoding='utf-8'
        )
        if result.returncode == 0:
            print(f"[OK] 备用通知已发送")
            return True
    except Exception:
        pass

    # 方法3: 最后的手段 - 使用beep声音提醒
    print("[INFO] 使用声音提醒")
    try:
        # Windows beep
        import winsound
        winsound.Beep(1000, 500)  # 频率1000Hz，持续500ms
        winsound.Beep(1200, 500)
        return True
    except ImportError:
        # 控制台beep
        print("\a\a\a")  # 响铃字符
        return True

    return False

def create_waiting_flag():
    """创建等待输入标志文件"""
    flag_file = Path.home() / '.claude_waiting_input'
    try:
        with open(flag_file, 'w') as f:
            f.write(str(os.getpid()))
        print(f"[OK] 创建等待标志文件: {flag_file}")
        return True
    except Exception as e:
        print(f"[ERROR] 创建标志文件失败: {e}")
        return False

def clear_waiting_flag():
    """清除等待输入标志文件"""
    flag_file = Path.home() / '.claude_waiting_input'
    try:
        if flag_file.exists():
            flag_file.unlink()
            print(f"[OK] 清除等待标志文件")
        return True
    except Exception as e:
        print(f"[ERROR] 清除标志文件失败: {e}")
        return False

def is_waiting_input():
    """检查是否在等待输入"""
    flag_file = Path.home() / '.claude_waiting_input'
    return flag_file.exists()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Claude对话通知工具')
    parser.add_argument('action', choices=['notify', 'start-wait', 'end-wait', 'check'],
                       help='操作类型')
    parser.add_argument('--title', default='Claude对话等待输入',
                       help='通知标题')
    parser.add_argument('--message', default='请返回Claude界面继续对话',
                       help='通知消息')

    args = parser.parse_args()

    if args.action == 'notify':
        success = send_windows_notification_simple(args.title, args.message)
        sys.exit(0 if success else 1)

    elif args.action == 'start-wait':
        # 开始等待输入
        create_waiting_flag()
        send_windows_notification_simple(args.title, args.message)

    elif args.action == 'end-wait':
        # 结束等待输入
        clear_waiting_flag()
        print("[OK] 结束等待状态")

    elif args.action == 'check':
        # 检查等待状态
        if is_waiting_input():
            print("WAITING")
            sys.exit(0)
        else:
            print("NOT_WAITING")
            sys.exit(1)