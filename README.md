# 自动化评测可视化工具

一个基于Streamlit的自动化评测结果可视化工具，支持多种评测场景的数据处理和对比分析。

## 功能特性

- 支持多种评测类型：问答提取、翻译提取、解释代码提取等
- 双文件对比分析
- 详细的统计报告和可视化图表
- 列级均值统计和阈值计数
- 支持按行序或按键列对齐

## 本地运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行应用：
```bash
streamlit run app.py
```

## 部署到Streamlit Cloud

1. 将代码推送到GitHub仓库
2. 访问 [Streamlit Cloud](https://share.streamlit.io/)
3. 连接GitHub仓库
4. 设置部署参数：
   - Main file path: `app.py`
   - Python version: 3.9+

## 部署到其他服务器

### 使用Docker部署

1. 构建镜像：
```bash
docker build -t evaluation-tool .
```

2. 运行容器：
```bash
docker run -p 8501:8501 evaluation-tool
```

### 使用systemd服务部署

1. 创建服务文件：
```bash
sudo nano /etc/systemd/system/evaluation-tool.service
```

2. 配置服务：
```ini
[Unit]
Description=Evaluation Tool Streamlit App
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/your/app
Environment=PATH=/path/to/your/venv/bin
ExecStart=/path/to/your/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

3. 启动服务：
```bash
sudo systemctl enable evaluation-tool
sudo systemctl start evaluation-tool
```

## 环境要求

- Python 3.8+
- 依赖包见 requirements.txt

## 使用说明

1. 选择处理类型
2. 上传1-2个Excel文件
3. 选择对齐方式（可选）
4. 点击开始处理
5. 查看结果和下载报告
