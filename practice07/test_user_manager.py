# 用户信息管理系统 - 完整测试脚本
# 依据 test.md 测试文档编写

import user_manager as um


def print_test_result(test_id, test_name, expected, actual, passed):
    """打印测试结果"""
    status = "PASS" if passed else "FAIL"
    print(f"{test_id} - {test_name}: {status}")
    if not passed:
        print(f"  预期：{expected}")
        print(f"  实际：{actual}")
    return passed


def run_all_tests():
    """运行所有测试用例"""
    print("=" * 60)
    print("用户信息管理系统 - 完整测试")
    print("=" * 60)
    
    total_tests = 0
    passed_tests = 0
    
    # ========== 4.1 用户新增功能测试 add_user ==========
    print("\n【4.1 用户新增功能测试】")
    
    # T001 - 正常新增合法用户
    um.clear_user_container()
    total_tests += 1
    result = um.add_user(1, "user01", 20, "男")
    expected_status = 1
    passed = result["status"] == expected_status and 1 in um.get_user_container()
    if print_test_result("T001", "正常新增合法用户", {"status": 1}, result, passed):
        passed_tests += 1
    
    # T002 - 重复 ID 新增
    total_tests += 1
    result = um.add_user(1, "user02", 25, "女")
    expected_status = 0
    passed = result["status"] == expected_status and "已存在" in result["message"]
    if print_test_result("T002", "重复 ID 新增", {"status": 0}, result, passed):
        passed_tests += 1
    
    # T003 - ID 为 0 非法输入
    total_tests += 1
    result = um.add_user(0, "user03", 30, "男")
    expected_status = 0
    passed = result["status"] == expected_status and "不合法" in result["message"]
    if print_test_result("T003", "ID 为 0 非法输入", {"status": 0}, result, passed):
        passed_tests += 1
    
    # T004 - 用户名长度不足 2 位
    total_tests += 1
    result = um.add_user(2, "a", 20, "男")
    expected_status = 0
    passed = result["status"] == expected_status and "长度" in result["message"]
    if print_test_result("T004", "用户名长度不足 2 位", {"status": 0}, result, passed):
        passed_tests += 1
    
    # T005 - 用户名含特殊符号
    total_tests += 1
    result = um.add_user(2, "user@1", 20, "男")
    expected_status = 0
    passed = result["status"] == expected_status and ("特殊" in result["message"] or "字母" in result["message"])
    if print_test_result("T005", "用户名含特殊符号", {"status": 0}, result, passed):
        passed_tests += 1
    
    # T006 - 年龄超出上限 120
    total_tests += 1
    result = um.add_user(2, "user02", 130, "男")
    expected_status = 0
    passed = result["status"] == expected_status and "年龄" in result["message"]
    if print_test_result("T006", "年龄超出上限 120", {"status": 0}, result, passed):
        passed_tests += 1
    
    # T007 - 年龄小于 1
    total_tests += 1
    result = um.add_user(2, "user02", 0, "男")
    expected_status = 0
    passed = result["status"] == expected_status and "年龄" in result["message"]
    if print_test_result("T007", "年龄小于 1", {"status": 0}, result, passed):
        passed_tests += 1
    
    # T008 - 性别输入非法值
    total_tests += 1
    result = um.add_user(2, "user02", 20, "中性")
    expected_status = 0
    passed = result["status"] == expected_status and "性别" in result["message"]
    if print_test_result("T008", "性别输入非法值", {"status": 0}, result, passed):
        passed_tests += 1
    
    # ========== 4.2 用户查询功能测试 ==========
    print("\n【4.2 用户查询功能测试】")
    
    # 4.2.1 单用户查询 get_user_by_id
    um.clear_user_container()
    um.add_user(1, "user01", 20, "男")
    um.add_user(2, "user02", 25, "女")
    
    # T101 - 查询已存在用户 ID
    total_tests += 1
    result = um.get_user_by_id(1)
    expected_status = 1
    passed = result["status"] == expected_status and result["data"]["username"] == "user01"
    if print_test_result("T101", "查询已存在用户 ID", {"status": 1}, result, passed):
        passed_tests += 1
    
    # T102 - 查询不存在用户 ID
    total_tests += 1
    result = um.get_user_by_id(999)
    expected_status = 0
    passed = result["status"] == expected_status and "未找到" in result["message"]
    if print_test_result("T102", "查询不存在用户 ID", {"status": 0}, result, passed):
        passed_tests += 1
    
    # T103 - 查询非法负数 ID
    total_tests += 1
    result = um.get_user_by_id(-5)
    expected_status = 0
    passed = result["status"] == expected_status and "不合法" in result["message"]
    if print_test_result("T103", "查询非法负数 ID", {"status": 0}, result, passed):
        passed_tests += 1
    
    # 4.2.2 全量查询 get_all_users
    # T104 - 无任何用户
    um.clear_user_container()
    total_tests += 1
    result = um.get_all_users()
    expected_status = 1
    passed = result["status"] == expected_status and result["data"] == []
    if print_test_result("T104", "无任何用户", {"status": 1, "data": []}, result, passed):
        passed_tests += 1
    
    # T105 - 存在多条用户数据
    um.clear_user_container()
    um.add_user(1, "user01", 20, "男")
    um.add_user(2, "user02", 25, "女")
    um.add_user(3, "user03", 30, "未知")
    total_tests += 1
    result = um.get_all_users()
    expected_status = 1
    passed = result["status"] == expected_status and len(result["data"]) == 3
    if print_test_result("T105", "存在多条用户数据", {"status": 1, "count": 3}, result, passed):
        passed_tests += 1
    
    # ========== 4.3 用户修改功能测试 update_user ==========
    print("\n【4.3 用户修改功能测试】")
    
    um.clear_user_container()
    um.add_user(1, "user01", 20, "男")
    
    # T201 - 正常修改用户名
    total_tests += 1
    result = um.update_user(1, new_username="user01_new")
    expected_status = 1
    passed = result["status"] == expected_status and result["data"]["username"] == "user01_new"
    if print_test_result("T201", "正常修改用户名", {"status": 1}, result, passed):
        passed_tests += 1
    
    # T202 - 正常修改年龄
    total_tests += 1
    result = um.update_user(1, new_age=25)
    expected_status = 1
    passed = result["status"] == expected_status and result["data"]["age"] == 25
    if print_test_result("T202", "正常修改年龄", {"status": 1}, result, passed):
        passed_tests += 1
    
    # T203 - 正常修改性别
    total_tests += 1
    result = um.update_user(1, new_gender="女")
    expected_status = 1
    passed = result["status"] == expected_status and result["data"]["gender"] == "女"
    if print_test_result("T203", "正常修改性别", {"status": 1}, result, passed):
        passed_tests += 1
    
    # T204 - 不传入任何修改字段
    total_tests += 1
    result = um.update_user(1)
    expected_status = 0
    passed = result["status"] == expected_status and "未修改" in result["message"]
    if print_test_result("T204", "不传入任何修改字段", {"status": 0}, result, passed):
        passed_tests += 1
    
    # T205 - 修改不存在用户 ID
    total_tests += 1
    result = um.update_user(999, new_username="test")
    expected_status = 0
    passed = result["status"] == expected_status and "未找到" in result["message"]
    if print_test_result("T205", "修改不存在用户 ID", {"status": 0}, result, passed):
        passed_tests += 1
    
    # T206 - 修改字段非法
    total_tests += 1
    result = um.update_user(1, new_age=150)
    expected_status = 0
    passed = result["status"] == expected_status and "年龄" in result["message"]
    if print_test_result("T206", "修改字段非法", {"status": 0}, result, passed):
        passed_tests += 1
    
    # ========== 4.4 用户删除功能测试 ==========
    print("\n【4.4 用户删除功能测试】")
    
    # 4.4.1 单条删除 delete_user_by_id
    um.clear_user_container()
    um.add_user(1, "user01", 20, "男")
    um.add_user(2, "user02", 25, "女")
    
    # T301 - 删除存在用户
    total_tests += 1
    result = um.delete_user_by_id(1)
    expected_status = 1
    passed = result["status"] == expected_status and 1 not in um.get_user_container()
    if print_test_result("T301", "删除存在用户", {"status": 1}, result, passed):
        passed_tests += 1
    
    # T302 - 删除不存在用户
    total_tests += 1
    result = um.delete_user_by_id(999)
    expected_status = 0
    passed = result["status"] == expected_status and "未找到" in result["message"]
    if print_test_result("T302", "删除不存在用户", {"status": 0}, result, passed):
        passed_tests += 1
    
    # T303 - 删除非法 ID
    total_tests += 1
    result = um.delete_user_by_id(-5)
    expected_status = 0
    passed = result["status"] == expected_status and "不合法" in result["message"]
    if print_test_result("T303", "删除非法 ID", {"status": 0}, result, passed):
        passed_tests += 1
    
    # 4.4.2 批量删除 delete_users_by_ids
    # T304 - 全部 ID 均存在
    um.clear_user_container()
    um.add_user(1, "user01", 20, "男")
    um.add_user(2, "user02", 25, "女")
    um.add_user(3, "user03", 30, "未知")
    total_tests += 1
    result = um.delete_users_by_ids([1, 2])
    expected_status = 1
    passed = result["status"] == expected_status and len(result["data"]["success_ids"]) == 2
    if print_test_result("T304", "全部 ID 均存在", {"status": 1}, result, passed):
        passed_tests += 1
    
    # T305 - 部分 ID 存在部分不存在
    um.clear_user_container()
    um.add_user(1, "user01", 20, "男")
    total_tests += 1
    result = um.delete_users_by_ids([1, 999])
    expected_status = 0
    passed = (result["status"] == expected_status and 
              len(result["data"]["success_ids"]) == 1 and 
              len(result["data"]["not_found_ids"]) == 1)
    if print_test_result("T305", "部分 ID 存在部分不存在", {"status": 0, "partial": True}, result, passed):
        passed_tests += 1
    
    # T306 - 传入空 ID 列表
    total_tests += 1
    result = um.delete_users_by_ids([])
    expected_status = 0
    passed = result["status"] == expected_status and "空" in result["message"]
    if print_test_result("T306", "传入空 ID 列表", {"status": 0}, result, passed):
        passed_tests += 1
    
    # T307 - 列表内含非法 ID
    total_tests += 1
    result = um.delete_users_by_ids([1, -5])
    expected_status = 0
    passed = result["status"] == expected_status and "不合法" in result["message"]
    if print_test_result("T307", "列表内含非法 ID", {"status": 0}, result, passed):
        passed_tests += 1
    
    # ========== 5. 联动流程集成测试 ==========
    print("\n【5. 联动流程集成测试】")
    
    # 流程 1：新增用户 → 查询验证 → 修改信息 → 查询确认修改 → 删除用户 → 查询确认删除
    um.clear_user_container()
    total_tests += 1
    flow1_passed = True
    
    # 新增
    result = um.add_user(100, "testuser", 25, "男")
    if result["status"] != 1:
        flow1_passed = False
    
    # 查询验证
    result = um.get_user_by_id(100)
    if result["status"] != 1 or result["data"]["username"] != "testuser":
        flow1_passed = False
    
    # 修改信息
    result = um.update_user(100, new_age=26)
    if result["status"] != 1 or result["data"]["age"] != 26:
        flow1_passed = False
    
    # 查询确认修改
    result = um.get_user_by_id(100)
    if result["status"] != 1 or result["data"]["age"] != 26:
        flow1_passed = False
    
    # 删除用户
    result = um.delete_user_by_id(100)
    if result["status"] != 1:
        flow1_passed = False
    
    # 查询确认删除
    result = um.get_user_by_id(100)
    if result["status"] != 0:
        flow1_passed = False
    
    if print_test_result("流程 1", "完整 CRUD 流程", {"status": "全部成功"}, {"flow1_passed": flow1_passed}, flow1_passed):
        passed_tests += 1
    
    # 流程 2：批量新增 → 全量查询 → 批量删除 → 清空校验
    um.clear_user_container()
    total_tests += 1
    flow2_passed = True
    
    # 批量新增
    if um.add_user(1, "user1", 20, "男")["status"] != 1:
        flow2_passed = False
    if um.add_user(2, "user2", 25, "女")["status"] != 1:
        flow2_passed = False
    if um.add_user(3, "user3", 30, "未知")["status"] != 1:
        flow2_passed = False
    
    # 全量查询
    result = um.get_all_users()
    if result["status"] != 1 or len(result["data"]) != 3:
        flow2_passed = False
    
    # 批量删除
    result = um.delete_users_by_ids([1, 2, 3])
    if result["status"] != 1:
        flow2_passed = False
    
    # 清空校验
    result = um.get_all_users()
    if result["status"] != 1 or len(result["data"]) != 0:
        flow2_passed = False
    
    if print_test_result("流程 2", "批量操作流程", {"status": "全部成功"}, {"flow2_passed": flow2_passed}, flow2_passed):
        passed_tests += 1
    
    # 流程 3：连续多次非法操作，校验系统不会崩溃、数据不乱码
    um.clear_user_container()
    total_tests += 1
    flow3_passed = True
    
    try:
        # 连续非法操作
        um.add_user(-1, "", -100, "非法")
        um.get_user_by_id("字符串")
        um.update_user(0)
        um.delete_user_by_id(None)
        um.delete_users_by_ids("不是列表")
        
        # 数据容器应该还是空的
        container = um.get_user_container()
        if not isinstance(container, dict):
            flow3_passed = False
    except Exception as e:
        flow3_passed = False
    
    if print_test_result("流程 3", "异常操作稳定性", {"status": "不崩溃"}, {"flow3_passed": flow3_passed}, flow3_passed):
        passed_tests += 1
    
    # ========== 测试结果汇总 ==========
    print("\n" + "=" * 60)
    print(f"测试汇总：{passed_tests}/{total_tests} 通过")
    if passed_tests == total_tests:
        print("[SUCCESS] 所有测试用例通过！")
    else:
        print(f"[FAILED] 有 {total_tests - passed_tests} 个测试用例失败")
    print("=" * 60)
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
