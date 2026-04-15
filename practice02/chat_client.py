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
    print("AI 智能体交互式聊天客户端")
    print("=" * 60)
    print("提示：")
    print("  - 输入消息与AI对话")
    print("  - 输入 'quit' 或 'exit' 退出")
    print("  - 按 Ctrl+C 中断当前响应")
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
                
                conversation_history.append({"role": "user", "content": user_input})
                
                print("AI: ", end='', flush=True)
                
                ai_response, time_taken = stream_llm_response(
                    base_url, model, api_key, conversation_history, max_tokens
                )
                
                if ai_response:
                    conversation_history.append({"role": "assistant", "content": ai_response})
                    print(f"\n[耗时: {time_taken:.2f}秒]")
                
            except KeyboardInterrupt:
                print("\n\n检测到 Ctrl+C，继续聊天...")
                continue
                
    except KeyboardInterrupt:
        print("\n\n程序已退出。")

if __name__ == "__main__":
    main()