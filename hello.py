"""第一个仓库里的第一个程序。

目的不是写出厉害的东西，而是确认三件事都通了：
1. Python 能跑
2. git 能提交
3. GitHub 能看到
"""

import sys


def greet(name: str) -> str:
    return f"Hello, {name}! 你的第一个仓库已经跑起来了。"


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "lsy-cs"
    print(greet(name))


if __name__ == "__main__":
    main()
