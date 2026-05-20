# 用户信息管理系统
# 依据 api.md 接口文档实现

# 全局用户数据容器，key 为用户 ID（正整数），value 为用户信息字典
user_container = {}


# ========== 通用校验函数 ==========
def validate_user_id(user_id):
    """校验用户 ID 合法性（正整数）"""
    if not isinstance(user_id, int) or user_id <= 0:
        return False, "ID 不合法，需为正整数"
    return True, ""


def validate_username(username):
    """校验用户名合法性（2-10 位，字母、数字、下划线）"""
    if not isinstance(username, str) or len(username) < 2 or len(username) > 10:
        return False, "用户名长度需为 2-10 位"
    for char in username:
        if not (char.isalpha() or char.isdigit() or char == '_'):
            return False, "用户名仅允许包含字母、数字、下划线"
    return True, ""


def validate_age(age):
    """校验年龄合法性（1-120 岁，正整数）"""
    if not isinstance(age, int) or age < 1 or age > 120:
        return False, "年龄需为 1-120 岁的正整数"
    return True, ""


def validate_gender(gender):
    """校验性别合法性（仅允许男、女、未知）"""
    valid_genders = ["男", "女", "未知"]
    if not isinstance(gender, str) or gender not in valid_genders:
        return False, "性别仅允许输入'男'、'女'、'未知'"
    return True, ""


# ========== 用户新增模块 ==========
def add_user(user_id, username, age, gender):
    """
    用户新增功能
    :param user_id: int, 用户 ID，正整数
    :param username: str, 用户名，2-10 位，字母、数字、下划线
    :param age: int, 年龄，1-120 岁
    :param gender: str, 性别，男/女/未知
    :return: dict, 标准返回格式
    """
    # 1. 校验所有输入参数
    id_valid, id_msg = validate_user_id(user_id)
    if not id_valid:
        return {"status": 0, "message": id_msg, "data": {}}
    
    username_valid, username_msg = validate_username(username)
    if not username_valid:
        return {"status": 0, "message": username_msg, "data": {}}
    
    age_valid, age_msg = validate_age(age)
    if not age_valid:
        return {"status": 0, "message": age_msg, "data": {}}
    
    gender_valid, gender_msg = validate_gender(gender)
    if not gender_valid:
        return {"status": 0, "message": gender_msg, "data": {}}
    
    # 2. 校验用户 ID 是否已存在
    if user_id in user_container:
        return {"status": 0, "message": f"用户 ID {user_id} 已存在", "data": {}}
    
    # 3. 新增用户到数据容器
    user_info = {
        "id": user_id,
        "username": username,
        "age": age,
        "gender": gender
    }
    user_container[user_id] = user_info
    
    # 4. 返回成功结果
    return {
        "status": 1,
        "message": "用户新增成功",
        "data": user_info
    }


# ========== 用户查询模块 ==========
def get_user_by_id(user_id):
    """
    单个用户查询功能
    :param user_id: int, 要查询的用户 ID
    :return: dict, 标准返回格式
    """
    # 1. 校验用户 ID 合法性
    id_valid, id_msg = validate_user_id(user_id)
    if not id_valid:
        return {"status": 0, "message": "查询 ID 不合法", "data": {}}
    
    # 2. 查询用户是否存在
    if user_id not in user_container:
        return {"status": 0, "message": "未找到该用户", "data": {}}
    
    # 3. 返回查询到的用户信息
    user_info = user_container[user_id]
    return {
        "status": 1,
        "message": "查询成功",
        "data": user_info
    }


def get_all_users():
    """
    批量查询所有用户功能
    :return: dict, 标准返回格式
    """
    # 1. 提取所有用户信息，转换为列表
    user_list = [user_info for user_id, user_info in user_container.items()]
    
    # 2. 返回查询结果
    return {
        "status": 1,
        "message": "查询成功",
        "data": user_list
    }


