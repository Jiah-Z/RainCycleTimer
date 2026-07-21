# Changelog

All notable changes to Rain Cycle Timer (RainCycleClock) will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [1.0.0] - 2026-07-20

### Added
- Windows 平台移植（基于 PyQt5）
- 可视化设置工具 (settings_editor.py)
- 自定义显示热键和退出热键（分别可设置）
- 窗口缩放 (Zoom In/Out) 与重置
- 窗口置顶 (Always on Top) 切换
- 计时结束的"波"扩散与业力"震动"动画
- 业力等级持久化保存到 config.json
- 全局退出热键（默认 Ctrl+Shift+Q）
- 支持加载 JSON 配置文件 (多区间顺序播放)
- 支持直接设置倒计时秒数 (Set Countdown)

### Changed
- 基于 Trebor-Huang/clock 进行改进
- 移除了 Hold 模式（因稳定性问题），仅保留 Toggle 模式
- 优化资源加载路径，支持 PyInstaller 打包

### Fixed
- 修复资源路径问题（图片、音效无法找到）
- 修复业力等级在 Set Countdown 后重置为 1 的 Bug
- 修复波边缘被裁剪的问题，添加透明度淡出

### Removed
- 移除 macOS 专用的 AppKit 依赖
- 移除 Hold 模式（键盘钩子导致的不稳定）