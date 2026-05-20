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
│   ├── chat_client.py     # 流式输出交互式聊天（支持工具调用）
│   └── tool_chat_client.py # 工具聊天客户端（网络访问专用）
├── practice03/             # 练习3：聊天记录压缩客户端
│   ├── chat_client_with_summary.py # 支持聊天记录自动压缩
│   └── chat_client_with_extraction.py # 支持关键信息提取和搜索
├── practice04/             # 练习4：AnythingLLM文档仓库查询客户端
│   ├── chat_client.py     # 支持AnythingLLM文档仓库查询
│   └── test_query.py      # AnythingLLM查询测试脚本
├── practice05/             # 练习5：技能系统智能体
│   ├── chat_client.py     # 技能系统智能体主程序
│   └── test_skill.py      # 技能测试脚本
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
- **工具调用功能**:
  - `list_files(directory)` - 列出目录下的文件及其属性
  - `rename_file(directory, old_name, new_name)` - 修改文件名
  - `delete_file(directory, filename)` - 删除文件
  - `create_file(directory, filename, content)` - 创建文件并写入内容
  - `read_file(directory, filename)` - 读取文件内容
  - `fetch_webpage(url)` - 通过curl访问网页并返回网页内容，可用于获取天气预报等信息

**运行方式**:
```bash
python practice02/chat_client.py
```

**使用说明**:
1. 运行程序后，在终端输入消息与AI对话
2. AI响应会以流式方式实时显示
3. 输入空消息会跳过
4. 按Ctrl+C退出程序，显示会话统计
5. 可以要求AI执行文件操作或网络访问，例如：
   - "列出practice01目录下的文件"
   - "获取北京的天气预报"

**学习目标**:
- 理解流式API的工作原理
- 掌握对话状态管理和上下文维护
- 学习如何处理用户中断和异常情况
- 实现用户友好的交互界面
- 理解工具调用的基本原理
- 掌握如何设计和实现工具接口

### Practice 02.1: 网络访问工具客户端

**文件位置**: `practice02/tool_chat_client.py`

**功能特点**:
- 基于practice02的交互式聊天功能
- 集成网络访问工具：
  - `fetch_webpage(url)` - 通过curl访问网页，可用于获取天气预报等信息
  - `get_current_date()` - 获取当前日期和时间
- 系统提示词自动包含当前日期，解决LLM不知道日期的问题
- 支持通过wttr.in获取天气预报，格式：`https://wttr.in/城市名`
- 自动解析工具调用并执行，然后将结果返回给LLM进行总结

**运行方式**:
```bash
python practice02/tool_chat_client.py
```

**使用说明**:
1. 运行程序后，在终端输入消息与AI对话
2. 可以要求AI获取天气预报，例如："请看看明天青城山的最高和最低气温"
3. AI会自动调用fetch_webpage工具获取天气信息
4. 工具执行完成后，AI会对结果进行总结并以自然语言回复
5. 输入 'quit' 或 'exit' 退出程序

**学习目标**:
- 理解如何使用subprocess模块调用curl命令
- 掌握HTTP网络请求的实现
- 理解如何在系统提示词中动态注入当前日期
- 掌握天气预报API的使用方法
- 理解工具调用的完整流程：解析、执行、结果反馈和总结

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

### Practice 03: 聊天记录压缩客户端

**文件位置**: `practice03/chat_client_with_summary.py`

**功能特点**:
- 基于practice02的交互式聊天功能
- 智能聊天记录压缩：
  - 当聊天超过5轮时自动触发压缩
  - 当聊天上下文长度超过3000字符时自动触发压缩
  - 对前70%的聊天内容进行总结压缩
  - 保留最后30%的聊天内容原文
- 自动使用LLM进行聊天记录总结
- 保持与之前版本相同的用户交互体验
- 完整的错误处理机制

**运行方式**:
```bash
python practice03/chat_client_with_summary.py
```

**使用说明**:
1. 运行程序后，在终端输入消息与AI对话
2. 正常与AI进行对话，无需手动触发压缩
3. 当聊天达到5轮或上下文超过3k时，系统会自动进行压缩
4. 压缩过程中会显示相应的系统提示
5. 输入 'quit' 或 'exit' 退出程序

**学习目标**:
- 理解聊天历史管理的重要性
- 掌握如何使用LLM进行文本总结
- 学习如何设计和实现聊天记录压缩策略
- 理解上下文长度限制对LLM性能的影响
- 掌握如何在保持对话连贯性的同时优化上下文长度

### Practice 04: AnythingLLM文档仓库查询客户端

**文件位置**: `practice04/chat_client.py`

**功能特点**:
- 基于practice03的聊天记录压缩功能
- AnythingLLM文档仓库集成：
  - 使用subprocess模块调用curl命令访问AnythingLLM API（注意中文编码处理）
  - 支持查询`http://localhost:3001/api/v1/workspace/{workspace_slug}/chat`接口
  - 使用message字段发送查询内容
  - 使用API密钥进行认证
  - 自动从.env文件读取`ANYTHINGLLM_API_KEY`和`ANYTHINGLLM_WORKSPACE_SLUG`配置
  - 智能关键词识别：当用户提到"文档仓库"、"文件仓库"、"仓库"时自动触发查询
  - 支持显示参考来源信息
