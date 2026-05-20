import os
import sys
import time
import json
import http.client
from urllib.parse import urlparse
from datetime import datetime

# ==================== 文件操作工具函数 ====================

def list_files(directory):
    """列出指定目录下的所有文件及其属性"""
    try:
        files = []
        for entry in os.listdir(directory):
            entry_path = os.path.join(directory, entry)
            if os.path.isfile(entry_path):
                stat = os.stat(entry_path)
                files.append({
                    'name': entry,
                    'type': 'file',
                    'size': stat.st_size,
                    'size_human': format_size(stat.st_size),
                    'created_time': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    'modified_time': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'path': entry_path
                })
            elif os.path.isdir(entry_path):
                stat = os.stat(entry_path)
                files.append({
                    'name': entry,
                    'type': 'directory',
                    'size': stat.st_size,
                    'size_human': format_size(stat.st_size),
                    'created_time': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    'modified_time': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'path': entry_path
                })
        return {'success': True, 'data': files}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def format_size(size):
    """将文件大小转换为人类可读格式"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"

def rename_file(directory, old_name, new_name):
    """重命名指定目录下的文件"""
    try:
        old_path = os.path.join(directory, old_name)
        new_path = os.path.join(directory, new_name)
        if not os.path.exists(old_path):
            return {'success': False, 'error': f"文件不存在: {old_path}"}
        os.rename(old_path, new_path)
        return {'success': True, 'message': f"文件已重命名: {old_name} -> {new_name}"}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def delete_file(directory, filename):
    """删除指定目录下的文件"""
    try:
        file_path = os.path.join(directory, filename)
        if not os.path.exists(file_path):
            return {'success': False, 'error': f"文件不存在: {file_path}"}
        if os.path.isfile(file_path):
            os.remove(file_path)
            return {'success': True, 'message': f"文件已删除: {filename}"}
        else:
            return {'success': False, 'error': f"{filename} 不是文件"}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def create_file(directory, filename, content=""):
    """在指定目录下创建新文件并写入内容"""
    try:
        file_path = os.path.join(directory, filename)
        if os.path.exists(file_path):
            return {'success': False, 'error': f"文件已存在: {file_path}"}
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {'success': True, 'message': f"文件已创建: {filename}", 'path': file_path}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def read_file(directory, filename):
    """读取指定目录下文件的内容"""
    try:
        file_path = os.path.join(directory, filename)
        if not os.path.exists(file_path):
            return {'success': False, 'error': f"文件不存在: {file_path}"}
        if not os.path.isfile(file_path):
            return {'success': False, 'error': f"{filename} 不是文件"}
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {'success': True, 'content': content, 'path': file_path}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ==================== 工具调用映射 ====================

TOOL_FUNCTIONS = {
    'list_files': list_files,
    'rename_file': rename_file,
    'delete_file': delete_file,
    'create_file': create_file,
    'read_file': read_file
}

# ==================== 系统提示词 ====================

SYSTEM_PROMPT = """
你是一个文件操作助手，你可以执行以下文件操作：

可用工具：
1. list_files(directory) - 列出指定目录下的所有文件及其属性（名称、类型、大小、创建时间、修改时间）
2. rename_file(directory, old_name, new_name) - 将目录下的old_name文件重命名为new_name
3. delete_file(directory, filename) - 删除目录下的指定文件
4. create_file(directory, filename, content) - 在目录下创建新文件并写入内容
5. read_file(directory, filename) - 读取目录下指定文件的内容

格式要求：
- 当你需要调用工具时，请输出JSON格式的工具调用，格式如下：
{"tool": "工具名称", "args": {"参数名": "参数值"}}

- 如果不需要调用工具，直接回答用户的问题即可

