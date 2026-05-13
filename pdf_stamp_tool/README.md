# 文件盖章易

专业版 Windows 桌面 PDF/Word 本地盖章工具。

## 技术栈

- Python 3.11 / 3.12
- PySide6
- PyMuPDF
- Pillow
- PyInstaller

## 当前阶段

当前实现为工程骨架和静态 UI：

- 顶部文件工作栏
- 左侧参数面板
- 右侧 PDF 预览工作区占位
- 底部日志与进度区
- 核心数据模型
- 配置与缓存目录初始化

后续模块将继续接入 PDF 渲染、印章处理、坐标交互、Word 转 PDF 和最终输出。

## 运行

```powershell
pip install -r requirements.txt
python main.py
```

