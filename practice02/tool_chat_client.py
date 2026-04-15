import os
import json
import time
import sys
import re
from http.client import HTTPSConnection, HTTPConnection
from urllib.parse import urlparse, quote

# ====================== 核心配置：固定文件操作目录为practice03 ======================
BASE_WORK_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"[系统] 文件操作目录：{BASE_WORK_DIR}")

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

    conn.request("POST", path, body=json.dumps(data), headers=headers)
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
        print("\n[用户中断]")
    finally:
        conn.close()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print()
    return full_content.strip(), elapsed_time

# ====================== 5个文件操作工具（原逻辑完全不变）======================
def list_directory(path=None):
    path = path if path else BASE_WORK_DIR
    try:
        if not os.path.exists(path):
            return f"错误：目录 '{path}' 不存在"
        if not os.path.isdir(path):
            return f"错误：'{path}' 不是一个目录"
        
        files = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            item_stat = os.stat(item_path)
            item_type = "目录" if os.path.isdir(item_path) else "文件"
            item_size = item_stat.st_size
            item_mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item_stat.st_mtime))
            files.append(f"{item_type}: {item} (大小: {item_size} 字节, 修改时间: {item_mtime})")
        
        return "\n".join(files)
    except Exception as e:
        return f"错误：{str(e)}"

def rename_file(old_name, new_name, directory=None):
    directory = directory if directory else BASE_WORK_DIR
    try:
        old_path = os.path.join(directory, old_name)
        new_path = os.path.join(directory, new_name)
        
        if not os.path.exists(old_path):
            return f"错误：文件 '{old_path}' 不存在"
        if os.path.exists(new_path):
            return f"错误：文件 '{new_path}' 已存在"
        
        os.rename(old_path, new_path)
        return f"成功：文件已重命名为 '{new_name}'"
    except Exception as e:
        return f"错误：{str(e)}"

def delete_file(file_name, directory=None):
    directory = directory if directory else BASE_WORK_DIR
    try:
        file_path = os.path.join(directory, file_name)
        
        if not os.path.exists(file_path):
            return f"错误：文件 '{file_path}' 不存在"
        if not os.path.isfile(file_path):
            return f"错误：'{file_path}' 不是一个文件"
        
        os.remove(file_path)
        return f"成功：文件 '{file_name}' 已删除"
    except Exception as e:
        return f"错误：{str(e)}"

def create_file(file_name, content, directory=None):
    directory = directory if directory else BASE_WORK_DIR
    try:
        if not os.path.exists(directory):
            return f"错误：目录 '{directory}' 不存在"
        if not os.path.isdir(directory):
            return f"错误：'{directory}' 不是一个目录"
        
        file_path = os.path.join(directory, file_name)
        if os.path.exists(file_path):
            return f"错误：文件 '{file_path}' 已存在"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"成功：文件 '{file_name}' 已在 {directory} 创建，内容：{content}"
    except Exception as e:
        return f"错误：{str(e)}"

def read_file(file_name, directory=None):
    directory = directory if directory else BASE_WORK_DIR
    try:
        file_path = os.path.join(directory, file_name)
        
        if not os.path.exists(file_path):
            return f"错误：文件 '{file_path}' 不存在"
        if not os.path.isfile(file_path):
            return f"错误：'{file_path}' 不是一个文件"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"文件 '{file_name}' 内容：\n{content}"
    except Exception as e:
        return f"错误：{str(e)}"

# ====================== 增强版curl工具（支持wttr.in天气直接输出）======================
def curl(url):
    try:
        parsed_url = urlparse(url)
        host = parsed_url.netloc
        path = parsed_url.path or '/'
        if parsed_url.query:
            path += '?' + parsed_url.query

        # 处理中文URL编码（wttr.in需要）
        if '%' not in path:
            path = quote(path, encoding='utf-8')

        if parsed_url.scheme == 'https':
            conn = HTTPSConnection(host, timeout=10)
        else:
            conn = HTTPConnection(host, timeout=10)

        start_time = time.time()
        conn.request("GET", path, headers={"User-Agent": "curl/7.68.0"})
        response = conn.getresponse()

        if response.status == 200:
            content = response.read().decode('utf-8', errors='replace')
            elapsed = time.time() - start_time
            return f"状态码：{response.status}\n耗时：{elapsed:.2f}秒\n\n{content}"
        else:
            return f"错误：HTTP {response.status} {response.reason}"
    except Exception as e:
        return f"错误：{str(e)}"

