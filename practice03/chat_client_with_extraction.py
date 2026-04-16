import os
import json
import time
import sys
from http.client import HTTPSConnection, HTTPConnection
from urllib.parse import urlparse

def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"')
    return env_vars

def calculate_context_length(conversation_history):
    total_length = 0
    for message in conversation_history:
        total_length += len(message.get('content', ''))
    return total_length

def summarize_conversation(base_url, model, api_key, messages_to_summarize):
    prompt = "请总结以下对话内容，保留关键信息：\n\n"
    
    total_chars = 0
    max_chars = 1500
    
    for msg in messages_to_summarize:
        role = msg.get('role', '')
        content = msg.get('content', '')
        
        if total_chars + len(content) > max_chars:
            remaining = max_chars - total_chars
            if remaining > 0:
                content = content[:remaining]
                prompt += f"{role}: {content}...\n"
            break
        
        prompt += f"{role}: {content}\n"
        total_chars += len(content)
    
    parsed_url = urlparse(base_url)
    host = parsed_url.netloc
    path = parsed_url.path or '/'
    if not path.endswith('/'):
        path += '/'
    path += 'chat/completions'
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    if parsed_url.scheme == 'https':
        conn = HTTPSConnection(host)
    else:
        conn = HTTPConnection(host)
    
    conn.request(
        "POST",
        path,
        body=json.dumps(data),
        headers=headers
    )
    
    response = conn.getresponse()
    response_data = response.read().decode('utf-8')
    conn.close()
    
    try:
        result = json.loads(response_data)
        if 'error' in result:
            return None, f"Error: {result['error']['message']}"
        
        if 'choices' not in result or len(result['choices']) == 0:
            return None, f"Error: No choices in response: {response_data[:200]}"
        
        if 'message' not in result['choices'][0]:
            return None, f"Error: No message in choice: {str(result['choices'][0])[:200]}"
        
        content = result['choices'][0]['message']['content']
        return content, None
    except Exception as e:
        return None, f"Error parsing response: {str(e)}, response: {response_data[:200]}"

def check_and_summarize(conversation_history, base_url, model, api_key, max_rounds=5, max_length=3000):
    if len(conversation_history) < max_rounds:
        return conversation_history, False
    
    context_length = calculate_context_length(conversation_history)
    if context_length < max_length:
        return conversation_history, False
    
    print(f"\n[系统提示] 检测到对话历史过长（{len(conversation_history)}轮，{context_length}字符），正在压缩...")
    
    split_point = int(len(conversation_history) * 0.7)
    messages_to_summarize = conversation_history[:split_point]
    messages_to_keep = conversation_history[split_point:]
    
    summary, error = summarize_conversation(base_url, model, api_key, messages_to_summarize)
    
    if error:
        print(f"[错误] 总结失败: {error}")
        return conversation_history, False
    
    print(f"[系统提示] 对话历史已压缩")
    
    new_history = [
        {"role": "system", "content": f"以下是之前对话的总结：{summary}"}
    ]
    new_history.extend(messages_to_keep)
    
    return new_history, True

def extract_key_information(base_url, model, api_key, messages_to_extract):
    prompt = "请从以下对话中提取关键信息，按照5W规则（Who、What、When、Where、Why）提取，每条信息单独一行：\n\n"
    
    for msg in messages_to_extract:
        role = msg.get('role', '')
        content = msg.get('content', '')
        prompt += f"{role}: {content}\n"
    
    parsed_url = urlparse(base_url)
    host = parsed_url.netloc
    path = parsed_url.path or '/'
    if not path.endswith('/'):
        path += '/'
    path += 'chat/completions'
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    if parsed_url.scheme == 'https':
        conn = HTTPSConnection(host)
    else:
        conn = HTTPConnection(host)
    
    conn.request(
        "POST",
        path,
        body=json.dumps(data),
        headers=headers
    )
    
    response = conn.getresponse()
    response_data = response.read().decode('utf-8')
    conn.close()
    
    try:
        result = json.loads(response_data)
        if 'error' in result:
            return None, f"Error: {result['error']['message']}"
        
        if 'choices' not in result or len(result['choices']) == 0:
            return None, f"Error: No choices in response: {response_data[:200]}"
        
        if 'message' not in result['choices'][0]:
            return None, f"Error: No message in choice: {str(result['choices'][0])[:200]}"
        
        content = result['choices'][0]['message']['content']
        return content, None
    except Exception as e:
        return None, f"Error parsing response: {str(e)}, response: {response_data[:200]}"

def save_key_information(key_info):
    log_dir = "D:\\aaalaoda\\university\\2.2\\Ai\\traeproject\\practice03\\chat-log"
    log_file = os.path.join(log_dir, "log.txt")
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"[系统提示] 创建了目录: {log_dir}")
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n=== {timestamp} ===\n")
        f.write(key_info)
        f.write("\n")
    
    print(f"[系统提示] 关键信息已保存到: {log_file}")

def check_and_extract_key_info(conversation_history, base_url, model, api_key, extraction_interval=5):
    if len(conversation_history) % extraction_interval != 0:
        return False
    
    print(f"\n[系统提示] 每{extraction_interval}轮对话，正在提取关键信息...")
    
    messages_to_extract = conversation_history[-extraction_interval:]
    key_info, error = extract_key_information(base_url, model, api_key, messages_to_extract)
    
    if error:
        print(f"[错误] 提取关键信息失败: {error}")
        return False
    
    save_key_information(key_info)
    print("[系统提示] 关键信息提取完成")
    return True

