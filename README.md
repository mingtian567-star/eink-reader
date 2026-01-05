# 水墨屏阅读器 (E-Ink Reader)

基于树莓派和电子墨水屏的定制化阅读器，支持多种书籍格式和个性化功能。

## 功能特性

- 📖 支持 TXT、EPUB、PDF 格式
- 🎨 自定义字体、字号、行距
- 🔄 物理按键控制（翻页、主页、菜单）
- 🔋 电池管理系统
- 📶 Wi-Fi 传书功能
- 🎵 文本转语音朗读
- 🌙 自动亮度调节
- 💾 阅读进度自动保存

## 硬件要求

1. 树莓派 4B (2GB/4GB/8GB)
2. Waveshare 7.5英寸电子墨水屏
3. 5V/3A 电源适配器
4. 16GB+ TF卡
5. 物理按键 x4
6. 杜邦线若干

## 快速开始

### 1. 系统安装
bash
烧录 Raspberry Pi OS
启用 SSH 和 SPI
### 2. 安装依赖
bash
sudo apt update
sudo apt install python3-pip python3-venv
sudo apt install fonts-wqy-microhei
### 3. 安装项目
bash
git clone https://github.com/yourusername/eink-reader.git
cd eink-reader
创建虚拟环境
python3 -m venv venv
source venv/bin/activate
安装依赖
pip install -r requirements.txt
### 4. 安装屏幕驱动
bash
cd ~
git clone https://github.com/waveshare/e-Paper.git
cd e-Paper/RaspberryPi_JetsonNano/python
sudo python3 setup.py install
### 5. 运行程序
bash
cd ~/eink-reader
sudo python3 main.py
## 系统服务

### 开机自启动
bash
sudo cp system/eink-reader.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable eink-reader.service
sudo systemctl start eink-reader.service
### 查看日志
bash
sudo journalctl -u eink-reader.service -f
## 使用说明

### 按键功能
- **上一页**: 短按返回上一页
- **下一页**: 短按进入下一页
- **主页**: 短按返回主菜单，长按3秒关机
- **菜单**: 打开设置菜单

### Wi-Fi 传书
1. 确保阅读器连接到 Wi-Fi
2. 在设置中启用 Wi-Fi 传书
3. 在同一网络下的设备访问显示的网址
4. 上传书籍文件

### 添加书籍
1. 将书籍文件放入 `books/` 目录
2. 重启阅读器
3. 在主菜单中选择书籍

## 项目结构
eink-reader/
├── main.py # 主程序入口
├── requirements.txt # 依赖包列表
├── config.json # 配置文件
├── README.md # 项目说明
├── start.sh # 启动脚本
├── core/ # 核心模块
├── hardware/ # 硬件控制
├── ui/ # 用户界面
├── utils/ # 工具函数
├── books/ # 书籍目录
└── system/ # 系统配置
## 开发指南

### 添加新功能
1. 在相应模块目录创建新文件
2. 在主程序中注册新模块
3. 更新配置文件
4. 添加用户界面

### 调试
bash
查看详细日志
sudo journalctl -u eink-reader.service -f --no-pager
手动调试
sudo python3 -m pdb main.py
## 常见问题

### 1. 屏幕不显示
- 检查 HDMI 连接
- 检查屏幕供电
- 运行测试程序: `python3 test_screen.py`

### 2. 按键无响应
- 检查 GPIO 连接
- 检查用户权限: `sudo usermod -a -G gpio $USER`
- 重启服务: `sudo systemctl restart eink-reader.service`

### 3. 系统卡顿
- 检查电源是否 5V/3A
- 检查 SD 卡剩余空间
- 降低屏幕刷新频率

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题，请通过以下方式联系：
- GitHub Issues: [项目地址](https://github.com/mingtian567-star/eink-reader.git)
- Email: 2811749082@qq.com
