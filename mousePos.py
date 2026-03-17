#!/usr/bin/env python3
"""获取或实时监控鼠标位置。支持交互式 Yes/No 引导。"""
import argparse
import sys
import time

import pyautogui

# 退出监控时重置终端光标
RESET_CURSOR = "\r\033[K\033[?25h\n"


def ask_yes_no(prompt: str, default_yes: bool = True) -> bool:
    """询问 Yes/No，默认 default_yes。空回车视为选默认。"""
    hint = "[Y/n]" if default_yes else "[y/N]"
    try:
        answer = input(f"{prompt} {hint}: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return default_yes
    if not answer:
        return default_yes
    return answer in ("y", "yes")


def run_watch(interval: float) -> None:
    """运行实时监控。"""
    try:
        while True:
            x, y = pyautogui.position()
            print(f"X={x}, Y={y}  (Ctrl+C 退出)", end="\r", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        sys.stdout.write(RESET_CURSOR)
        sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(
        description="获取/监控鼠标位置 (x, y)，支持交互式引导",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python mousePos.py           # 打印一次位置，并询问是否进入监控
  python mousePos.py -w       # 询问后进入监控模式
  python mousePos.py -y       # 仅打印位置，不询问
  python mousePos.py -w -y    # 直接进入监控，不询问
  python mousePos.py -h       # 显示帮助
        """,
    )
    parser.add_argument(
        "-w", "--watch",
        action="store_true",
        help="进入实时监控模式（会先询问确认，除非加 -y）",
    )
    parser.add_argument(
        "-i", "--interval",
        type=float,
        default=0.1,
        metavar="SEC",
        help="监控时的刷新间隔（秒），默认 0.1",
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        dest="no_prompt",
        help="跳过所有询问，直接执行（适合脚本调用）",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="不显示使用提示，只输出结果",
    )
    args = parser.parse_args()

    # 首次使用提示（未 -q 时）
    if not args.quiet:
        print("鼠标位置工具 (使用 -h 查看完整帮助)\n")

    # 先输出当前坐标
    x, y = pyautogui.position()
    print(f"当前鼠标位置: X={x}, Y={y}")

    if args.watch:
        if not args.no_prompt and not ask_yes_no("是否进入实时监控?", default_yes=True):
            print("已取消。")
            return
        if not args.quiet:
            print("监控中，按 Ctrl+C 退出。\n")
        run_watch(args.interval)
    else:
        if not args.no_prompt and ask_yes_no("是否进入实时监控?", default_yes=True):
            if not args.quiet:
                print("监控中，按 Ctrl+C 退出。\n")
            run_watch(args.interval)
        elif not args.no_prompt:
            print("如需监控可加参数: python mousePos.py -w")


if __name__ == "__main__":
    main()
