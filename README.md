# 文件盖章易 / File Stamp Easy

文件盖章易是一个本地优先的 PDF/Word 盖章工具套件，包含两个实现：

- `pdf_stamp_tool/` - Windows 桌面版，Python + PySide6 + PyMuPDF + Pillow，支持绿色版 exe 打包
- `pdf_stamp_web/` - Web 版，浏览器本地处理 PDF 和印章图片，已部署到 Netlify

核心目标：

- 普通公章、法人签字章、骑缝章统一管理
- 正红透字、真实印泥感、透明叠加
- Word 本地转 PDF
- 页面可视化放置、拖拽、删除、清空
- 默认不依赖服务器，文件尽量在本地完成处理

## 仓库结构

```text
pdf_stamp_tool/   Windows 桌面版
pdf_stamp_web/    Web 版
docs/             架构与发布说明
```

## 版本概览

### Windows 桌面版

特性：

- PySide6 专业桌面 UI
- PDF 预览、放章、拖拽、导出
- 普通章 / 签字章 / 骑缝章
- Word 自动转 PDF
- 设置持久化到 `user_data/settings.json`
- PyInstaller 绿色版打包

构建方式：

```powershell
cd pdf_stamp_tool
.\build_portable.ps1
```

### Web 版

特性：

- 浏览器内本地预览 PDF
- 本地处理印章图片
- 导出盖章 PDF
- 拖拽导入、页面标记、骑缝章
- 已部署到 Netlify

在线地址：

- [Production](https://file-stamp-easy-web-20260513.netlify.app)

构建方式：

```powershell
cd pdf_stamp_web
npm install
npm run build
```

## 本地优先说明

两种版本都尽量保持本地处理：

- 桌面版不上传文件
- Web 版在浏览器里完成 PDF/图片处理，不走服务器上传链路

## 说明文档

- [架构说明](docs/ARCHITECTURE.md)
- [发布说明](docs/RELEASE.md)

