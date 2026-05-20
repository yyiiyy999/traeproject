import os
import sys

BASE_WORK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_WORK_DIR)

from chat_client import (
    execute_chained_tool_call,
    ChainedCallContext,
    build_analysis_prompt,
    load_env,
    call_llm
)

def test_chained_call_context():
    print("=" * 60)
    print("测试1：ChainedCallContext 类")
    print("=" * 60)

    context = ChainedCallContext(max_iterations=3)

    context.add_call("search_files", {"directory": "practice05", "keyword": "def"}, '[{"file": "test.py", "lines": [1, 2]}]')
    context.add_call("read_file", {"file_path": "test.py"}, "def hello(): print('world')")

    print(f"当前迭代：{context.current_iteration}")
    print(f"调用历史：{len(context.call_history)} 条")
    print(f"变量：{context.variables}")
    print(f"历史摘要：\n{context.get_history_summary()}")

    assert context.current_iteration == 0
    assert len(context.call_history) == 2
    assert "last_read_file" in context.variables

    print("\n[通过] ChainedCallContext 测试完成\n")

def test_build_analysis_prompt():
    print("=" * 60)
    print("测试2：build_analysis_prompt 函数")
    print("=" * 60)

    context = ChainedCallContext()
    context.add_call("search_files", {"directory": "practice05", "keyword": "def"}, '[{"file": "test.py"}]')

    user_request = "查找practice05目录下包含def的文件"
    prompt = build_analysis_prompt(user_request, context)

    assert user_request in prompt
    assert "已执行的工具调用历史" in prompt
    assert "search_files" in prompt
    assert "def" in prompt

    print("生成的提示词预览：")
    print(prompt[:500] + "...")

    print("\n[通过] build_analysis_prompt 测试完成\n")

def test_chained_file_search():
    print("=" * 60)
    print("测试3：链式文件搜索")
    print("=" * 60)

    env_vars = load_env()
    base_url = env_vars.get('BASE_URL', 'http://127.0.0.1:1234/v1')
    model = env_vars.get('MODEL', 'qwen/qwen3.5-2b')
    api_key = env_vars.get('API_KEY', 'sk-local-llm')

    user_request = "请查找 practice05 目录下所有包含'def'关键词的文件，并总结这些文件的主要内容"

    print(f"[测试] 用户请求：{user_request}\n")

    result = execute_chained_tool_call(base_url, model, api_key, user_request, max_iterations=10)

    print(f"\n[测试] 最终结果：{result}")
    print("\n[通过] 链式文件搜索测试完成\n")

def test_multi_file_operation():
    print("=" * 60)
    print("测试4：多文件操作（读取、计算、写入）")
    print("=" * 60)

    env_vars = load_env()
    base_url = env_vars.get('BASE_URL', 'http://127.0.0.1:1234/v1')
    model = env_vars.get('MODEL', 'qwen/qwen3.5-2b')
    api_key = env_vars.get('API_KEY', 'sk-local-llm')

    user_request = "读取 d:\\aaalaoda\\university\\2.2\\Ai\\traeproject\\practice06\\1.txt 和 d:\\aaalaoda\\university\\2.2\\Ai\\traeproject\\practice06\\2.txt 两个文件，文件内容的都是正整数，把两个数相加的和写入 d:\\aaalaoda\\university\\2.2\\Ai\\traeproject\\practice06\\result.txt 文件。"

    print(f"[测试] 用户请求：{user_request}\n")

    result = execute_chained_tool_call(base_url, model, api_key, user_request, max_iterations=10)

    print(f"\n[测试] 最终结果：{result}")

    result_file = os.path.join(BASE_WORK_DIR, "result.txt")
    if os.path.exists(result_file):
        with open(result_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        print(f"[测试] result.txt 内容：{content}")
        try:
            num = int(content)
            if 95 <= num <= 105:
                print(f"[验证] 42 + 58 = 100，结果正确！")
        except ValueError:
            print(f"[验证] 结果不是有效数字")

    print("\n[通过] 多文件操作测试完成\n")

def test_webpage_chain():
    print("=" * 60)
    print("测试5：网页处理链式调用")
    print("=" * 60)

    env_vars = load_env()
    base_url = env_vars.get('BASE_URL', 'http://127.0.0.1:1234/v1')
    model = env_vars.get('MODEL', 'qwen/qwen3.5-2b')
    api_key = env_vars.get('API_KEY', 'sk-local-llm')

    user_request = "访问 https://www.nsu.edu.cn/HTML/news/2024/06/article_3974.html 并总结页面内容，保存到 d:\\aaalaoda\\university\\2.2\\Ai\\traeproject\\practice06\\summary.txt"

    print(f"[测试] 用户请求：{user_request}\n")

    result = execute_chained_tool_call(base_url, model, api_key, user_request, max_iterations=10)

    print(f"\n[测试] 最终结果：{result}")

    summary_file = os.path.join(BASE_WORK_DIR, "summary.txt")
    if os.path.exists(summary_file):
        with open(summary_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"[测试] summary.txt 内容预览：{content[:200]}...")

    print("\n[通过] 网页处理链式调用测试完成\n")

def main():
    print("\n" + "=" * 60)
    print("practice06 链式工具调用测试")
    print("=" * 60 + "\n")

    try:
        test_chained_call_context()
    except Exception as e:
        print(f"[失败] 测试1出错：{str(e)}\n")

    try:
        test_build_analysis_prompt()
    except Exception as e:
        print(f"[失败] 测试2出错：{str(e)}\n")

    print("\n" + "-" * 60)
    print("以下为交互式测试，需要LLM服务运行：")
    print("-" * 60)

    choice = input("\n是否运行交互式测试？(y/n): ").strip().lower()
    if choice == 'y':
        try:
            test_chained_file_search()
        except Exception as e:
            print(f"[失败] 测试3出错：{str(e)}\n")

        choice2 = input("\n是否继续测试2？(y/n): ").strip().lower()
        if choice2 == 'y':
            try:
                test_multi_file_operation()
            except Exception as e:
                print(f"[失败] 测试4出错：{str(e)}\n")

        choice3 = input("\n是否继续测试3（网页处理）？(y/n): ").strip().lower()
        if choice3 == 'y':
            try:
                test_webpage_chain()
            except Exception as e:
                print(f"[失败] 测试5出错：{str(e)}\n")

    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()