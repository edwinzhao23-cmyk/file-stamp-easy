# 架构说明

## 产品分层

### 1. Windows 桌面版

目录：`pdf_stamp_tool/`

技术栈：

- Python 3.12
- PySide6
- PyMuPDF
- Pillow
- PyInstaller

职责：

- Word / PDF 导入
- 页面预览与坐标交互
- 普通章、签字章、骑缝章管理
- 印章图像处理
- PDF 输出
- 绿色版打包

### 2. Web 版

目录：`pdf_stamp_web/`

技术栈：

- Vite
- pdfjs-dist
- pdf-lib
- 原生 HTML / CSS / JS

职责：

- 浏览器本地 PDF 预览
- 页面放章与拖拽
- 本地图像处理
- 导出盖章 PDF
- Netlify 部署

## 设计原则

- 本地优先
- 坐标统一
- 页面预览与最终输出一致
- 正红透字
- 用户可恢复、可撤销、可清空

## 目录边界

```text
pdf_stamp_tool/   桌面版源代码与打包脚本
pdf_stamp_web/    Web 版源码与部署配置
docs/             共享说明
```

