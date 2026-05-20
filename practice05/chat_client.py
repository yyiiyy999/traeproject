import os
import json
import time
import sys
import subprocess
import re
from http.client import HTTPSConnection, HTTPConnection
from urllib.parse import urlparse, quote

BASE_WORK_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(os.path.dirname(BASE_WORK_DIR), '.agents', 'skills')
print(f"[系统] 工作目录：{BASE_WORK_DIR}")
print(f"[系统] 技能目录：{SKILLS_DIR}")

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

def list_available_skills():
    """
    读取 .agents/skills 目录下的所有一级子目录，读取每个子目录内 SKILL.md 文件的 YAML front matter
    提取 name 和 description 字段
    """
    skills = []
    
    if not os.path.exists(SKILLS_DIR):
        print(f"[系统] 技能目录不存在：{SKILLS_DIR}")
        return skills
    
    try:
        # 遍历技能目录下的所有一级子目录
        for skill_dir in os.listdir(SKILLS_DIR):
            skill_path = os.path.join(SKILLS_DIR, skill_dir)
            if os.path.isdir(skill_path):
                skill_file = os.path.join(skill_path, 'SKILL.md')
                if os.path.exists(skill_file):
                    try:
                        with open(skill_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 提取 YAML front matter（--- 标记之间的内容）
                        if content.startswith('---'):
                            end_index = content.find('---\n', 3)
                            if end_index != -1:
                                front_matter = content[3:end_index].strip()
                                # 简单解析 YAML
                                skill_info = {}
                                lines = front_matter.split('\n')
                                for line in lines:
                                    if ':' in line:
                                        key, value = line.split(':', 1)
                                        key = key.strip()
                                        value = value.strip().strip('"').strip("'")
                                        if key == 'name':
                                            skill_info['name'] = value
                                        elif key == 'description':
                                            skill_info['description'] = value
                                
                                if 'name' in skill_info and 'description' in skill_info:
                                    skills.append(skill_info)
                                    print(f"[系统] 加载技能：{skill_info['name']} - {skill_info['description']}")
                    except Exception as e:
                        print(f"[系统] 读取技能文件失败 {skill_file}: {str(e)}")
    except Exception as e:
        print(f"[系统] 遍历技能目录失败: {str(e)}")
    
    return skills

def load_skill_content(skill_name):
    """
    加载指定技能的 SKILL.md 文件正文内容（YAML front matter 之后的部分）
    """
    skill_path = os.path.join(SKILLS_DIR, skill_name)
    skill_file = os.path.join(skill_path, 'SKILL.md')
    
    if not os.path.exists(skill_file):
        return None
    
    try:
        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取 YAML front matter 之后的内容
        if content.startswith('---'):
            end_index = content.find('---\n', 3)
            if end_index != -1:
                body_content = content[end_index + 4:].strip()
                return body_content
        
        return content.strip()
    except Exception as e:
        print(f"[系统] 加载技能内容失败 {skill_file}: {str(e)}")
        return None

def anythingllm_query(query):
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

def call_function(function_name, function_args, base_url, model, api_key):
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
    print("AI 智能体（支持技能系统）")
    print("=" * 60)
    print("提示：")
    print("  - 输入消息与AI对话")
    print("  - 系统会自动识别可用技能并调用")
    print("  - 聊天超过5轮或上下文超过3k时会自动压缩")
    print("  - 输入 'quit' 或 'exit' 退出")
    print("=" * 60)
    print(f"连接到: {base_url}")
    print(f"使用模型: {model}")
    print("=" * 60)

    # 加载可用技能列表
    skills = list_available_skills()
    skills_json = json.dumps({"skills": skills}, ensure_ascii=False, indent=2)
    print(f"[系统] 已加载 {len(skills)} 个技能")
    print(f"[系统] 技能列表: {skills_json}")

    # 系统提示词：不干预技能执行
    system_prompt = f"""你是一个智能助手，可以帮助用户回答各种问题。

你可以使用以下可用技能：
{skills_json}

当用户的请求匹配某个技能的描述时，你需要根据技能的指令生成回复。
禁止输出<skill:xxx>格式的调用标记，直接输出最终结果即可。"""

    history = [
        {
            "role": "system",
            "content": system_prompt
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

            # 技能匹配
            skill_to_call = None
            for skill in skills:
                skill_name = skill['name']
                if skill_name == "notice":
                    notice_keywords = ["通知", "放假", "公告", "撰写通知", "修改通知", "润色通知"]
                    if any(keyword in text_lower for keyword in notice_keywords):
                        skill_to_call = skill_name
                        break

            # ========== NOTICE 技能处理：完全硬编码，不依赖模型 ==========
            if skill_to_call == "notice":
                print(f"\n【系统】检测到技能调用：notice")
                
                # 1. 提取部门（完全重写的正则，解决所有识别问题）
                department = "XX部"
                # 直接匹配“XX部”格式，排除“撰写”“通知”等无关词
                dept_match = re.search(r'(?<!撰写)(?<!修改)(?<!润色)(\S+部)', user_input)
                if dept_match:
                    department = dept_match.group(1)
                # 匹配“我是XX部的”
                elif "我是" in user_input and "的" in user_input:
                    dept_match2 = re.search(r"我是(.*?)部的", user_input)
                    if dept_match2:
                        department = dept_match2.group(1) + "部"

                # 2. 强制固定开头
                fixed_start = f"{department}通知\n\n"
                print(f"【系统】已设置通知开头：{fixed_start.strip()}")

                # 3. 给模型的指令：**只写正文，不写标题、不写开头、不写结尾**
                notice_instruction = f"""【强制规则，必须100%遵守】
你现在需要撰写一份正式通知，**开头和结尾已经固定，你只需要写中间的正文内容**：

固定开头：{fixed_start}
固定结尾：特此通知。

你的任务：
1. 只写通知的正文内容，不要写标题、不要重复开头、不要写结尾的“特此通知”
2. 正文内容要正式、规范，包含事由、时间、工作要求等关键信息
3. 不要写任何额外的解释、说明、格式符号
4. 不要出现任何“XX部通知”的字样

用户请求：{user_input}"""

                # 加入对话历史
                history.append({
                    "role": "system",
                    "content": notice_instruction
                })

            chat_length = get_chat_history_length(history)
            chat_rounds = len(history) // 2

            if chat_rounds >= 5 or chat_length >= 3000:
                history = summarize_chat_history(base_url, model, api_key, history)

            print("AI：", end="", flush=True)

            ai_response, time_taken = stream_llm_response(
                base_url, model, api_key, history, max_tokens
            )

            # 4. 强制拼接开头+正文+结尾，清理所有模型输出的多余内容
            if skill_to_call == "notice":
                # 清理模型输出：去掉所有开头、结尾、无关内容
                cleaned_body = re.sub(r'^.*通知\s*\n*', '', ai_response)
                cleaned_body = re.sub(r'特此通知[。.]?\s*$', '', cleaned_body)
                cleaned_body = cleaned_body.strip()
                
                # 强制拼接
                final_response = f"{fixed_start}{cleaned_body}\n\n特此通知。"
                # 输出最终结果
                print(final_response, end="")
                ai_response = final_response

            if ai_response:
                history.append({"role": "assistant", "content": ai_response})
                print(f"\n[耗时：{time_taken:.2f}秒]")

        except KeyboardInterrupt:
            print("\n\n检测到Ctrl+C，继续聊天...")
            continue

if __name__ == "__main__":
    main()