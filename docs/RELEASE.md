# 发布说明

## Windows 桌面版

### 构建绿色版

```powershell
cd pdf_stamp_tool
.\build_portable.ps1
```

输出：

- `pdf_stamp_tool/dist/文件盖章易/`
- `pdf_stamp_tool/dist/文件盖章易_绿色版.zip`

### 运行要求

- Windows 10 / 11
- Word / WPS / LibreOffice 任选其一可用于 Word 转 PDF

## Web 版

### 本地构建

```powershell
cd pdf_stamp_web
npm install
npm run build
```

### Netlify 发布

已配置 `netlify.toml`。

部署命令：

```powershell
npx netlify deploy --prod --dir=dist
```