- 保持与之前版本相同的用户交互体验
- 完整的错误处理机制和超时保护（30秒）

**运行方式**:
```bash
python practice04/chat_client.py
```

**使用说明**:
1. 确保已正确配置.env文件中的AnythingLLM相关配置：
   ```env
   ANYTHINGLLM_API_KEY="your-api-key-here"
   ANYTHINGLLM_WORKSPACE_SLUG="project"  # 默认工作区名称
   ```
2. 确保AnythingLLM服务已在`http://localhost:3001`运行
3. 运行程序后，在终端输入消息与AI对话
4. 当您提到"文档仓库"、"文件仓库"、"仓库"、"文档"、"知识库"等关键词时，系统会自动触发AnythingLLM查询
5. 当聊天达到5轮或上下文超过3k时，系统会自动进行压缩
6. 输入 'quit' 或 'exit' 退出程序

**学习目标**:
- 理解如何使用subprocess模块调用外部命令
- 掌握curl命令在Python中的使用
- 学习如何集成第三方API服务（AnythingLLM）
- 理解环境变量管理和配置读取
- 掌握智能关键词识别和工具触发机制
- 学习如何处理API响应和错误情况
- 理解文档知识库查询的应用场景

### Practice 04.5: 关键信息提取和搜索客户端

**文件位置**: `practice03/chat_client_with_extraction.py`

**功能特点**:
- 基于practice03的聊天记录压缩功能
- 智能关键信息提取：
  - 每5次聊天自动提取关键信息
  - 按照5W规则提取：Who（谁）、What（做什么事）、When（什么时候，可选）、Where（在何处，可选）、Why（为什么，可选）
  - 使用LLM进行智能信息提取
- 聊天历史日志管理：
  - 自动创建日志目录（D:\chat-log\）
  - 将提取的关键信息保存到log.txt文件
  - 支持增量更新，保留历史记录
- 聊天历史搜索功能：
  - 支持"/search"命令触发搜索
  - 支持自然语言搜索请求（如"查找聊天历史"、"搜索历史记录"等）
  - 结合日志内容和用户请求进行智能搜索
- 保持与之前版本相同的用户交互体验
- 完整的错误处理机制

**运行方式**:
```bash
python practice03/chat_client_with_extraction.py
```

**使用说明**:
1. 运行程序后，在终端输入消息与AI对话
2. 正常与AI进行对话，每5次聊天会自动提取关键信息并保存到日志
3. 当聊天达到5轮或上下文超过3k时，系统会自动进行压缩
4. 可以使用以下方式搜索聊天历史：
   - 输入 "/search" 后跟搜索内容
   - 使用自然语言表达搜索意图，如"查找聊天历史"、"搜索历史记录"等
5. 输入 'quit' 或 'exit' 退出程序

**学习目标**:
- 理解关键信息提取的重要性和应用场景
- 掌握5W规则在信息提取中的应用
- 学习如何设计和实现日志管理系统
- 理解搜索功能的实现原理
- 掌握如何结合LLM实现智能搜索
- 学习如何进行增量数据更新和管理

### Practice 05: 技能系统智能体

**文件位置**: `practice05/chat_client.py`

**功能特点**:
- **技能系统**:
  - `list_available_skills()`: 自动读取`.agents/skills`目录下的所有技能
  - `load_skill_content(skill_name)`: 加载指定技能的详细内容
  - 支持YAML front matter解析（提取name和description字段）
  - 技能列表以JSON格式通过system prompt发送给LLM
- **AnythingLLM查询功能**:
  - `anythingllm_query`: 使用subprocess调用curl访问AnythingLLM API
  - 支持查询`http://localhost:3001/api/v1/workspace/{workspace_slug}/chat`接口
- **聊天记录压缩功能**:
  - 自动检测聊天轮次（>=5轮）或上下文长度（>=3000字符）
  - 使用LLM自动总结历史记录
- **智能技能调用**:
  - 自动识别用户请求是否匹配某个技能的描述
  - 匹配成功后自动加载技能内容并添加到system prompt
  - 支持通知撰写技能（notice）示例

**技能目录结构**:
```
.agents/
└── skills/
    └── notice/
        └── SKILL.md  # 技能定义文件，包含YAML front matter和正文
```

**技能文件格式**:
```markdown
---
name: "notice"
description: "用于撰写、修改、润色通知"
---

# 技能正文
...
```

**运行方式**:
```bash
python practice05/chat_client.py
```

**使用说明**:
1. 运行程序后，在终端输入消息与AI对话
2. 系统会自动加载`.agents/skills`目录下的所有技能
3. 当用户请求匹配某个技能的描述时，系统会自动调用该技能
4. 示例技能测试：
   - 输入"帮我写一个五一放假通知"（无部门）→ 输出以"XX部通知"开头
   - 输入"我是销售部的，帮我写一个五一放假通知"（有部门）→ 输出以"销售部通知"开头
5. 聊天超过5轮或上下文超过3k时会自动压缩
6. 输入 'quit' 或 'exit' 退出程序

**学习目标**:
- 理解技能系统的设计原理
- 掌握YAML front matter解析方法
- 学习如何实现技能自动匹配和调用
- 理解如何将技能信息传递给LLM
- 掌握目录遍历和文件读取操作
- 理解技能驱动的智能体架构

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
