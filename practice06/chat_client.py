import os
import json
import http.client
import ssl
from urllib.parse import urlparse
import sys
from datetime import datetime

def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if not os.path.exists(env_path):
        print(f"错误：{env_path} 文件不存在，请从 env.example 复制并填写正确参数")
        exit(1)

    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

def list_available_skills():
    skills_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.agents', 'skills')
    
    if not os.path.exists(skills_dir) or not os.path.isdir(skills_dir):
        return []
    
    skills = []
    
    for item in os.listdir(skills_dir):
        item_path = os.path.join(skills_dir, item)
        if os.path.isdir(item_path):
            skill_file = os.path.join(item_path, 'SKILL.md')
            if os.path.exists(skill_file):
                try:
                    with open(skill_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if content.startswith('---'):
                        end_index = content.find('\n---\n', 4)
                        if end_index != -1:
                            front_matter = content[4:end_index].strip()
                            lines = front_matter.split('\n')
                            skill_info = {}
                            for line in lines:
                                if ':' in line:
                                    key, value = line.split(':', 1)
                                    skill_info[key.strip()] = value.strip()
                            
                            if 'name' in skill_info:
                                skills.append({
                                    'name': skill_info['name'],
                                    'description': skill_info.get('description', '')
                                })
                except Exception as e:
                    print(f"读取技能文件 {skill_file} 时发生错误: {str(e)}")
    
    return skills

def load_skill_content(skill_name):
    skills_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.agents', 'skills')
    skill_dir = os.path.join(skills_dir, skill_name)
    
    if not os.path.exists(skill_dir) or not os.path.isdir(skill_dir):
        return None
    
    skill_file = os.path.join(skill_dir, 'SKILL.md')
    if not os.path.exists(skill_file):
        return None
    
    try:
        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content.startswith('---'):
            end_index = content.find('\n---\n', 4)
            if end_index != -1:
                return content[end_index + 5:]
        
        return content
    except Exception as e:
        print(f"加载技能内容时发生错误: {str(e)}")
        return None

def get_tools_config():
    return [
        {
            "type": "function",
            "function": {
                "name": "list_directory",
                "description": "列出目录文件",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dir_path": {"type": "string"}
                    },
                    "required": ["dir_path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "读取文件内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dir_path": {"type": "string"},
                        "file_name": {"type": "string"}
                    },
                    "required": ["dir_path", "file_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_file",
                "description": "创建文件",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dir_path": {"type": "string"},
                        "file_name": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["dir_path", "file_name", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "curl",
                "description": "访问网页",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"}
                    },
                    "required": ["url"]
                }
            }
        }
    ]

def call_llm_non_stream(messages, tools=None):
    base_url = os.getenv('BASE_URL')
    model = os.getenv('MODEL')
    api_key = os.getenv('API_KEY')

    if not all([base_url, model, api_key]):
        print("错误：请在.env文件中配置BASE_URL、MODEL和API_KEY")
        exit(1)

    parsed_url = urlparse(base_url)
    host = parsed_url.netloc
    path = parsed_url.path.rstrip('/') + '/chat/completions'
    protocol = parsed_url.scheme

    data = {
        "model": model,
        "messages": messages,
        "temperature": float(os.getenv('TEMPERATURE', '0.7')),
        "max_tokens": int(os.getenv('MAX_TOKENS', '8192')),
        "stream": False
    }

    if tools:
        data["tools"] = tools
        data["tool_choice"] = "auto"

    if protocol == 'https':
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        conn = http.client.HTTPSConnection(host, context=context)
    else:
        conn = http.client.HTTPConnection(host)

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    try:
        conn.request('POST', path, json.dumps(data), headers)
        response = conn.getresponse()

        if response.status != 200:
            try:
                error_content = response.read().decode()
                print(f"API错误: HTTP状态码 {response.status}")
                print(f"错误内容: {error_content[:500]}")
                try:
                    error_data = json.loads(error_content)
                    if isinstance(error_data, dict):
                        error_info = error_data.get('error', {})
                        if isinstance(error_info, dict):
                            print(f"API错误信息: {error_info.get('message', '未知错误')}")
                        else:
                            print(f"API错误信息: {error_info}")
                except json.JSONDecodeError:
                    pass
            except Exception as e:
                print(f"读取错误响应时发生错误: {str(e)}")
            return None

        raw_response = response.read().decode()
        print(f"[LLM调试] 原始响应: {raw_response[:500]}...")

        response_data = json.loads(raw_response)

        if not isinstance(response_data, dict):
            print(f"API错误: 响应数据不是字典格式")
            return None

        if 'choices' not in response_data or not isinstance(response_data['choices'], list) or len(response_data['choices']) == 0:
            print(f"API错误: 响应数据中没有有效的choices")
            return None

        choice = response_data['choices'][0]
        if not isinstance(choice, dict):
            print(f"API错误: choice不是字典格式: {type(choice)}")
            return None

        message = choice.get('message', {})
        if not isinstance(message, dict):
            print(f"API错误: message不是字典格式: {type(message)}")
            return None

        content = message.get('content', '')
        tool_calls = message.get('tool_calls', None)

        return {"content": content, "tool_calls": tool_calls}

    except json.JSONDecodeError as e:
        print(f"解析JSON响应时发生错误: {str(e)}")
        return None
    except Exception as e:
        print(f"调用LLM时发生错误: {str(e)}")
        return None
    finally:
        conn.close()

