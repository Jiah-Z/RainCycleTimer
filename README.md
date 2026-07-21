# 雨循环计时器 (RainCycleTimer)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**雨循环计时器** 是一款 Windows 桌面工具，复刻了游戏《雨世界》(Rain World) 中的"业力时钟"。

在《雨世界》中，这个 UI 被称为 **Cycle Timer（轮回计时器）** 或 **Rain Timer（雨期计时器）**。它是游戏生存机制的核心：每个轮回开始后，计时器便会开始倒计时，代表暴雨来临前的剩余时间。玩家必须在此之前抵达避难所并成功休眠，才能推进游戏。

本项目是基于 [Trebor-Huang/clock](https://github.com/Trebor-Huang/clock) 的衍生作品，在保留原 MIT 许可证的前提下，进行了大量改进和 Windows 平台移植。
在开发过程中，代码逻辑借助了 AI 辅助编程工具进行实现与调试。


## 游戏中的计时器机制

| 要素 | 说明 |
|------|------|
| 业力符号 | 中央的符号代表玩家当前的业力等级 (1~10) |
| 小点 (Pips) | 环绕在业力符号周围，每个点代表约 30 秒的剩余时间 |
| 轮回时长 | 每个轮回的时长在游戏内是随机生成的，并非固定值 |
| 暴雨降临 | 当所有小点消失，暴雨便会降临。玩家必须在此之前抵达避难所 |

本项目在保留其视觉风格的基础上，将其改造为一个独立的桌面计时工具，适用于专注计时、直播辅助等场景。


## 主要改进 (与原始项目对比)

- 跨平台移植：从 macOS 原生应用移植至 Windows (使用 PyQt5)
- 交互增强：支持鼠标拖拽移动窗口、双击切换显示
- 可视化设置工具：提供 settings_editor.py，无需编辑代码即可调整所有参数
- 热键自定义：支持分别自定义显示/隐藏和退出热键
- 窗口控制：支持缩放 (Zoom) 和置顶 (Always on Top) 切换
- 业力等级持久化：手动设置的业力等级会自动保存，下次启动恢复
- 计时结束特效：添加"波"扩散与业力图标"震动"动画，更贴近游戏原版体验
- 一键打包：支持使用 PyInstaller 打包为独立 exe 文件


## 系统要求

- Windows 10 / 11
- Python 3.11 及以上（如果使用源代码运行）
- 若使用打包好的 exe，无需安装 Python


## 快速开始

### 方式一：使用打包好的 exe（推荐给普通用户）

1. 从 Releases 页面下载 RainCycleTimer.zip
2. 解压到任意文件夹
3. 双击 RainCycleTimer.exe 即可运行
4. 如需调整参数，双击 RainCycleTimerEditor.exe（设置工具）

## 使用指南（也可查看文件内的教程）

### 基本操作

| 操作 | 效果 |
|------|------|
| 左键按住并拖动 | 移动时钟位置 |
| 左键双击 | 切换显示/隐藏 |
| 右键单击 | 弹出主菜单（所有设置入口） |
| 显示热键（默认 Ctrl+Shift+F） | 切换显示/隐藏 |
| 退出热键（默认 Ctrl+Shift+Q） | 立即退出程序 |

### 右键菜单功能

- Set Countdown (seconds)：快速创建单段倒计时（输入秒数）
- Load JSON：加载 JSON 配置文件（支持多区间顺序播放）
- Set Karma Level：调整业力符号等级（1~10）
- Zoom：放大/缩小/重置窗口大小
- Settings：
  - Set Show Hotkey：自定义显示热键
  - Set Quit Hotkey：自定义退出热键
  - Sound ON/OFF：全局声音开关
- Toggle Always on Top：窗口置顶开关
- Quit：退出程序

### 配置文件

config.json 保存所有自定义设置（热键、缩放、业力等级、波参数等）。如果你手动编辑它，请确保 JSON 格式正确。


## 自定义 JSON 配置

你可以通过 Load JSON 加载复杂的计时序列。示例：

{
  "ticktock": 2.0,
  "intervals": [
    {
      "totalPip": 20,
      "totalTime": 300,
      "karmaSymbol": 3,
      "karmaReinforced": false,
      "maxKarma": 5
    },
    {
      "totalPip": 10,
      "totalTime": 120,
      "karmaSymbol": 7,
      "karmaReinforced": true,
      "maxKarma": 10
    }
  ]
}

字段说明：
- ticktock：滴答声间隔（秒）
- intervals：区间列表，每个区间包含：
  - totalPip：圆点总数
  - totalTime：持续时间（秒）
  - karmaSymbol：业力等级 (0~10)
  - karmaReinforced：是否显示强化花环 (true/false)
  - maxKarma：若等级 >5，需指定最大值 (7~10)

## 许可证与版权声明

### 代码部分

本项目代码采用 MIT 许可证。详情请见 LICENSE 文件。

- 原始项目 Trebor-Huang/clock 版权归 Trebor-Huang 所有，遵循 MIT 许可证。
- 本项目的修改和新增代码版权归 Jiah-Z 所有，同样遵循 MIT 许可证。

### 游戏素材部分

resources/ 目录下的所有图片（Karma_*.png, Circle.png, CircleReinforced.png）和音效（*.wav）均来自游戏《雨世界》(Rain World)，版权归其开发者 Videocult 所有。这些素材不包含在本项目的 MIT 许可证范围内，使用时应遵守原游戏的版权规定。


## 如何贡献

欢迎提交 Issue 和 Pull Request！请先阅读 CONTRIBUTING.md 了解贡献指南。


## 联系方式

- 作者：Jiah-Z
- GitHub：https://github.com/Jiah-Z


## 致谢

- 感谢 Trebor-Huang 的原始项目 clock
- 感谢《雨世界》(Rain World) 游戏提供的灵感与素材


Enjoy!
