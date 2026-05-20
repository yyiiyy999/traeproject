import os
import sys
import time
import json
import http.client
import subprocess
from urllib.parse import urlparse
from datetime import datetime

# ==================== 网络访问工具函数 ====================

def fetch_webpage(url):
    """通过curl访问网页并返回网页内容"""
    try:
        result = subprocess.run(
            ['curl', '-s', '-L', url],
            capture_output=True,
            timeout=30
        )
        if result.returncode == 0:
            try:
                content = result.stdout.decode('utf-8')
            except UnicodeDecodeError:
                content = result.stdout.decode('gbk', errors='replace')
            return {'success': True, 'content': content}
        else:
            try:
                error_msg = result.stderr.decode('utf-8')
            except UnicodeDecodeError:
                error_msg = result.stderr.decode('gbk', errors='replace')
            return {'success': False, 'error': f"curl执行失败: {error_msg}"}
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': '请求超时'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_current_date():
    """获取当前日期和时间"""
    now = datetime.now()
    return {
        'success': True,
        'content': now.strftime('%Y-%m-%d %H:%M:%S'),
        'date': now.strftime('%Y-%m-%d'),
        'time': now.strftime('%H:%M:%S')
    }

# ==================== 工具调用映射 ====================

TOOL_FUNCTIONS = {
    'fetch_webpage': fetch_webpage,
    'get_current_date': get_current_date
}

# ==================== 系统提示词 ====================

def get_system_prompt():
    """生成包含当前日期的系统提示词"""
    current_date = datetime.now().strftime('%Y-%m-%d')
    return f"""
你是一个网络访问助手，可以获取网页内容和天气预报信息。

当前日期: {current_date}

可用工具：
1. fetch_webpage(url) - 通过curl访问网页并返回网页内容
2. get_current_date() - 获取当前日期和时间

格式要求：
- 当你需要调用工具时，请输出JSON格式的工具调用，格式如下：
{{"tool": "工具名称", "args": {{"参数名": "参数值"}}}}

- 如果不需要调用工具，直接回答用户的问题即可

示例：
- 获取网页内容：{{"tool": "fetch_webpage", "args": {{"url": "https://example.com"}}}}
- 获取天气预报：{{"tool": "fetch_webpage", "args": {{"url": "https://wttr.in/城市名"}}}}
- 获取当前日期：{{"tool": "get_current_date", "args": {{}}}}

使用说明：
- 要获取天气预报，请使用 https://wttr.in/城市名 格式，例如：https://wttr.in/北京
- 天气数据返回后，请用自然、友好的语言总结给用户
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

# ==================== 聊天记录压缩功能 ====================

def calculate_context_length(chat_history):
    """计算聊天上下文的总字符长度"""
    total_length = 0
    for message in chat_history:
        if 'content' in message:
            total_length += len(message['content'])
    return total_length

def count_chat_rounds(chat_history):
    """计算对话轮次（排除system消息和工具调用结果）"""
    rounds = 0
    for message in chat_history:
        if message.get('role') == 'user':
            rounds += 1
    return rounds

def should_compress(chat_history, max_rounds=5, max_length=3000):
    """检查是否需要进行聊天记录压缩"""
    rounds = count_chat_rounds(chat_history)
    length = calculate_context_length(chat_history)
    return rounds >= max_rounds or length >= max_length

def summarize_chat_history(base_url, api_key, model, chat_history):
    """使用LLM对聊天记录进行总结"""
    # 过滤掉system消息和工具调用结果，只保留用户和助手的对话
    conversation = []
    for message in chat_history:
        role = message.get('role')
        if role == 'user' or role == 'assistant':
            conversation.append({
                'role': role,
                'content': message['content']
            })
    
    if not conversation:
        return None
    
    # 计算分割点：前70%压缩，后30%保留
    total_messages = len(conversation)
    split_index = int(total_messages * 0.7)
    
    # 需要总结的部分（前70%）
    messages_to_summarize = conversation[:split_index]
    # 需要保留的部分（后30%）
    messages_to_keep = conversation[split_index:]
    
    if not messages_to_summarize:
        return None
    
    # 构建总结请求
    summary_prompt = f"""
请对以下对话历史进行简明扼要的总结：

{json.dumps(messages_to_summarize, ensure_ascii=False, indent=2)}

请用中文进行总结，保持关键信息完整，语言简洁。
"""
    
    summary_messages = [
        {"role": "system", "content": "你是一个专业的对话总结助手，请对用户提供的对话历史进行准确、简洁的总结。"},
        {"role": "user", "content": summary_prompt}
    ]
    
    print("\n" + "=" * 70)
    print("正在执行聊天记录压缩...")
    print(f"总对话轮次: {total_messages}")
    print(f"需要总结的消息数: {len(messages_to_summarize)}")
    print(f"保留的消息数: {len(messages_to_keep)}")
    print("=" * 70)
    
    result = call_llm(base_url, api_key, model, summary_messages, temperature=0.3, max_tokens=500)
    
    if result['success']:
        summary = result['content']
        print(f"\n总结内容:\n{summary}")
        print("\n" + "=" * 70)
        
        # 修复：将总结改为user角色消息，避免模板校验失败
        compressed_history = [
            {"role": "system", "content": get_system_prompt()},
            {"role": "user", "content": f"【历史对话总结】\n{summary}\n\n--- 以下为最近对话 ---"}
        ]
        
        # 添加保留的消息
        compressed_history.extend(messages_to_keep)
        
        return compressed_history
    else:
        print(f"总结失败: {result['error']}")
        return None

# ==================== 主程序 ====================

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
    print("LLM 聊天记录压缩助手")
    print("=" * 70)
    print(f"API基础URL: {base_url}")
    print(f"模型名称: {model}")
    print(f"温度参数: {temperature}")
    print(f"最大令牌数: {max_tokens}")
    print("=" * 70)
    print("支持的网络操作：")
    print("  1. 获取网页内容")
    print("  2. 获取天气预报 (使用 wttr.in)")
    print("  3. 获取当前日期和时间")
    print("=" * 70)
    print("智能压缩功能：")
    print("  - 聊天超过5轮自动触发压缩")
    print("  - 上下文超过3000字符自动触发压缩")
    print("  - 前70%内容总结压缩，后30%保留原文")
    print("=" * 70)
    
    chat_history = []
    chat_history.append({"role": "system", "content": get_system_prompt()})
    
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
        
        # 检查是否需要压缩
        if should_compress(chat_history):
            # 先保存最新的用户消息
            latest_user_message = chat_history.pop()
            # 对剩余历史进行压缩
            compressed_history = summarize_chat_history(base_url, api_key, model, chat_history)
            if compressed_history:
                chat_history = compressed_history
                print("聊天记录已成功压缩！")
            # 将最新的用户消息重新添加回去
            chat_history.append(latest_user_message)
        
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
            print(f"当前对话轮次: {count_chat_rounds(chat_history)}")
            print(f"当前上下文长度: {calculate_context_length(chat_history)} 字符")
            
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