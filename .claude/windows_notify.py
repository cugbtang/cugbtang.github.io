#!/usr/bin/env python3
"""
Windows系统通知工具 - 使用ctypes调用Windows API
适用于MINGW64环境
"""

import os
import sys
import ctypes
import ctypes.wintypes
from pathlib import Path

# Windows API常量
MB_OK = 0x00000000
MB_ICONINFORMATION = 0x00000040
MB_ICONWARNING = 0x00000030
MB_ICONERROR = 0x00000010

def send_windows_messagebox(title="Claude对话等待输入", message="请返回Claude界面继续对话"):
    """使用Windows MessageBox API显示通知"""
    try:
        result = ctypes.windll.user32.MessageBoxW(
            0,  # 无父窗口
            message,
            title,
            MB_OK | MB_ICONINFORMATION
        )
        return result > 0
    except Exception as e:
        print(f"[ERROR] MessageBox失败: {e}")
        return False

def send_windows_beep():
    """使用Windows Beep声音提醒"""
    try:
        ctypes.windll.kernel32.Beep(1000, 500)  # 频率1000Hz，持续500ms
        ctypes.windll.kernel32.Beep(1200, 500)  # 频率1200Hz，持续500ms
        return True
    except Exception as e:
        print(f"[ERROR] Beep失败: {e}")
        return False

def send_windows_flash_window():
    """闪烁任务栏窗口提醒"""
    try:
        # 获取控制台窗口句柄
        console_hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if console_hwnd:
            # 闪烁窗口
            FLASHW_STOP = 0
            FLASHW_CAPTION = 0x00000001
            FLASHW_TRAY = 0x00000002
            FLASHW_TIMERNOFG = 0x0000000C

            class FLASHWINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", ctypes.wintypes.UINT),
                    ("hwnd", ctypes.wintypes.HWND),
                    ("dwFlags", ctypes.wintypes.DWORD),
                    ("uCount", ctypes.wintypes.UINT),
                    ("dwTimeout", ctypes.wintypes.DWORD)
                ]

            flash_info = FLASHWINFO()
            flash_info.cbSize = ctypes.sizeof(FLASHWINFO)
            flash_info.hwnd = console_hwnd
            flash_info.dwFlags = FLASHW_CAPTION | FLASHW_TRAY
            flash_info.uCount = 5  # 闪烁5次
            flash_info.dwTimeout = 0  # 使用默认闪烁速率

            ctypes.windll.user32.FlashWindowEx(ctypes.byref(flash_info))
            return True
    except Exception as e:
        print(f"[ERROR] 窗口闪烁失败: {e}")
        return False

def send_notification(title="Claude对话等待输入", message="请返回Claude界面继续对话"):
    """
    发送Windows系统通知
    尝试多种方法直到成功
    """
    print(f"发送通知: {title}")

    # 方法1: MessageBox
    if send_windows_messagebox(title, message):
        print("[OK] MessageBox通知已发送")
        return True

    # 方法2: 声音提醒
    print("[INFO] 尝试声音提醒...")
    if send_windows_beep():
        print("[OK] 声音提醒已发送")
        return True

    # 方法3: 窗口闪烁
    print("[INFO] 尝试窗口闪烁...")
    if send_windows_flash_window():
        print("[OK] 窗口闪烁已激活")
        return True

    print("[ERROR] 所有通知方法都失败了")
    return False

def create_waiting_flag():
    """创建等待输入标志文件"""
    flag_file = Path.home() / '.claude_waiting_input'
    try:
        with open(flag_file, 'w', encoding='utf-8') as f:
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

    parser = argparse.ArgumentParser(description='Windows系统通知工具')
    parser.add_argument('action', choices=['notify', 'start-wait', 'end-wait', 'check'],
                       help='操作类型')
    parser.add_argument('--title', default='Claude对话等待输入',
                       help='通知标题')
    parser.add_argument('--message', default='请返回Claude界面继续对话',
                       help='通知消息')

    args = parser.parse_args()

    if args.action == 'notify':
        success = send_notification(args.title, args.message)
        sys.exit(0 if success else 1)

    elif args.action == 'start-wait':
        # 开始等待输入
        create_waiting_flag()
        send_notification(args.title, args.message)

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