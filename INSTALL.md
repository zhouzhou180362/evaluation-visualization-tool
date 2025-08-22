# 📦 安装说明

## 🔧 本地环境要求

### Python版本
- Python 3.8 或更高版本
- 推荐：Python 3.9

### 必需依赖包

```bash
pip install pandas numpy openpyxl streamlit matplotlib
```

或者使用requirements.txt：

```bash
pip install -r requirements.txt
```

## 🚀 快速开始

### 1. 安装依赖
```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行应用
```bash
streamlit run app.py
```

### 3. 访问应用
打开浏览器访问：http://localhost:8501

## 📋 依赖包说明

- **pandas**: 数据处理和分析
- **numpy**: 数值计算
- **openpyxl**: Excel文件读写
- **streamlit**: Web应用框架
- **matplotlib**: 图表绘制

## ⚠️ 注意事项

1. **确保所有依赖包都已安装**
2. **Python脚本需要在有依赖包的环境中运行**
3. **如果遇到导入错误，请检查依赖包安装状态**

## 🔍 故障排除

### 问题：ModuleNotFoundError: No module named 'pandas'

**解决方案：**
```bash
pip install pandas
```

### 问题：ModuleNotFoundError: No module named 'openpyxl'

**解决方案：**
```bash
pip install openpyxl
```

### 问题：ModuleNotFoundError: No module named 'numpy'

**解决方案：**
```bash
pip install numpy
```

## 📚 更多信息

- 查看 `requirements.txt` 了解具体版本要求
- 查看 `README.md` 了解应用功能
- 查看 `DEPLOYMENT.md` 了解部署说明
