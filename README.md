# 剪切板发送器 v3.0

Windows 10 上运行的剪切板监听工具，检测到剪切板文本变化后，将内容发送到已打开的 ChatGPT 网页客户端，并自动回车发送。

## 功能
- 监听剪切板文本变化并自动发送
- 站点优先级：chatgpt.com → ai.google.com → chat.deepseek.com
- 未检测到站点时弹窗提示（重试/退出）
- 托盘最小化，右键退出
- 作者按钮：点击打开 https://blog.dengfangbo.com

## 运行前提
- Windows 10
- 系统已安装 Edge
- Edge 以调试端口启动

启动 Edge（必须）：


## 依赖安装（Python 3.12 64位）


说明：程序通过 CDP 连接系统 Edge，不需要打包 Chromium。Playwright 的 Chromium 可不安装，但建议保留以免依赖缺失。

## 启动


## 使用
1) 打开目标网站（按优先级）
2) 点击“开始”
3) 复制任意文本到剪切板
4) 程序会自动粘贴并回车发送

## 打包（onefile，精简版
1) 见release

## 常见问题
- 未检测到调试端口：请确认 Edge 使用了启动命令，并且端口未被占用。
- 无法发送：确认输入框可编辑且已加载完成。
