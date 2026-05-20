import os
import sys
import time
import json
import http.client
from urllib.parse import urlparse

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
    print("LLM Token统计客户端")
    print("=" * 70)
    print(f"API基础URL: {base_url}")
    print(f"模型名称: {model}")
    print(f"温度参数: {temperature}")
    print(f"最大令牌数: {max_tokens}")
    print("=" * 70)
    
    chat_history = []
    
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
            chat_history.append({"role": "assistant", "content": result['content']})
            
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
            print(result['content'])
        else:
            print(f"请求失败: {result['error']}")
            if 'response' in result:
                print(f"响应内容: {result['response']}")
            print(f"耗时: {result['elapsed_time']:.4f} 秒")
        
        print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