示例：
- 列出目录内容：{"tool": "list_files", "args": {"directory": "/path/to/directory"}}
- 重命名文件：{"tool": "rename_file", "args": {"directory": "/path", "old_name": "old.txt", "new_name": "new.txt"}}
- 删除文件：{"tool": "delete_file", "args": {"directory": "/path", "filename": "file.txt"}}
- 创建文件：{"tool": "create_file", "args": {"directory": "/path", "filename": "new.txt", "content": "Hello World"}}
- 读取文件：{"tool": "read_file", "args": {"directory": "/path", "filename": "file.txt"}}
"""

# ==================== LLM调用函数 ====================

def load_env():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(project_root, '.env')
    
    if not os.path.exists(env_path):
        print(f"错误：未找到.env文件，请在项目根目录创建.env文件")
        print(f"预期路径: {env_path}")
        sys.exit(1)
    
    env_vars = {}
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return env_vars

def estimate_tokens(text):
    return len(text) // 4

def call_llm(base_url, api_key, model, messages, temperature=0.7, max_tokens=1000, stream=False):
    parsed_url = urlparse(base_url)
    host = parsed_url.hostname
    port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
    path = parsed_url.path.rstrip('/') + '/chat/completions'
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    payload = {
        'model': model,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
        'stream': stream
    }
    
    start_time = time.time()
    
    try:
        if parsed_url.scheme == 'https':
            conn = http.client.HTTPSConnection(host, port, timeout=60)
        else:
            conn = http.client.HTTPConnection(host, port, timeout=60)
        
        conn.request('POST', path, json.dumps(payload), headers)
        response = conn.getresponse()
        response_body = response.read().decode('utf-8')
        conn.close()
        
        elapsed_time = time.time() - start_time
        
        if response.status == 200:
            result = json.loads(response_body)
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                
                usage = result.get('usage', {})
                prompt_tokens = usage.get('prompt_tokens', estimate_tokens(json.dumps(messages)))
                completion_tokens = usage.get('completion_tokens', estimate_tokens(content))
                total_tokens = usage.get('total_tokens', prompt_tokens + completion_tokens)
                
                return {
                    'success': True,
                    'content': content,
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'total_tokens': total_tokens,
                    'elapsed_time': elapsed_time
                }
            else:
                return {
                    'success': False,
                    'error': 'No choices in response',
                    'response': response_body,
                    'elapsed_time': elapsed_time
                }
        else:
            return {
                'success': False,
                'error': f"HTTP Error {response.status}",
                'response': response_body,
                'elapsed_time': elapsed_time
            }
    except Exception as e:
        elapsed_time = time.time() - start_time
        return {
            'success': False,
            'error': str(e),
            'elapsed_time': elapsed_time
        }

def parse_tool_call(response):
    """解析LLM响应中的工具调用"""
    try:
        response = response.strip()
        if response.startswith('{') and response.endswith('}'):
            data = json.loads(response)
            if 'tool' in data and 'args' in data:
                return {'tool': data['tool'], 'args': data['args']}
        return None
    except json.JSONDecodeError:
        return None

def execute_tool(tool_name, args):
    """执行工具调用"""
    if tool_name not in TOOL_FUNCTIONS:
        return {'success': False, 'error': f"未知工具: {tool_name}"}
    
    func = TOOL_FUNCTIONS[tool_name]
    try:
        return func(**args)
    except Exception as e:
        return {'success': False, 'error': str(e)}

def main():
    env_vars = load_env()
    
    required_vars = ['BASE_URL', 'MODEL', 'API_KEY']
    missing_vars = [var for var in required_vars if var not in env_vars]
    if missing_vars:
        print(f"错误：.env文件缺少以下必需变量: {', '.join(missing_vars)}")
        sys.exit(1)
    
    base_url = env_vars['BASE_URL']
    model = env_vars['MODEL']
    api_key = env_vars['API_KEY']
    temperature = float(env_vars.get('TEMPERATURE', 0.7))
    max_tokens = int(env_vars.get('MAX_TOKENS', 1000))
    
    print("=" * 70)
    print("LLM 文件操作助手 - 工具调用演示")
    print("=" * 70)
    print(f"API基础URL: {base_url}")
    print(f"模型名称: {model}")
    print(f"温度参数: {temperature}")
    print(f"最大令牌数: {max_tokens}")
    print("=" * 70)
    print("支持的文件操作：")
    print("  1. 列出目录文件")
    print("  2. 重命名文件")
    print("  3. 删除文件")
    print("  4. 创建文件")
    print("  5. 读取文件")
    print("=" * 70)
    
    chat_history = []
    chat_history.append({"role": "system", "content": SYSTEM_PROMPT})
    
    while True:
        print("\n请输入消息（输入 'exit' 或 'quit' 退出）:")
        user_input = input("> ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("感谢使用，再见！")
            break
        
        if not user_input.strip():
            print("请输入有效的消息")
            continue
        
        chat_history.append({"role": "user", "content": user_input})
        
        print("\n正在发送请求...")
        
        result = call_llm(base_url, api_key, model, chat_history, temperature, max_tokens)
        
        print("\n" + "=" * 70)
        print("请求统计报告")
        print("=" * 70)
        
        if result['success']:
            response_content = result['content']
            chat_history.append({"role": "assistant", "content": response_content})
            
            print(f"请求耗时: {result['elapsed_time']:.4f} 秒")
            print(f"输入令牌数 (Prompt): {result['prompt_tokens']}")
            print(f"输出令牌数 (Completion): {result['completion_tokens']}")
            print(f"总令牌数: {result['total_tokens']}")
            
            if result['elapsed_time'] > 0:
                tokens_per_second = result['total_tokens'] / result['elapsed_time']
                print(f"处理速度: {tokens_per_second:.2f} tokens/s")
            
            print("\n" + "=" * 70)
            print("LLM响应")
            print("=" * 70)
            print(response_content)
            
            # 检查是否为工具调用
            tool_call = parse_tool_call(response_content)
            if tool_call:
                print("\n" + "=" * 70)
                print("工具调用执行")
                print("=" * 70)
                print(f"调用工具: {tool_call['tool']}")
                print(f"参数: {json.dumps(tool_call['args'], ensure_ascii=False)}")
                
                tool_result = execute_tool(tool_call['tool'], tool_call['args'])
                print(f"\n执行结果: {json.dumps(tool_result, ensure_ascii=False, indent=2)}")
                
                # 将工具执行结果添加到对话历史
                chat_history.append({"role": "user", "content": f"工具执行结果: {json.dumps(tool_result, ensure_ascii=False)}"})
                
                # 再次调用LLM获取总结回答
                print("\n正在获取总结回答...")
                summary_result = call_llm(base_url, api_key, model, chat_history, temperature, max_tokens)
                
                if summary_result['success']:
                    chat_history.append({"role": "assistant", "content": summary_result['content']})
                    print("\n" + "=" * 70)
                    print("总结回答")
                    print("=" * 70)
                    print(summary_result['content'])
                else:
                    print(f"总结请求失败: {summary_result['error']}")
        else:
            print(f"请求失败: {result['error']}")
            if 'response' in result:
                print(f"响应内容: {result['response']}")
            print(f"耗时: {result['elapsed_time']:.4f} 秒")
        
        print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
