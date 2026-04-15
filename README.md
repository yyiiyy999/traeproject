# AI智能体开发教学项目

这是一个基于Python的AI智能体开发教学项目，旨在帮助学习者从零开始掌握AI智能体的开发技能。

## 项目结构

```
traeproject/
├── env.example              # 环境变量配置模板
├── .gitignore              # Git忽略文件配置
├── practice01/             # 练习1：基础LLM客户端
│   └── llm_client.py      # 单次请求LLM并统计指标
├── practice02/             # 练习2：交互式聊天客户端
│   └── chat_client.py     # 流式输出交互式聊天
├── practice02.2/           # 练习2.2：工具调用客户端
│   └── chat_client_with_tools.py  # 支持文件系统工具调用
├── practice03/             # 练习3：增强版工具调用客户端
│   ├── chat_client.py      # 基础聊天客户端
│   ├── tool_client.py      # 工具客户端
│   └── tool_chat_client.py # 支持curl网络访问的工具聊天客户端
└── README.md              # 项目说明文档
```

## 环境配置

### 1. 创建虚拟环境

```bash
python -m venv venv
```

### 2. 激活虚拟环境

Windows:
```bash
venv\Scripts\activate
```

Linux/Mac:
```bash
source venv/bin/activate
```

### 3. 配置环境变量

复制环境变量模板文件：
```bash
cp env.example .env
```

编辑`.env`文件，填写你的LLM API配置：
```env
BASE_URL="https://api.example.com/v1"
MODEL="gpt-3.5-turbo"
API_KEY="your-api-key-here"
TEMPERATURE=0.7
MAX_TOKENS=1000
```

## 练习内容

### Practice 01: 基础LLM客户端

**文件位置**: `practice01/llm_client.py`

**功能特点**:
- 读取项目根目录的`.env`文件获取配置
- 使用Python标准库`http.client`访问LLM API
- 发送单次聊天完成请求
- 统计并显示以下指标：
  - 提示词Token数
  - 完成Token数
  - 总Token数
  - 响应时间（秒）
  - Token处理速度（tokens/秒）

**运行方式**:
```bash
python practice01/llm_client.py
```

**学习目标**:
- 理解OpenAI兼容协议的API调用方式
- 掌握HTTP请求的基本原理
- 学习如何统计和分析API调用性能指标

### Practice 02: 交互式聊天客户端

**文件位置**: `practice02/chat_client.py`

**功能特点**:
- 支持终端界面实时输入聊天内容
- 实现流式输出，实时显示AI响应
- 自动维护聊天历史记录，每次请求都会包含完整上下文
- 支持Ctrl+C优雅退出
- 显示会话统计信息（总对话轮次、总耗时）

**运行方式**:
```bash
python practice02/chat_client.py
```

**使用说明**:
1. 运行程序后，在终端输入消息与AI对话
2. AI响应会以流式方式实时显示
3. 输入空消息会跳过
4. 按Ctrl+C退出程序，显示会话统计

**学习目标**:
- 理解流式API的工作原理
- 掌握对话状态管理和上下文维护
- 学习如何处理用户中断和异常情况
- 实现用户友好的交互界面

### Practice 02.2: 工具调用客户端

**文件位置**: `practice02.2/chat_client_with_tools.py`

**功能特点**:
- 基于practice02的交互式聊天功能
- 集成5个文件系统操作工具：
  1. `list_files(directory)` - 列出目录下的文件及其属性
  2. `rename_file(directory, old_name, new_name)` - 修改文件名
  3. `delete_file(directory, filename)` - 删除文件
  4. `create_file(directory, filename, content)` - 创建文件并写入内容
  5. `read_file(directory, filename)` - 读取文件内容
- 支持LLM通过JSON格式调用工具
- 工具执行结果自动返回给LLM进行分析
- 完整的错误处理机制

**运行方式**:
```bash
python practice02.2/chat_client_with_tools.py
```

**使用说明**:
1. 运行程序后，在终端输入消息与AI对话
2. 可以要求AI执行文件操作，例如：
   - "列出practice01目录下的文件"
   - "在practice02.2目录创建一个名为test.txt的文件，内容为'Hello World'"
   - "读取practice02.2目录下的test.txt文件内容"
3. AI会自动调用相应的工具并返回结果
4. 输入 'quit' 或 'exit' 退出程序

**学习目标**:
- 理解工具调用的基本原理
- 掌握如何设计和实现工具接口
- 学习如何在LLM系统中集成外部工具
- 理解工具执行结果的处理和反馈机制
- 掌握JSON格式的工具调用协议

### Practice 03: 增强版工具调用客户端

**文件位置**: `practice03/tool_chat_client.py`

**功能特点**:
- 基于practice02.2的工具调用功能
- 新增curl网络访问工具：
  - `curl(url)` - 通过HTTP请求访问网页并返回内容
- 支持识别curl相关指令，直接执行网络访问
- 集成6个工具：5个文件操作工具 + 1个网络访问工具
- 保持与之前版本相同的用户交互体验
- 完整的错误处理和内容截断机制

**运行方式**:
```bash
python practice03/tool_chat_client.py
```

**使用说明**:
1. 运行程序后，在终端输入消息与AI对话
2. 可以要求AI执行文件操作，例如：
   - "列出当前目录文件"
   - "创建一个test.txt文件，内容是Hello World"
3. 可以要求AI执行网络访问，例如：
   - "curl https://www.example.com"
   - "访问网页 https://www.python.org"
4. AI会自动调用相应的工具并返回结果
5. 输入 'quit' 或 'exit' 退出程序

**学习目标**:
- 理解如何扩展工具调用系统
- 掌握网络请求的基本原理和实现
- 学习如何处理网络响应和错误
- 理解工具调用的安全性考虑
- 掌握如何设计和实现新的工具接口

## 技术栈

- **Python**: 3.13+
- **HTTP客户端**: Python标准库`http.client`
- **数据格式**: JSON
- **API协议**: OpenAI兼容协议

## 项目特色

1. **零依赖**: 仅使用Python标准库，无需安装额外依赖
2. **教学导向**: 代码结构清晰，注释详细，适合学习
3. **实战导向**: 从基础到进阶，循序渐进
4. **可扩展**: 为后续功能扩展预留空间

## 注意事项

- 确保已正确配置`.env`文件
- API密钥请妥善保管，不要提交到版本控制系统
- 使用流式输出时，确保网络连接稳定
- 注意API调用频率限制

## 后续扩展方向

- 支持多轮对话的token限制管理
- 添加对话历史持久化存储
- 实现对话模板和角色设定
- 扩展更多工具类型（网络请求、数据库操作等）
- 添加对话质量评估功能
- 实现工具调用的权限控制
- 支持并行工具调用

## 许可证

本项目仅供教学使用。
