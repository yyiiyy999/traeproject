import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chat_client import list_available_skills, load_skill_content

def test_skills():
    print("=" * 60)
    print("测试技能系统")
    print("=" * 60)
    
    # 测试 list_available_skills
    print("\n1. 测试 list_available_skills 函数：")
    skills = list_available_skills()
    print(f"   加载到 {len(skills)} 个技能")
    for skill in skills:
        print(f"   - {skill['name']}: {skill['description']}")
    
    # 测试 load_skill_content
    print("\n2. 测试 load_skill_content 函数：")
    if skills:
        skill_content = load_skill_content(skills[0]['name'])
        if skill_content:
            print(f"   技能 {skills[0]['name']} 的内容（前200字符）：")
            print(f"   {skill_content[:200]}...")
        else:
            print(f"   无法加载技能 {skills[0]['name']} 的内容")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_skills()