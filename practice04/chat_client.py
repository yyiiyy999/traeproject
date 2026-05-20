import os
import json
import time
import sys
import subprocess
from http.client import HTTPSConnection, HTTPConnection
from urllib.parse import urlparse, quote

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

def anythingllm_query(query):
    """
    使用subprocess调用curl访问AnythingLLM聊天API
    注意处理中文编码问题
    """
    try:
        env_vars = load_env()
        api_key = env_vars.get('ANYTHINGLLM_API_KEY', '')
        workspace_slug = env_vars.get('ANYTHING_WORKSPACE_SLUG', 'project')

        if not api_key:
            return "错误：未找到ANYTHINGLLM_API_KEY，请在.env文件中配置"

        api_url = f"http://localhost:3001/api/v1/workspace/{workspace_slug}/chat"

        request_body = json.dumps({
            "message": query
        }, ensure_ascii=False)

        curl_cmd = [
            'curl',
            '-X', 'POST',
            api_url,
            '-H', 'Content-Type: application/json; charset=utf-8',
            '-H', f'Authorization: Bearer {api_key}',
            '-d', request_body
        ]

        print(f"[调试] 正在调用AnythingLLM API...")

        result = subprocess.run(
            curl_cmd,
            capture_output=True,
            timeout=30
        )

        if result.returncode != 0:
            return f"错误：curl命令执行失败 - {result.stderr.decode('utf-8', errors='replace')}"

        try:
            response_data = json.loads(result.stdout.decode('utf-8', errors='replace'))

            if 'textResponse' in response_data:
                return response_data['textResponse']
            elif 'sources' in response_data:
                response_text = response_data.get('textResponse', '')
                sources = response_data.get('sources', [])
                if sources:
                    sources_text = "\n\n参考来源：\n"
                    for i, source in enumerate(sources, 1):
                        title = source.get('title', '未知文档')
                        sources_text += f"{i}. {title}\n"
                    return response_text + sources_text
                return response_text
            else:
                return f"收到响应，但格式不完整：{str(response_data)[:200]}"

        except json.JSONDecodeError:
            return f"API响应解析失败，原始响应：{result.stdout.decode('utf-8', errors='replace')[:200]}"

    except subprocess.TimeoutExpired:
        return "错误：请求超时，请检查AnythingLLM是否正常运行"
    except Exception as e:
        return f"错误：{str(e)}"

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
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {api_key}"
    }

    if parsed_url.scheme == 'https':
        conn = HTTPSConnection(host)
    else:
        conn = HTTPConnection(host)

    body = json.dumps(data, ensure_ascii=False).encode('utf-8')
    conn.request("POST", path, body=body, headers=headers)
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
                except:
                    continue
    except KeyboardInterrupt:
        print("\n\n[用户中断]")
    finally:
        conn.close()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print()
    return full_content.strip(), elapsed_time

AVAILABLE_FUNCTIONS = {
    "anythingllm_query": {
        "name": "anythingllm_query",
        "description": "当用户提到'文档仓库'、'文件仓库'、'仓库'时，查询AnythingLLM文档仓库获取相关信息。使用方法：输入用户想要查询的内容。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "用户想要查询的内容"
                }
            },
            "required": ["query"]
        }
    }
}

def call_function(function_name, function_args, base_url, model, api_key):
    """调用指定的函数"""
    if function_name == "anythingllm_query":
        query = function_args.get("query", "")
        return anythingllm_query(query)
    else:
        return f"错误：未知函数 {function_name}"

def get_chat_history_length(history):
    total_length = 0
    for message in history:
        total_length += len(message.get('content', ''))
    return total_length

def summarize_chat_history(base_url, model, api_key, history):
    split_point = int(len(history) * 0.7)
    history_to_summarize = history[:split_point]
    history_to_keep = history[split_point:]

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
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {api_key}"
    }

    if parsed_url.scheme == 'https':
        conn = HTTPSConnection(host)
    else:
        conn = HTTPConnection(host)

    body = json.dumps(data, ensure_ascii=False).encode('utf-8')
    conn.request("POST", path, body=body, headers=headers)
    response = conn.getresponse()

    try:
        response_data = json.loads(response.read().decode('utf-8'))
        if 'choices' in response_data and len(response_data['choices']) > 0:
            summary = response_data['choices'][0].get('message', {}).get('content', '')
            print(f"[系统] 聊天历史总结完成")

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

def main():
    env_vars = load_env()

    base_url = env_vars.get('BASE_URL', 'http://127.0.0.1:1234/v1')
    model = env_vars.get('MODEL', 'qwen/qwen3.5-2b')
    api_key = env_vars.get('API_KEY', 'sk-local-llm')
    max_tokens = int(env_vars.get('MAX_TOKENS', 500))

    print("=" * 60)
    print("AI 智能体（支持AnythingLLM文档仓库查询）")
    print("=" * 60)
    print("提示：")
    print("  - 输入消息与AI对话")
    print("  - 提到'文档仓库'、'文件仓库'、'仓库'时会触发文档查询")
    print("  - 聊天超过5轮或上下文超过3k时会自动压缩")
    print("  - 输入 'quit' 或 'exit' 退出")
    print("=" * 60)
    print(f"连接到: {base_url}")
    print(f"使用模型: {model}")
    print("=" * 60)

    history = [
        {
            "role": "system",
            "content": """你是一个智能助手，可以帮助用户回答各种问题。

你可以调用以下工具：
1. anythingllm_query - 当用户提到'文档仓库'、'文件仓库'、'仓库'时使用，用于查询AnythingLLM文档仓库中的相关信息。

当用户询问与文档、文件、仓库相关的问题时，你应该：
1. 先识别出用户想要查询的内容
2. 调用anythingllm_query工具获取文档仓库中的信息
3. 根据查询结果回答用户的问题

可用工具列表：
- anythingllm_query: 查询AnythingLLM文档仓库"""
        }
    ]

    while True:
        try:
            user_input = input("\n你：").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', '退出']:
                print("再见！")
                break

            history.append({"role": "user", "content": user_input})

            text_lower = user_input.lower()
            warehouse_keywords = ["文档仓库", "文件仓库", "仓库"]

            if any(keyword in text_lower for keyword in warehouse_keywords):
                print("\n【系统】检测到文档仓库查询，正在执行...")

                query = user_input
                for keyword in warehouse_keywords:
                    if keyword in query:
                        query = query.replace(keyword, '').strip()
                if not query:
                    query = user_input

                result = call_function("anythingllm_query", {"query": query}, base_url, model, api_key)
                print(f"【查询结果】\n{result}")

                history.append({"role": "assistant", "content": result})
                continue

            chat_length = get_chat_history_length(history)
            chat_rounds = len(history) // 2

            if chat_rounds >= 5 or chat_length >= 3000:
                history = summarize_chat_history(base_url, model, api_key, history)

            print("AI：", end="", flush=True)

            ai_response, time_taken = stream_llm_response(
                base_url, model, api_key, history, max_tokens
            )

            if ai_response:
                history.append({"role": "assistant", "content": ai_response})
                print(f"\n[耗时：{time_taken:.2f}秒]")

        except KeyboardInterrupt:
            print("\n\n检测到Ctrl+C，继续聊天...")
            continue

if __name__ == "__main__":
    main()
