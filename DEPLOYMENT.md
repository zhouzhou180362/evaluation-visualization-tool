# 🚀 部署说明 - 自动化评测可视化工具

## 📋 部署前准备

### 1. 选择依赖文件

我们提供了两个依赖文件：

- **`requirements.txt`** - 推荐版本（有版本范围）
- **`requirements-minimal.txt`** - 最小版本（固定版本，兼容性最好）

### 2. 推荐使用最小版本

在Streamlit Cloud上，建议使用 `requirements-minimal.txt`：

1. 在Streamlit Cloud部署时，将 `requirements.txt` 重命名为 `requirements-minimal.txt`
2. 或者直接使用 `requirements-minimal.txt` 作为依赖文件

## 🔧 常见问题解决

### 问题1：pandas未安装

**解决方案：**
- 使用 `requirements-minimal.txt`
- 确保Python版本为3.9或3.10
- 在Streamlit Cloud上选择 "Python 3.9"

### 问题2：图表无法显示

**解决方案：**
- 应用会自动检测可用的图表库
- 优先使用Plotly（更轻量）
- 备用方案：Matplotlib
- 最后方案：纯文本统计

### 问题3：Excel文件无法读取

**解决方案：**
- 确保使用 `openpyxl==3.1.2`
- 检查Excel文件格式（.xlsx）
- 文件大小不超过50MB

## 🌐 Streamlit Cloud部署步骤

### 1. 准备文件

确保以下文件存在：
```
├── app.py                    # 主应用
├── requirements-minimal.txt  # 依赖文件（推荐）
├── .streamlit/
│   └── config.toml         # 配置文件
└── README.md               # 说明文档
```

### 2. 部署设置

在Streamlit Cloud上：
- **Main file path**: `app.py`
- **Python version**: 3.9
- **Requirements file**: `requirements-minimal.txt`

### 3. 环境变量（可选）

```
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
```

## 📊 功能特性

### 核心功能
- ✅ 多种评测类型支持
- ✅ 双文件对比分析
- ✅ 智能依赖检测
- ✅ 备用方案支持

### 图表支持
- 🎯 Plotly（推荐，轻量）
- 📈 Matplotlib（备用）
- 📝 纯文本统计（兜底）

### 文件格式
- 📊 Excel (.xlsx)
- 📋 CSV (计划中)
- 📄 JSON (计划中)

## 🆘 故障排除

### 如果应用无法启动

1. 检查Python版本（推荐3.9）
2. 使用 `requirements-minimal.txt`
3. 查看Streamlit Cloud日志
4. 确保所有文件都已上传

### 如果功能受限

1. 应用会自动显示警告信息
2. 检查依赖包安装状态
3. 某些功能会降级为文本模式

## 📞 技术支持

如果遇到问题：
1. 查看Streamlit Cloud日志
2. 检查依赖包版本
3. 确认文件格式正确
4. 使用最小依赖版本

---

**注意：** 此应用已针对Streamlit Cloud进行了优化，支持自动降级和备用方案，确保在各种环境下都能正常运行。