# ========== 用户修改模块 ==========
def update_user(user_id, new_username=None, new_age=None, new_gender=None):
    """
    用户修改功能
    :param user_id: int, 要修改的用户 ID
    :param new_username: str, 可选，修改后的用户名
    :param new_age: int, 可选，修改后的年龄
    :param new_gender: str, 可选，修改后的性别
    :return: dict, 标准返回格式
    """
    # 1. 校验用户 ID 合法性及是否存在
    id_valid, id_msg = validate_user_id(user_id)
    if not id_valid:
        return {"status": 0, "message": "修改 ID 不合法", "data": {}}
    
    if user_id not in user_container:
        return {"status": 0, "message": "未找到该用户", "data": {}}
    
    # 2. 校验是否修改了至少一个字段
    if new_username is None and new_age is None and new_gender is None:
        return {"status": 0, "message": "未修改任何字段", "data": {}}
    
    # 3. 校验修改字段的合法性（仅校验传入的字段）
    if new_username is not None:
        username_valid, username_msg = validate_username(new_username)
        if not username_valid:
            return {"status": 0, "message": username_msg, "data": {}}
    
    if new_age is not None:
        age_valid, age_msg = validate_age(new_age)
        if not age_valid:
            return {"status": 0, "message": age_msg, "data": {}}
    
    if new_gender is not None:
        gender_valid, gender_msg = validate_gender(new_gender)
        if not gender_valid:
            return {"status": 0, "message": gender_msg, "data": {}}
    
    # 4. 更新用户信息
    user_info = user_container[user_id]
    if new_username is not None:
        user_info["username"] = new_username
    if new_age is not None:
        user_info["age"] = new_age
    if new_gender is not None:
        user_info["gender"] = new_gender
    
    # 更新数据容器中的用户信息
    user_container[user_id] = user_info
    
    # 5. 返回成功结果
    return {
        "status": 1,
        "message": "用户修改成功",
        "data": user_info
    }


# ========== 用户删除模块 ==========
def delete_user_by_id(user_id):
    """
    单个用户删除功能
    :param user_id: int, 要删除的用户 ID
    :return: dict, 标准返回格式
    """
    # 1. 校验用户 ID 合法性
    id_valid, id_msg = validate_user_id(user_id)
    if not id_valid:
        return {"status": 0, "message": "删除 ID 不合法", "data": {}}
    
    # 2. 查询用户是否存在
    if user_id not in user_container:
        return {"status": 0, "message": "未找到该用户", "data": {}}
    
    # 3. 删除用户
    del user_container[user_id]
    
    # 4. 返回成功结果
    return {
        "status": 1,
        "message": "用户删除成功",
        "data": {}
    }


def delete_users_by_ids(user_ids):
    """
    批量用户删除功能
    :param user_ids: list, 要删除的用户 ID 列表
    :return: dict, 标准返回格式
    """
    # 1. 校验参数是否为列表
    if not isinstance(user_ids, list):
        return {"status": 0, "message": "删除 ID 不合法", "data": {}}
    
    # 2. 校验列表是否为空
    if len(user_ids) == 0:
        return {"status": 0, "message": "批量删除 ID 列表为空", "data": {}}
    
    # 3. 校验所有 ID 的合法性
    for uid in user_ids:
        id_valid, id_msg = validate_user_id(uid)
        if not id_valid:
            return {"status": 0, "message": "删除 ID 不合法", "data": {}}
    
    # 4. 执行批量删除
    success_ids = []
    not_found_ids = []
    
    for uid in user_ids:
        if uid in user_container:
            del user_container[uid]
            success_ids.append(uid)
        else:
            not_found_ids.append(uid)
    
    # 5. 返回结果
    if len(not_found_ids) == 0:
        # 全部删除成功
        return {
            "status": 1,
            "message": "批量删除成功",
            "data": {"success_ids": success_ids, "not_found_ids": []}
        }
    else:
        # 部分删除失败
        return {
            "status": 0,
            "message": "批量删除部分失败",
            "data": {"success_ids": success_ids, "not_found_ids": not_found_ids}
        }


# ========== 辅助函数（用于测试） ==========
def clear_user_container():
    """清空用户容器，用于测试"""
    global user_container
    user_container = {}


def get_user_container():
    """获取用户容器，用于测试验证"""
    return user_container


if __name__ == "__main__":
    # 简单测试
    print("=== 用户信息管理系统 ===")
    
    # 测试新增
    result = add_user(1, "user01", 20, "男")
    print(f"新增用户：{result}")
    
    # 测试查询
    result = get_user_by_id(1)
    print(f"查询用户：{result}")
    
    # 测试修改
    result = update_user(1, new_username="user02")
    print(f"修改用户：{result}")
    
    # 测试删除
    result = delete_user_by_id(1)
    print(f"删除用户：{result}")
    
    print("=== 测试完成 ===")
