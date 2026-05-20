import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chat_client import anythingllm_query, load_env

print("测试AnythingLLM查询功能")
print("=" * 60)

print("\n1. 测试环境变量加载...")
env_vars = load_env()
api_key = env_vars.get('ANYTHINGLLM_API_KEY', '未找到')
workspace_slug = env_vars.get('ANYTHING_WORKSPACE_SLUG', '未找到')
print(f"   ANYTHINGLLM_API_KEY: {api_key[:10]}..." if len(api_key) > 10 else f"   ANYTHINGLLM_API_KEY: {api_key}")
print(f"   ANYTHING_WORKSPACE_SLUG: {workspace_slug}")

print("\n2. 测试AnythingLLM查询...")
test_query = input("请输入查询内容（直接按Enter使用默认查询）：").strip()
if not test_query:
    test_query = "项目介绍"

print(f"\n正在查询：{test_query}")
print("-" * 50)
result = anythingllm_query(test_query)
print(result)
print("-" * 50)

print("\n测试完成！")