# ====================== 终极版指令识别（支持"XX天气如何"直接查天气）======================
def parse_command(user_input):
    text = user_input.strip().lower()
    original = user_input.strip()
    print(f"[调试] 识别输入：{text}")

    # 1. 优先识别URL（直接输入https://xxx自动触发curl）
    url_pattern = r'https?://[\w\-._~:/?#[\]@!$&\'()*+,;=.]+'
    url_match = re.search(url_pattern, original)
    if url_match:
        return ("curl", url_match.group(0))

    # 2. 识别"XX天气如何/XX天气怎么样"等自然问句
    weather_question_pattern = r'([\u4e00-\u9fa5a-zA-Z0-9\s]+?)(天气|气温|温度).*?(如何|怎么样|多少|预报)'
    weather_match = re.search(weather_question_pattern, original)
    if weather_match:
        city = weather_match.group(1).strip()
        return ("curl", f"https://www.wttr.in/{city}")

    # 3. 识别纯城市名查天气
    city_pattern = r'^([\u4e00-\u9fa5a-zA-Z0-9\s]+)$'
    city_match = re.match(city_pattern, original)
    if city_match and not any(k in text for k in ["列出", "创建", "读取", "重命名", "删除"]):
        city = city_match.group(1).strip()
        return ("curl", f"https://www.wttr.in/{city}")

    # 4. 列出目录
    list_keywords = ["列出", "查看", "有什么文件", "当前目录", "目录下的文件"]
    if any(k in text for k in list_keywords):
        return ("list",)

    # 5. 创建文件
    create_keywords = ["创建", "新建", "生成", "写一个", "新建文件"]
    if any(k in text for k in create_keywords):
        file_match = re.search(r'([a-zA-Z0-9_]+\.[a-zA-Z0-9]+)', text)
        if not file_match:
            return None
        file_name = file_match.group(1)
        content = "默认内容"
        content_patterns = [r'内容[是为](.*)', r'写入(.*)', r'内容(.*)']
        for pattern in content_patterns:
            content_match = re.search(pattern, text)
            if content_match:
                content = content_match.group(1).strip()
                break
        return ("create", file_name, content)

    # 6. 读取文件
    read_keywords = ["读取", "打开", "查看内容", "读一下", "内容是什么"]
    if any(k in text for k in read_keywords):
        file_match = re.search(r'([a-zA-Z0-9_]+\.[a-zA-Z0-9]+)', text)
        if not file_match:
            return None
        file_name = file_match.group(1)
        return ("read", file_name)

    # 7. 重命名文件
    rename_keywords = ["重命名", "改名", "把xxx改成xxx", "重命名为"]
    if any(k in text for k in rename_keywords):
        file_match = re.search(r'把\s*([a-zA-Z0-9_]+\.[a-zA-Z0-9]+)\s*(改成|重命名为|改为)\s*([a-zA-Z0-9_]+\.[a-zA-Z0-9]+)', text)
        if not file_match:
            return None
        old_name = file_match.group(1)
        new_name = file_match.group(3)
        return ("rename", old_name, new_name)

    # 8. 删除文件
    delete_keywords = ["删除", "删掉", "移除", "删除文件"]
    if any(k in text for k in delete_keywords):
        file_match = re.search(r'([a-zA-Z0-9_]+\.[a-zA-Z0-9]+)', text)
        if not file_match:
            return None
        file_name = file_match.group(1)
        return ("delete", file_name)
    
    # 9. curl指令
    curl_keywords = ["curl", "访问网页", "获取网页", "下载网页"]
    if any(k in text for k in curl_keywords):
        url_match = re.search(url_pattern, text)
        if not url_match:
            return None
        return ("curl", url_match.group(0))

    return None

# ====================== 主程序（更新提示文本）======================
def main():
    env = load_env()
    base_url = env.get('BASE_URL', 'http://127.0.0.1:1234/v1')
    model = env.get('MODEL', 'qwen/qwen3.5-2b')
    api_key = env.get('API_KEY', 'sk-local-llm')
    max_tokens = int(env.get('MAX_TOKENS', 500))

    print("=" * 60)
    print("AI 文件助手（真实操作版，支持天气/网页直接输出）")
    print("=" * 60)
    print("支持指令示例：")
    print("1. 列出当前目录文件")
    print("2. 创建一个文件，并且写入内容")
    print("3. 读取某个文件")
    print("4. 修改某个文件的名字")
    print("5. 删除某个目录下的某个文件")
    print("6. curl访问网页，例如：curl https://www.example.com")
    print("7. 查天气，例如：青城山天气如何 / 成都天气怎么样 / 青城山")
    print("=" * 60)

    history = [
        {"role":"system","content":"你是一个简洁的中文助手，只回答用户问题，不要多余内容。"}
    ]

    while True:
        user = input("\n你：").strip()
        if not user:
            continue
        if user.lower() in ["quit", "exit", "退出"]:
            print("再见！")
            break

        cmd = parse_command(user)
        if cmd:
            print("\n【系统】检测到操作，正在执行...")
            res = ""
            if cmd[0] == "list":
                res = list_directory()
            elif cmd[0] == "create":
                res = create_file(cmd[1], cmd[2])
            elif cmd[0] == "read":
                res = read_file(cmd[1])
            elif cmd[0] == "rename":
                res = rename_file(cmd[1], cmd[2])
            elif cmd[0] == "delete":
                res = delete_file(cmd[1])
            elif cmd[0] == "curl":
                res = curl(cmd[1])
            else:
                res = "错误：未知指令"

            print(f"【执行结果】\n{res}")
            history.append({"role":"user","content":user})
            history.append({"role":"assistant","content":res})
            continue

        history.append({"role":"user","content":user})
        print("AI：", end="", flush=True)
        ans, t = stream_llm_response(base_url, model, api_key, history, max_tokens)
        history.append({"role":"assistant","content":ans})
        print(f"\n[耗时：{t:.2f}s]")

if __name__ == "__main__":
    main()