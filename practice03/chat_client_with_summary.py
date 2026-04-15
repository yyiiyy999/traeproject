import os
import json
import time
import sys
from http.client import HTTPSConnection, HTTPConnection
from urllib.parse import urlparse

# ====================== 核心配置 ======================
# 自动获取当前脚本所在目录
BASE_WORK_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"[系统] 工作目录：{BASE_WORK_DIR}")

def load_env():
    env_path = os.path.join(os.path.dirname(BASE_WORK_DIR), '.env')
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

def get_chat_history_length(history):
    """计算聊天历史的总长度"""
    total_length = 0
    for message in history:
        total_length += len(message.get('content', ''))
    return total_length

def summarize_chat_history(base_url, model, api_key, history):
    """使用LLM对聊天历史进行总结"""
    # 计算分割点，前70%压缩，后30%保留原文
    split_point = int(len(history) * 0.7)
    history_to_summarize = history[:split_point]
    history_to_keep = history[split_point:]
    
    # 构建总结请求
    summary_prompt = [
        {
            "role": "system",
            "content": "你是一个聊天记录总结助手，需要将用户和AI的对话进行简洁总结，保留关键信息和对话要点。"
        },
        {
            "role": "user",
            "content": f"请总结以下聊天记录，保持简洁明了：\n\n{json.dumps(history_to_summarize, ensure_ascii=False)}"
        }
    ]
    
    print("\n[系统] 正在总结聊天历史...")
    
    # 发送总结请求
    parsed_url = urlparse(base_url)
    host = parsed_url.netloc
    path = parsed_url.path or '/'
    if not path.endswith('/'):
        path += '/'
    path += 'chat/completions'
    
    data = {
        "model": model,
        "messages": summary_prompt,
        "max_tokens": 500,
        "stream": False
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
    
    try:
        response_data = json.loads(response.read().decode('utf-8'))
        if 'choices' in response_data and len(response_data['choices']) > 0:
            summary = response_data['choices'][0].get('message', {}).get('content', '')
            print(f"[系统] 聊天历史总结完成")
            
            # 构建新的历史记录：总结 + 保留的原文
            new_history = [
                {
                    "role": "system",
                    "content": f"聊天历史总结：{summary}\n\n以下是最近的对话内容："
                }
            ] + history_to_keep
            
            return new_history
        else:
            print("[系统] 总结失败，保留原始历史")
            return history
    except Exception as e:
        print(f"[系统] 总结出错：{str(e)}，保留原始历史")
        return history
    finally:
        conn.close()

def print_welcome():
    print("=" * 60)
    print("AI 智能体交互式聊天客户端（支持聊天记录压缩）")
    print("=" * 60)
    print("提示：")
    print("  - 输入消息与AI对话")
    print("  - 输入 'quit' 或 'exit' 退出")
    print("  - 按 Ctrl+C 中断当前响应")
    print("  - 聊天超过5轮或上下文超过3k时会自动压缩")
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
                
                # 添加用户输入到历史记录
                conversation_history.append({"role": "user", "content": user_input})
                
                # 检查是否需要压缩聊天历史
                chat_length = get_chat_history_length(conversation_history)
                chat_rounds = len(conversation_history) // 2  # 每两轮为一个完整对话
                
                if chat_rounds >= 5 or chat_length >= 3000:
                    print("\n[系统] 聊天历史达到阈值，开始压缩...")
                    conversation_history = summarize_chat_history(base_url, model, api_key, conversation_history)
                    print("[系统] 聊天历史压缩完成")
                
                print("AI: ", end='', flush=True)
                
                # 获取AI响应
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