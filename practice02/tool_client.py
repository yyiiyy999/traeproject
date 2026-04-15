import os
import json
import time
import sys
from http.client import HTTPSConnection, HTTPConnection
from urllib.parse import urlparse

# ====================== 核心配置：固定文件操作目录为practice03 ======================
# 自动获取当前脚本所在目录（practice03），保证文件创建在这里
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

# ====================== 5个文件操作工具（强制在practice03目录操作）======================
def list_directory(path=None):
    # 默认列出practice03目录
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
    # 默认在practice03目录
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
    # 默认在practice03目录
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
    # 默认在practice03目录，强制真实创建
    directory = directory if directory else BASE_WORK_DIR
    try:
        if not os.path.exists(directory):
            return f"错误：目录 '{directory}' 不存在"
        if not os.path.isdir(directory):
            return f"错误：'{directory}' 不是一个目录"
        
        file_path = os.path.join(directory, file_name)
        if os.path.exists(file_path):
            return f"错误：文件 '{file_path}' 已存在"
        
        # 真实写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"成功：文件 '{file_name}' 已在 {directory} 创建，内容：{content}"
    except Exception as e:
        return f"错误：{str(e)}"

def read_file(file_name, directory=None):
    # 默认在practice03目录
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

# ====================== 强化版指令识别（100%匹配中文）======================
def parse_command(user_input):
    text = user_input.strip().lower()
    print(f"[调试] 识别输入：{text}")  # 调试用，可删除

    # 1. 列出目录（匹配所有相关关键词）
    list_keywords = ["列出", "查看", "有什么文件", "当前目录", "目录下的文件"]
    if any(k in text for k in list_keywords):
        return ("list",)

    # 2. 创建文件（匹配所有相关关键词，提取文件名和内容）
    create_keywords = ["创建", "新建", "生成", "写一个", "新建文件"]
    if any(k in text for k in create_keywords):
        # 提取文件名（匹配xxx.txt/xxx.py等）
        import re
        file_match = re.search(r'([a-zA-Z0-9_]+\.[a-zA-Z0-9]+)', text)
        if not file_match:
            return None
        file_name = file_match.group(1)

        # 提取内容（匹配"内容是xxx" / "内容为xxx" / "写入xxx"）
        content_patterns = [
            r'内容[是为](.*)',
            r'写入(.*)',
            r'内容(.*)'
        ]
        content = "默认内容"
        for pattern in content_patterns:
            content_match = re.search(pattern, text)
            if content_match:
                content = content_match.group(1).strip()
                break

        return ("create", file_name, content)

    # 3. 读取文件
    read_keywords = ["读取", "打开", "查看内容", "读一下", "内容是什么"]
    if any(k in text for k in read_keywords):
        import re
        file_match = re.search(r'([a-zA-Z0-9_]+\.[a-zA-Z0-9]+)', text)
        if not file_match:
            return None
        file_name = file_match.group(1)
        return ("read", file_name)

    # 4. 重命名文件
    rename_keywords = ["重命名", "改名", "把xxx改成xxx", "重命名为"]
    if any(k in text for k in rename_keywords):
        import re
        # 匹配"把old.txt改成new.txt"
        file_match = re.search(r'把\s*([a-zA-Z0-9_]+\.[a-zA-Z0-9]+)\s*(改成|重命名为|改为)\s*([a-zA-Z0-9_]+\.[a-zA-Z0-9]+)', text)
        if not file_match:
            return None
        old_name = file_match.group(1)
        new_name = file_match.group(3)
        return ("rename", old_name, new_name)

    # 5. 删除文件
    delete_keywords = ["删除", "删掉", "移除", "删除文件"]
    if any(k in text for k in delete_keywords):
        import re
        file_match = re.search(r'([a-zA-Z0-9_]+\.[a-zA-Z0-9]+)', text)
        if not file_match:
            return None
        file_name = file_match.group(1)
        return ("delete", file_name)

    return None

# ====================== 主程序 ======================
def main():
    env = load_env()
    base_url = env.get('BASE_URL', 'http://127.0.0.1:1234/v1')
    model = env.get('MODEL', 'qwen/qwen3.5-2b')
    api_key = env.get('API_KEY', 'sk-local-llm')
    max_tokens = int(env.get('MAX_TOKENS', 500))

    print("=" * 60)
    print("AI 文件助手（真实操作版，文件保存在practice02目录）")
    print("=" * 60)
    print("支持指令示例：")
    print("1. 列出当前目录文件")
    print("2. 创建一个文件，并且写入内容")
    print("3. 读取某个文件")
    print("4. 修改某个文件的名字")
    print("5. 删除某个目录下的某个文件")
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

        # 第一步：优先识别文件操作指令，强制执行
        cmd = parse_command(user)
        if cmd:
            print("\n【系统】检测到文件操作，正在执行...")
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
            else:
                res = "错误：未知指令"

            print(f"【执行结果】\n{res}")
            # 把执行结果加入对话历史
            history.append({"role":"user","content":user})
            history.append({"role":"assistant","content":res})
            continue

        # 第二步：不是文件操作，走普通聊天
        history.append({"role":"user","content":user})
        print("AI：", end="", flush=True)
        ans, t = stream_llm_response(base_url, model, api_key, history, max_tokens)
        history.append({"role":"assistant","content":ans})
        print(f"\n[耗时：{t:.2f}s]")

if __name__ == "__main__":
    main()