def list_directory(dir_path):
    try:
        if not os.path.isdir(dir_path):
            return f"错误：{dir_path} 不是有效的目录路径"

        files_info = []
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            item_stat = os.stat(item_path)

            if os.path.isdir(item_path):
                item_type = "目录"
            else:
                item_type = "文件"

            size = item_stat.st_size
            if size < 1024:
                size_str = f"{size} 字节"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.2f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.2f} MB"

            modify_time = datetime.fromtimestamp(item_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

            files_info.append({
                "名称": item,
                "类型": item_type,
                "大小": size_str,
                "修改时间": modify_time
            })

        return json.dumps(files_info, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"列出目录时发生错误: {str(e)}"

def rename_file(dir_path, old_name, new_name):
    try:
        old_path = os.path.join(dir_path, old_name)
        new_path = os.path.join(dir_path, new_name)

        if not os.path.exists(old_path):
            return f"错误：文件 {old_path} 不存在"

        if os.path.exists(new_path):
            return f"错误：文件 {new_path} 已存在"

        os.rename(old_path, new_path)
        return f"成功：文件已从 {old_name} 重命名为 {new_name}"
    except Exception as e:
        return f"重命名文件时发生错误: {str(e)}"

def delete_file(dir_path, file_name):
    try:
        file_path = os.path.join(dir_path, file_name)

        if not os.path.exists(file_path):
            return f"错误：文件 {file_path} 不存在"

        os.remove(file_path)
        return f"成功：文件 {file_name} 已删除"
    except Exception as e:
        return f"删除文件时发生错误: {str(e)}"

def create_file(dir_path, file_name, content):
    try:
        file_path = os.path.join(dir_path, file_name)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"成功：文件 {file_name} 已创建并写入内容"
    except Exception as e:
        return f"创建文件时发生错误: {str(e)}"

def read_file(dir_path, file_name):
    try:
        file_path = os.path.join(dir_path, file_name)

        if not os.path.exists(file_path):
            return f"错误：文件 {file_path} 不存在"

        if not os.path.isfile(file_path):
            return f"错误：{file_path} 不是一个文件"

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return content
    except Exception as e:
        return f"读取文件时发生错误: {str(e)}"

def curl(url):
    try:
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url

        parsed_url = urlparse(url)
        host = parsed_url.netloc
        path = parsed_url.path or '/'

        import urllib.parse
        path = urllib.parse.quote(path, safe='/')

        protocol = parsed_url.scheme

        if protocol == 'https':
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            conn = http.client.HTTPSConnection(host, context=context)
        else:
            conn = http.client.HTTPConnection(host)

        if host == 'wttr.in':
            ascii_result = ""
            json_result = ""

            conn.request('GET', path)
            response = conn.getresponse()
            if response.status == 200:
                ascii_result = response.read().decode('utf-8', errors='ignore')

            conn.close()

            json_path = path + '?format=j1'
            conn = http.client.HTTPSConnection(host, context=context) if protocol == 'https' else http.client.HTTPConnection(host)
            conn.request('GET', json_path)
            response = conn.getresponse()
            if response.status == 200:
                json_content = response.read().decode('utf-8', errors='ignore')
                try:
                    data = json.loads(json_content)
                    if 'weather' in data and len(data['weather']) > 0:
                        today = data['weather'][0]
                        json_result = f"\n📍 详细温度信息:\n"
                        json_result += f"📍 {data['nearest_area'][0]['areaName'][0]['value']}\n"
                        json_result += f"\n📅 今日 ({today['date']}):\n"
                        json_result += f"  🌡️ 最高气温: {today['maxtempC']}°C\n"
                        json_result += f"  🌡️ 最低气温: {today['mintempC']}°C\n"
                        json_result += f"  🌡️ 平均气温: {today['avgtempC']}°C\n"
                        json_result += f"  ☁️ {today['hourly'][0]['weatherDesc'][0]['value']}\n"
                        if len(data['weather']) > 1:
                            tomorrow = data['weather'][1]
                            json_result += f"\n📅 明日 ({tomorrow['date']}):\n"
                            json_result += f"  🌡️ 最高气温: {tomorrow['maxtempC']}°C\n"
                            json_result += f"  🌡️ 最低气温: {tomorrow['mintempC']}°C\n"
                            json_result += f"  🌡️ 平均气温: {tomorrow['avgtempC']}°C\n"
                            json_result += f"  ☁️ {tomorrow['hourly'][0]['weatherDesc'][0]['value']}\n"
                except json.JSONDecodeError:
                    pass

            conn.close()
            return ascii_result + json_result
        else:
            conn.request('GET', path)
            response = conn.getresponse()

            if response.status == 200:
                content = response.read().decode('utf-8', errors='ignore')
                return content
            else:
                return f"错误：HTTP请求失败，状态码: {response.status}"
    except Exception as e:
        return f"访问网页时发生错误: {str(e)}"
    finally:
        try:
            conn.close()
        except:
            pass

LOG_FILE_PATH = r"D:\chat-log\log.txt"

def search_chat_history(user_question):
    try:
        if not os.path.exists(LOG_FILE_PATH):
            return "聊天历史记录文件不存在，请先进行一些对话。"

        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            return "聊天历史记录为空，请先进行一些对话。"

        try:
            chat_log = json.loads(content)
        except json.JSONDecodeError:
            return "聊天历史记录格式错误，无法搜索。"

        if not isinstance(chat_log, list) or len(chat_log) == 0:
            return "聊天历史记录为空，请先进行一些对话。"

        chat_log_text = ""
        for entry in chat_log:
            who = entry.get('Who', '未知')
            what = entry.get('What', '')
            time = entry.get('时间', '')

            line = f"【{time}】{who}: {what}"
            chat_log_text += line + "\n"

        search_prompt = [
            {
                "role": "system",
                "content": "你是一个聊天历史搜索助手。用户会提供一个聊天历史记录和当前问题，你需要根据聊天历史记录回答用户的问题。如果聊天历史中有相关信息，请基于历史记录给出准确回答；如果没有相关信息，请明确告知用户。"
            },
            {
                "role": "user",
                "content": f"【聊天历史记录】\n{chat_log_text}\n\n【用户当前问题】\n{user_question}"
            }
        ]

        result = call_llm_non_stream(search_prompt)
        if result:
            return result.get('content', '搜索过程中发生错误。')
        return "搜索聊天历史时发生错误。"
    except Exception as e:
        return f"搜索聊天历史时发生错误: {str(e)}"

def anythingllm_query(message):
    import subprocess

    api_key = os.getenv('ANYTHINGLLM_API_KEY')
    workspace_slug = os.getenv('ANYTHINGLLM_WORKSPACE_SLUG')

    if not api_key:
        return "错误：未配置ANYTHINGLLM_API_KEY环境变量"
    if not workspace_slug:
        return "错误：未配置ANYTHINGLLM_WORKSPACE_SLUG环境变量"

    url = "http://localhost:3001/api/v1/workspace/assistant-chats/chat"

    curl_cmd = [
        'curl', '-X', 'POST',
        url,
        '-H', f'Authorization: Bearer {api_key}',
        '-H', 'Content-Type: application/json',
        '-d', f'{{"message": "{message}"}}',
        '--max-time', '30'
    ]

    try:
        result = subprocess.run(
            curl_cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=35
        )

        if result.returncode != 0:
            return f"错误：curl命令执行失败 (返回码: {result.returncode})\n{result.stderr}"

        response_text = result.stdout.strip()

        if not response_text:
            return "错误：API返回了空响应"

        try:
            response_data = json.loads(response_text)

            if isinstance(response_data, dict):
                if response_data.get('error'):
                    return f"API错误：{response_data.get('error')}"
                if response_data.get('text'):
                    return response_data.get('text')
                if response_data.get('response'):
                    return response_data.get('response')
                if response_data.get('message'):
                    return response_data.get('message')

            return response_text

        except json.JSONDecodeError:
            return response_text

    except subprocess.TimeoutExpired:
        return "错误：API请求超时（超过30秒）"
    except Exception as e:
        return f"查询AnythingLLM时发生错误: {str(e)}"

def execute_tool(tool_name, arguments):
    if tool_name == "load_skill_content":
        return load_skill_content(arguments.get("skill_name", ""))
    elif tool_name == "list_directory":
        return list_directory(arguments.get("dir_path", ""))
    elif tool_name == "rename_file":
        return rename_file(arguments.get("dir_path", ""), arguments.get("old_name", ""), arguments.get("new_name", ""))
    elif tool_name == "delete_file":
        return delete_file(arguments.get("dir_path", ""), arguments.get("file_name", ""))
    elif tool_name == "create_file":
        return create_file(arguments.get("dir_path", ""), arguments.get("file_name", ""), arguments.get("content", ""))
    elif tool_name == "read_file":
        return read_file(arguments.get("dir_path", ""), arguments.get("file_name", ""))
    elif tool_name == "curl":
        return curl(arguments.get("url", ""))
    elif tool_name == "search_chat_history":
        return search_chat_history(arguments.get("user_question", ""))
    elif tool_name == "anythingllm_query":
        return anythingllm_query(arguments.get("message", ""))
    else:
        return f"未知工具: {tool_name}"


class ChainedCallContext:
    def __init__(self, max_iterations=10):
        self.max_iterations = max_iterations
        self.steps = []
        self.variables = {}
        self.current_iteration = 0

    def add_step(self, tool_name, arguments, result):
        self.steps.append({
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result
        })
        self.current_iteration += 1

    def set_variable(self, key, value):
        self.variables[key] = value

    def get_variable(self, key, default=None):
        return self.variables.get(key, default)

    def get_steps_history(self):
        return self.steps

    def is_max_iterations_reached(self):
        return self.current_iteration >= self.max_iterations

    def reset(self):
        self.steps = []
        self.variables = {}
        self.current_iteration = 0


def get_chained_system_prompt():
    return """你是工具调用助手。必须通过调用工具完成任务，不能凭空回答。写入文件必须调用create_file工具。

可用工具：
- list_directory(dir_path): 列出目录文件
- read_file(dir_path, file_name): 读取文件内容
- create_file(dir_path, file_name, content): 创建/写入文件
- curl(url): 获取网页内容

输出格式：仅JSON。例如：
{"done":true,"answer":"完成"}
{"done":false,"tool_call":{"name":"read_file","arguments":{"dir_path":"demo","file_name":"1.txt"}}}"""


def build_analysis_prompt(user_request, steps_history, variables):
    history_text = ""
    if steps_history:
        history_text = "\n已执行:"
        recent_steps = steps_history[-3:]
        for i, step in enumerate(recent_steps, 1):
            args_str = json.dumps(step['arguments'], ensure_ascii=False)
            history_text += f" [{step['tool_name']}({args_str[:50]})]"
    
    variables_text = ""
    if variables:
        variables_text = "\n变量:"
        for key, value in variables.items():
            val_str = str(value)
            variables_text += f" {key}={val_str[:30]}..." if len(val_str) > 30 else f" {key}={val_str}"

    prompt = f"请求:{user_request}{history_text}{variables_text}\n下一步？仅输出JSON:"

    return prompt


def parse_llm_response(response):
    if response is None:
        print("[解析错误] LLM响应为None")
        return None, None

    content = response.get("content", "")
    tool_calls = response.get("tool_calls", None)

    if tool_calls and isinstance(tool_calls, list) and len(tool_calls) > 0:
        tool_call = tool_calls[0]
        tool_name = tool_call.get('function', {}).get('name')
        arguments = tool_call.get('function', {}).get('arguments', {})

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                print(f"[解析错误] 无法解析工具参数: {arguments}")
                arguments = {}

        print(f"[解析成功] tool_calls格式: {tool_name}({arguments})")
        return False, {"name": tool_name, "arguments": arguments}

    if content:
        json_content = content.strip()
        original_content = json_content

        if json_content.startswith('```json'):
            json_content = json_content.split('```json')[1].split('```')[0].strip()
        elif json_content.startswith('```'):
            json_content = json_content.split('```')[1].strip()

        json_content = json_content.strip()

        try:
            decision = json.loads(json_content)

            if decision.get("done") is True:
                answer = decision.get("answer", "")
                print(f"[解析成功] done=true，回答: {answer[:100]}..." if len(answer) > 100 else f"[解析成功] done=true，回答: {answer}")
                return True, answer

            if decision.get("done") is False:
                tool_call = decision.get("tool_call", {})
                if tool_call and isinstance(tool_call, dict) and "name" in tool_call:
                    print(f"[解析成功] done=false，调用工具: {tool_call.get('name')}")
                    return False, tool_call

        except json.JSONDecodeError as e:
            print(f"[解析错误] JSON解析失败: {str(e)}")
            print(f"[解析错误] 原始内容: {original_content[:200]}...")
            
            # 尝试修复不完整的JSON（缺少结尾括号、引号或转义问题）
            try:
                import re
                fixed_content = json_content
                
                # 处理路径末尾反斜杠转义引号的问题
                # 模式: "dir_path":"d:\demo\", -> "dir_path":"d:\demo",
                # 在正则表达式中，\\ 表示匹配单个反斜杠
                fixed_content = re.sub(r'"(dir_path|file_name|url)":\s*"([^"]*?)\\",', r'"\1": "\2",', fixed_content)
                fixed_content = re.sub(r'"(dir_path|file_name|url)":\s*"([^"]*?)\\\s*}', r'"\1": "\2"}', fixed_content)
                
                # 处理路径转义问题：将 \\\\" 替换为 \\（Windows路径）
                fixed_content = fixed_content.replace('\\\\\\\\', '\\\\')
                
                # 修复路径末尾反斜杠转义引号的问题（处理未转义的情况）
                fixed_content = re.sub(r'"([^"]+?)\\\\",', r'"\1",', fixed_content)
                fixed_content = re.sub(r'"([^"]+?)\\\\\s*([,\}])', r'"\1"\2', fixed_content)
                
                # 移除末尾可能的多余字符
                fixed_content = fixed_content.rstrip(', \t\n\r')
                
                # 计算括号匹配
                open_braces = fixed_content.count('{')
                close_braces = fixed_content.count('}')
                open_brackets = fixed_content.count('[')
                close_brackets = fixed_content.count(']')
                
                # 添加缺少的括号
                fixed_content += '}' * (open_braces - close_braces)
                fixed_content += ']' * (open_brackets - close_brackets)
                
                if fixed_content != json_content:
                    print(f"[解析尝试] 修复JSON: 转义处理 + 添加 {open_braces - close_braces} 个 }} 和 {open_brackets - close_brackets} 个 ]")
                
                decision = json.loads(fixed_content)
                    
                if decision.get("done") is True:
                    answer = decision.get("answer", "")
                    print(f"[解析成功] done=true，回答: {answer[:100]}..." if len(answer) > 100 else f"[解析成功] done=true，回答: {answer}")
                    return True, answer

                if decision.get("done") is False:
                    tool_call = decision.get("tool_call", {})
                    if tool_call and isinstance(tool_call, dict) and "name" in tool_call:
                        print(f"[解析成功] done=false，调用工具: {tool_call.get('name')}")
                        return False, tool_call
            except json.JSONDecodeError as e2:
                print(f"[解析错误] 修复后仍然解析失败: {str(e2)}")

    print(f"[解析错误] 无法解析响应: content={content[:200]}..., tool_calls={tool_calls}")
    return None, None


def execute_chained_tool_call(user_request, max_iterations=10):
    context = ChainedCallContext(max_iterations=max_iterations)

    system_prompt = get_chained_system_prompt()

    print(f"\n{'='*60}")
    print(f"开始链式工具调用")
    print(f"用户请求: {user_request}")
    print(f"最大迭代次数: {max_iterations}")
    print(f"{'='*60}\n")

    for iteration in range(max_iterations):
        print(f"[迭代 {iteration + 1}/{max_iterations}]")

        analysis_prompt = build_analysis_prompt(
            user_request,
            context.get_steps_history(),
            context.variables
        )

        # 每次迭代只发送必要的消息，不累积历史
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": analysis_prompt}
        ]

        print(f"[调试] 当前消息数量: {len(messages)}")

        print(f"[调试] 调用LLM...")
        try:
            response = call_llm_non_stream(messages, None)
            print(f"[调试] LLM响应: {response}")
        except Exception as e:
            print(f"[错误] LLM调用异常: {str(e)}")
            response = None

        done, result = parse_llm_response(response)

        if done is None:
            print(f"[警告] 无法解析LLM响应，尝试继续...")
            continue

        if done:
            # 检查任务是否真正完成
            steps = context.get_steps_history()
            read_count = sum(1 for s in steps if s['tool_name'] == 'read_file')
            create_count = sum(1 for s in steps if s['tool_name'] == 'create_file')
            
            # 如果用户请求涉及写入文件但未调用create_file，则拒绝完成
            if '写入' in user_request or 'create_file' in user_request.lower():
                if create_count == 0:
                    print(f"[警告] LLM声称任务完成，但未调用create_file工具！强制继续...")
                    continue
            
            # 如果用户请求涉及读取多个文件但未全部读取，则拒绝完成
            if ('读取' in user_request and ('和' in user_request or '两个' in user_request)):
                if read_count < 2:
                    print(f"[警告] LLM声称任务完成，但只读取了{read_count}个文件！强制继续...")
                    continue
            
            print(f"[完成] 任务完成")
            print(f"最终回答: {result}")
            return result

        if isinstance(result, dict) and "name" in result:
            tool_name = result.get("name")
            tool_arguments = result.get("arguments", {})

            print(f"决定调用工具: {tool_name}")
            print(f"参数: {json.dumps(tool_arguments, ensure_ascii=False)}")

            try:
                tool_result = execute_tool(tool_name, tool_arguments)
                print(f"工具返回: {tool_result[:200]}..." if len(str(tool_result)) > 200 else f"工具返回: {tool_result}")

                context.add_step(tool_name, tool_arguments, tool_result)

                if tool_name == "list_directory":
                    try:
                        files = json.loads(tool_result)
                        if isinstance(files, list):
                            file_list = [f["名称"] for f in files if f.get("类型") == "文件"]
                            context.set_variable("file_list", file_list)
                            context.set_variable("files_json", tool_result)
                    except:
                        pass

                elif tool_name == "read_file":
                    context.set_variable(f"file_content_{tool_arguments.get('file_name', 'unknown')}", tool_result)

                elif tool_name == "curl":
                    context.set_variable("web_content", tool_result)

            except Exception as e:
                error_msg = f"工具执行异常: {str(e)}"
                print(f"[错误] {error_msg}")
                messages.append({
                    "role": "assistant",
                    "content": json.dumps({"done": False, "tool_call": {"name": tool_name, "arguments": tool_arguments}}, ensure_ascii=False)
                })
                messages.append({
                    "role": "tool",
                    "content": error_msg,
                    "name": tool_name
                })
        else:
            print(f"[警告] 无效的决策结果: {result}")

    print(f"\n[警告] 达到最大迭代次数 {max_iterations}，停止执行")
    return "抱歉，由于达到最大迭代次数，任务未能完成。请简化您的请求或减少操作步骤。"


def main():
    load_env()

    print("=== LLM 链式工具调用客户端 ===")
    print("输入消息开始聊天，按 Ctrl+C 退出")
    print("功能：支持链式工具调用，前一个工具的输出可作为后一个工具的输入")
    print("==========================================\n")

    try:
        while True:
            user_input = input("你: ")

            if user_input.lower() in ['exit', 'quit', '退出']:
                print("退出聊天客户端")
                break

            result = execute_chained_tool_call(user_input, max_iterations=10)
            print(f"\n最终结果: {result}\n")

    except KeyboardInterrupt:
        print("\n退出聊天客户端")
        sys.exit(0)

if __name__ == "__main__":
    main()