def search_chat_history(user_query, base_url, model, api_key):
    log_dir = "D:\\chat-log"
    log_file = os.path.join(log_dir, "log.txt")
    
    if not os.path.exists(log_file):
        return "[错误] 聊天记录文件不存在，没有可搜索的内容。"
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            chat_log = f.read()
    except Exception as e:
        return f"[错误] 读取聊天记录失败: {str(e)}"
    
    prompt = f"请根据以下聊天记录和用户查询，提供相关的回答：\n\n"
    prompt += f"聊天记录：\n{chat_log}\n\n"
    prompt += f"用户查询：{user_query}\n"
    
    parsed_url = urlparse(base_url)
    host = parsed_url.netloc
    path = parsed_url.path or '/'
    if not path.endswith('/'):
        path += '/'
    path += 'chat/completions'
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    if parsed_url.scheme == 'https':
        conn = HTTPSConnection(host)
    else:
        conn = HTTPConnection(host)
    
    conn.request(
        "POST",
        path,
        body=json.dumps(data),
        headers=headers
    )
    
    response = conn.getresponse()
    response_data = response.read().decode('utf-8')
    conn.close()
    
    try:
        result = json.loads(response_data)
        if 'error' in result:
            return f"[错误] 搜索失败: {result['error']['message']}"
        
        if 'choices' not in result or len(result['choices']) == 0:
            return "[错误] 搜索失败: 无返回结果"
        
        if 'message' not in result['choices'][0]:
            return "[错误] 搜索失败: 无效的返回格式"
        
        content = result['choices'][0]['message']['content']
        return content
    except Exception as e:
        return f"[错误] 搜索失败: {str(e)}"

def should_search_chat_history(user_input):
    user_input_lower = user_input.lower()
    
    if user_input_lower.startswith('/search'):
        return True
    
    search_keywords = [
        "查找聊天历史", "搜索聊天记录", "聊天记录", "历史消息",
        "之前的对话", "之前说的", "之前聊的", "查找历史",
        "之前聊了什么", "之前说了什么", "历史记录"
    ]
    
    for keyword in search_keywords:
        if keyword in user_input_lower:
            return True
    
    return False

def stream_llm_response(base_url, model, api_key, messages, max_tokens=500):
    parsed_url = urlparse(base_url)
    host = parsed_url.netloc
    path = parsed_url.path or '/'
    if not path.endswith('/'):
        path += '/'
    path += 'chat/completions'
    
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": True
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    if parsed_url.scheme == 'https':
        conn = HTTPSConnection(host)
    else:
        conn = HTTPConnection(host)
    
    conn.request(
        "POST",
        path,
        body=json.dumps(data),
        headers=headers
    )
    
    response = conn.getresponse()
    
    full_content = ""
    start_time = time.time()
    
    try:
        while True:
            line = response.readline().decode('utf-8')
            if not line:
                break
            
            line = line.strip()
            if line.startswith('data: '):
                data_str = line[6:]
                if data_str == '[DONE]':
                    break
                
                try:
                    chunk = json.loads(data_str)
                    if 'choices' in chunk and len(chunk['choices']) > 0:
                        delta = chunk['choices'][0].get('delta', {})
                        content = delta.get('content', '')
                        if content:
                            print(content, end='', flush=True)
                            full_content += content
                except json.JSONDecodeError:
                    continue
    except KeyboardInterrupt:
        print("\n\n[用户中断]")
    finally:
        conn.close()
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print()
    return full_content, elapsed_time

def print_welcome():
    print("=" * 60)
    print("AI 智能体交互式聊天客户端 (带关键信息提取和历史搜索)")
    print("=" * 60)
    print("提示：")
    print("  - 输入消息与AI对话")
    print("  - 输入 'quit' 或 'exit' 退出")
    print("  - 按 Ctrl+C 中断当前响应")
    print("  - 对话超过5轮或3000字符时自动压缩历史")
    print("  - 每5轮对话自动提取关键信息并保存")
    print("  - 输入 '/search' 或 '查找聊天历史' 搜索历史记录")
    print("=" * 60)

def main():
    env_vars = load_env()
    
    base_url = env_vars.get('BASE_URL', 'http://127.0.0.1:1234/v1')
    model = env_vars.get('MODEL', 'qwen/qwen3.5-2b')
    api_key = env_vars.get('API_KEY', 'sk-local-llm')
    max_tokens = int(env_vars.get('MAX_TOKENS', 500))
    
    print_welcome()
    print(f"连接到: {base_url}")
    print(f"使用模型: {model}")
    print("=" * 60)
    
    conversation_history = []
    
    try:
        while True:
            try:
                user_input = input("\n你: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("再见！")
                    break
                
                if should_search_chat_history(user_input):
                    print("[系统提示] 正在搜索聊天历史...")
                    search_result = search_chat_history(user_input, base_url, model, api_key)
                    print(f"[搜索结果]\n{search_result}")
                    continue
                
                conversation_history.append({"role": "user", "content": user_input})
                
                print("AI: ", end='', flush=True)
                
                ai_response, time_taken = stream_llm_response(
                    base_url, model, api_key, conversation_history, max_tokens
                )
                
                if ai_response:
                    conversation_history.append({"role": "assistant", "content": ai_response})
                    print(f"\n[耗时: {time_taken:.2f}秒]")
                    
                    check_and_extract_key_info(conversation_history, base_url, model, api_key)
                    
                    conversation_history, was_summarized = check_and_summarize(
                        conversation_history, base_url, model, api_key
                    )
                    
                    if was_summarized:
                        print(f"[当前对话轮数: {len(conversation_history)}]")
                
            except KeyboardInterrupt:
                print("\n\n检测到 Ctrl+C，继续聊天...")
                continue
                
    except KeyboardInterrupt:
        print("\n\n程序已退出。")

if __name__ == "__main__":
    main()
