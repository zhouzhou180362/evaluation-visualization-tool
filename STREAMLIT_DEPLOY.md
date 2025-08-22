# Streamlit Cloud 部署指南

## 部署步骤

### 1. 准备代码
确保您的代码已经修复了以下问题：
- 移除了对外部Python脚本的依赖
- 使用内置处理逻辑
- 更新了requirements.txt

### 2. 推送到GitHub
```bash
git add .
git commit -m "修复Streamlit Cloud兼容性问题"
git push origin main
```

### 3. 在Streamlit Cloud上部署
1. 访问 [share.streamlit.io](https://share.streamlit.io)
2. 使用GitHub账号登录
3. 选择您的仓库
4. 设置部署参数：
   - **Main file path**: `app.py`
   - **Python version**: 3.9 或 3.10
   - **Requirements file**: `requirements.txt`

### 4. 常见问题解决

#### 问题1: "No module named 'pandas'"
**解决方案**: 确保requirements.txt包含所有必要的依赖包

#### 问题2: 文件路径错误
**解决方案**: 代码已修改为使用内置处理逻辑，不依赖外部文件

#### 问题3: 字体显示问题
**解决方案**: 已优化字体设置，使用更兼容的字体

## 部署后的功能

✅ 支持多种Excel处理类型
✅ 内置处理逻辑，无需外部脚本
✅ 文件对比和统计分析
✅ 可视化图表生成
✅ 结果文件下载

## 注意事项

1. **文件大小限制**: Streamlit Cloud对上传文件有大小限制
2. **处理时间**: 大文件处理可能需要较长时间
3. **内存限制**: 云环境有内存使用限制
4. **并发用户**: 免费版本有并发用户数限制

## 技术支持

如果遇到部署问题，请检查：
1. requirements.txt是否完整
2. 代码是否包含语法错误
3. 是否使用了云环境不支持的功能
