# 🤖 AI智能面试官系统

基于DeepSeek大模型的智能面试评估系统，提供专业、客观、高效的AI面试体验。

## ✨ 特性

- 🎯 **多种面试模式**: 基础面试、JD定向面试、简历匹配面试
- 🧠 **智能评估**: 基于AI的多维度评估和打分
- 📊 **详细报告**: 自动生成专业的面试评估报告
- 🌐 **多端支持**: Gradio Web界面、Streamlit仪表板、FastAPI
- 📈 **数据统计**: 面试历史和趋势分析
- 🔒 **安全可靠**: 完善的错误处理和日志系统

## 🏗️ 技术架构

- **后端**: Python 3.11+ / DeepSeek LLM / BGE嵌入模型 / LangChain
- **前端**: Gradio / Streamlit / FastAPI
- **存储**: Qdrant向量数据库 / 本地文件系统
- **部署**: Docker / 本地部署

## 📋 系统要求

- Python 3.11+
- 8GB+ 内存
- DeepSeek API密钥
- （可选）Qdrant服务

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd llm-developing-mock-interview

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements_new.txt
```

### 2. 配置环境

```bash
# 复制环境变量文件
copy .env.example .env

# 编辑.env文件，填入你的API密钥
# DEEPSEEK_API_KEY=sk-your-api-key-here
```

### 3. 项目初始化

```bash
# 检查配置
python check_config.py

# 项目初始化（创建必要目录）
python app.py setup

# 检查系统状态
python app.py check
```

### 4. 启动应用

#### 方式一：Gradio Web界面（推荐）
```bash
python app.py gradio
# 访问 http://localhost:7860
```

#### 方式二：Streamlit仪表板
```bash  
python app.py streamlit
# 访问 http://localhost:8501
```

#### 方式三：FastAPI服务
```bash
python app.py api  
# API文档 http://localhost:8000/docs
```

#### 方式四：快速演示
```bash
# Windows
demo.bat

# Linux/Mac
./demo.sh
```

## 📖 使用指南

### 面试模式

1. **基础面试**: 通用技术面试，适用于各种技术岗位
2. **JD定向面试**: 基于具体职位描述的针对性面试  
3. **简历匹配面试**: 基于候选人简历的个性化面试

### 评估维度

- **技术准确性** (25%): 技术概念理解的准确性
- **沟通表达** (20%): 语言表达的清晰度和逻辑性
- **问题解决** (20%): 分析和解决问题的能力
- **经验深度** (20%): 实践经验的丰富程度  
- **学习能力** (15%): 学习新技术的能力和意愿

### API使用

```python
import requests

# 开始面试
response = requests.post('http://localhost:8000/interview/start', json={
    'mode': 'basic',
    'resume_content': '',
    'jd_content': ''
})

session_id = response.json()['data']['session_id']

# 继续对话
response = requests.post('http://localhost:8000/interview/continue', json={
    'session_id': session_id,
    'user_response': '您好，我是一名Python开发工程师...'
})

# 结束面试
response = requests.post('http://localhost:8000/interview/end', json={
    'session_id': session_id
})
```

## 🗂️ 项目结构

```
llm-developing-mock-interview/
├── app.py                  # 主启动器
├── requirements_new.txt    # 依赖包
├── .env.example           # 环境变量示例  
├── backend/               # 后端模块
│   ├── models/           # 模型封装
│   ├── services/         # 业务服务
│   └── utils/           # 工具模块
├── frontend/             # 前端应用
│   ├── gradio_app.py    # Gradio界面
│   └── streamlit_app.py # Streamlit界面
├── api/                  # API服务
│   └── main.py          # FastAPI应用
├── tests/               # 测试模块
├── data/                # 数据文件
├── chat_history/        # 聊天记录
├── logs/                # 日志文件
└── reports/            # 报告输出
```

## 🔧 配置说明

### 必需配置

- `DEEPSEEK_API_KEY`: DeepSeek API密钥（必填）
- `DEEPSEEK_BASE_URL`: API基础URL（默认：https://api.deepseek.com）

### 可选配置

- `BGE_MODEL_PATH`: BGE模型本地路径
- `QDRANT_HOST`: Qdrant服务地址
- `LOG_LEVEL`: 日志级别

完整配置说明请参考 `.env.example` 文件。

## 🧪 测试

```bash
# 运行基础测试
python -m pytest tests/ -v

# 运行特定测试
python tests/test_evaluation_service.py

# 检查代码覆盖率
pip install coverage
coverage run -m pytest tests/
coverage report
```

## 📊 性能优化

- **模型缓存**: BGE模型支持本地缓存
- **并发控制**: 支持多并发会话管理
- **内存管理**: 自动清理过期会话数据
- **错误重试**: 网络请求自动重试机制

## 🔒 安全说明

- API密钥通过环境变量管理，不提交到代码库
- 文件上传大小限制，防止恶意攻击
- 输入验证和XSS防护
- 会话隔离，防止数据泄露

## 📈 监控和日志

- 结构化日志记录
- 面试会话跟踪
- 错误监控和告警
- 性能指标统计

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📝 更新日志

### v1.0.0 (2024-xx-xx)
- 🎉 首次发布
- ✨ 支持多种面试模式
- 🧠 AI智能评估系统
- 📊 报告生成功能
- 🌐 多端支持

## ❓ 常见问题

### Q: DeepSeek API调用失败怎么办？
A: 请检查API密钥是否正确，网络是否正常，可以运行 `python check_config.py` 进行诊断。

### Q: BGE模型下载速度慢？
A: 可以设置 `BGE_MODEL_PATH` 使用本地模型，或配置代理加速下载。

### Q: 如何自定义面试问题？
A: 可以修改 `backend/services/interview_service.py` 中的面试模板。

### Q: 支持哪些文件格式？
A: 目前支持 .txt、.md、.pdf 格式的简历和职位描述文件。

## 📄 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。

## 👥 致谢

- [DeepSeek](https://www.deepseek.com/) - 提供强大的语言模型
- [BGE](https://github.com/FlagOpen/FlagEmbedding) - 优秀的中文嵌入模型
- [LangChain](https://github.com/langchain-ai/langchain) - 强大的AI应用开发框架
- [Gradio](https://gradio.app/) - 简单易用的Web界面框架

---

**如果这个项目对你有帮助，请给一个 ⭐️ Star！**

## 📞 联系我们

- 项目主页: [GitHub Repository]
- 问题反馈: [Issues]
- 邮箱: [your-email@example.com]

**让AI面试更智能，让求职更高效！** 🚀
