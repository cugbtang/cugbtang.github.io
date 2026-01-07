#!/usr/bin/env python3
"""
系统通知工具 - 用于在Claude对话需要输入时提醒用户
支持跨平台通知（Windows/Linux/macOS）
"""

import os
import sys
import platform
import time
import subprocess
import json
from pathlib import Path

def get_platform():
    """获取当前操作系统平台"""
    system = platform.system().lower()
    if 'mingw' in system or 'cygwin' in system or 'windows' in system:
        return 'windows'
    return system

def send_windows_notification(title, message):
    """在Windows上发送系统通知"""
    try:
        # 使用win10toast库（如果已安装）
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(
            title=title,
            msg=message,
            duration=5,
            threaded=True
        )
        return True
    except ImportError:
        # 如果win10toast未安装，使用原生Windows API
        try:
            from win32api import MessageBox
            from win32con import MB_OK, MB_ICONINFORMATION
            MessageBox(0, message, title, MB_OK | MB_ICONINFORMATION)
            return True
        except ImportError:
            # 使用powershell创建通知
            try:
                ps_script = f'''
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

                $template = @"
                <toast>
                    <visual>
                        <binding template="ToastGeneric">
                            <text>{title}</text>
                            <text>{message}</text>
                        </binding>
                    </visual>
                </toast>
                "@

                $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
                $xml.LoadXml($template)
                $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Claude Code").Show($toast)
                '''
                subprocess.run(['powershell', '-Command', ps_script],
                             capture_output=True, timeout=5)
                return True
            except Exception as e:
                print(f"Windows通知失败: {e}")
                return False

def send_linux_notification(title, message):
    """在Linux上发送系统通知"""
    try:
        # 尝试使用notify-send命令
        subprocess.run(['notify-send', title, message],
                      capture_output=True, timeout=5)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        try:
            # 尝试使用dbus-send
            subprocess.run([
                'dbus-send',
                '--session',
                '--dest=org.freedesktop.Notifications',
                '--type=method_call',
                '/org/freedesktop/Notifications',
                'org.freedesktop.Notifications.Notify',
                'string:"Claude Code"',
                'uint32:0',
                'string:""',
                f'string:"{title}"',
                f'string:"{message}"',
                'array:string:',
                'dict:string:string:',
                'int32:5000'
            ], capture_output=True, timeout=5)
            return True
        except Exception as e:
            print(f"Linux通知失败: {e}")
            return False

def send_macos_notification(title, message):
    """在macOS上发送系统通知"""
    try:
        # 使用osascript发送通知
        script = f'''
        display notification "{message}" with title "{title}"
        '''
        subprocess.run(['osascript', '-e', script],
                      capture_output=True, timeout=5)
        return True
    except Exception as e:
        print(f"macOS通知失败: {e}")
        return False

def send_notification(title="Claude对话等待输入", message="请返回Claude界面继续对话"):
    """
    发送系统通知
    Args:
        title: 通知标题
        message: 通知消息内容
    Returns:
        bool: 是否成功发送通知
    """
    current_platform = get_platform()

    print(f"发送{current_platform}系统通知: {title} - {message}")

    if current_platform == 'windows':
        return send_windows_notification(title, message)
    elif current_platform == 'linux':
        return send_linux_notification(title, message)
    elif current_platform == 'darwin':  # macOS
        return send_macos_notification(title, message)
    else:
        print(f"不支持的操作系统: {current_platform}")
        return False

def monitor_claude_session(session_file=None, check_interval=30):
    """
    监控Claude会话状态，在需要输入时发送通知
    Args:
        session_file: Claude会话状态文件路径（可选）
        check_interval: 检查间隔（秒）
    """
    print(f"开始监控Claude会话，检查间隔: {check_interval}秒")

    # 默认会话状态文件位置
    if session_file is None:
        # 假设Claude Code将状态存储在临时文件中
        temp_dir = os.environ.get('TEMP', os.environ.get('TMP', '/tmp'))
        session_file = Path(temp_dir) / 'claude_session_status.json'

    last_notification_time = 0
    notification_cooldown = 300  # 5分钟内不重复通知

    try:
        while True:
            try:
                # 检查会话状态文件是否存在
                if session_file.exists():
                    with open(session_file, 'r') as f:
                        status = json.load(f)

                    # 检查是否等待用户输入
                    if status.get('waiting_for_input', False):
                        current_time = time.time()
                        if current_time - last_notification_time > notification_cooldown:
                            if send_notification():
                                last_notification_time = current_time
                                print(f"已发送通知 (等待输入)")
                            else:
                                print(f"通知发送失败")
                    else:
                        print(f"会话状态: 无需输入")
                else:
                    print(f"会话状态文件不存在: {session_file}")

            except (json.JSONDecodeError, IOError) as e:
                print(f"读取会话状态文件失败: {e}")

            time.sleep(check_interval)

    except KeyboardInterrupt:
        print("\n停止监控")

def create_session_status(waiting=True, message="等待用户输入"):
    """创建会话状态文件"""
    temp_dir = os.environ.get('TEMP', os.environ.get('TMP', '/tmp'))
    session_file = Path(temp_dir) / 'claude_session_status.json'

    status = {
        'waiting_for_input': waiting,
        'message': message,
        'timestamp': time.time()
    }

    try:
        with open(session_file, 'w') as f:
            json.dump(status, f, indent=2)
        print(f"已创建会话状态文件: {session_file}")
        return str(session_file)
    except Exception as e:
        print(f"创建会话状态文件失败: {e}")
        return None

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Claude对话系统通知工具')
    subparsers = parser.add_subparsers(dest='command', help='命令')

    # notify命令：直接发送通知
    notify_parser = subparsers.add_parser('notify', help='发送通知')
    notify_parser.add_argument('--title', default='Claude对话等待输入', help='通知标题')
    notify_parser.add_argument('--message', default='请返回Claude界面继续对话', help='通知消息')

    # monitor命令：监控模式
    monitor_parser = subparsers.add_parser('monitor', help='监控会话状态')
    monitor_parser.add_argument('--file', help='会话状态文件路径')
    monitor_parser.add_argument('--interval', type=int, default=30, help='检查间隔（秒）')

    # status命令：更新会话状态
    status_parser = subparsers.add_parser('status', help='更新会话状态')
    status_parser.add_argument('--waiting', type=bool, default=True, help='是否等待输入')
    status_parser.add_argument('--message', default='等待用户输入', help='状态消息')

    args = parser.parse_args()

    if args.command == 'notify':
        success = send_notification(args.title, args.message)
        sys.exit(0 if success else 1)
    elif args.command == 'monitor':
        monitor_claude_session(args.file, args.interval)
    elif args.command == 'status':
        create_session_status(args.waiting, args.message)
    else:
        # 默认行为：发送测试通知
        print("发送测试通知...")
        success = send_notification()
        sys.exit(0 if success else 1)