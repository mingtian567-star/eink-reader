#!/bin/bash
# 启动脚本

# 进入项目目录
cd "$(dirname "$0")"

# 检查是否在树莓派上运行
if [ ! -e "/proc/device-tree/model" ]; then
    echo "警告: 这不是树莓派系统，使用模拟模式"
    export SIMULATION_MODE=1
fi

# 检查是否以root运行
if [ "$EUID" -ne 0 ]; then 
    echo "请以root运行: sudo ./start.sh"
    echo "或以模拟模式运行: python3 main.py"
    exit 1
fi

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# 运行主程序
python3 main.py