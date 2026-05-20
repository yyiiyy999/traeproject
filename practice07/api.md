API - 项目接口文档
1. 文档说明
本文档依据 spec.md 规范及 requirement.md 需求文档编写，定义用户信息管理系统所有核心功能的接口（函数），包含函数名称、参数说明、返回值说明及伪代码实现，为后续代码开发提供唯一接口标准，确保开发过程与需求一致。
本文档需与 requirement.md 保持完全一致，若接口有变更，需同步更新 requirement.md 中的对应需求，确保接口与需求闭环；伪代码需具备可移植性，可直接翻译成对应编程语言（如 Python、Java 等）的实际代码。
2. 通用说明
2.1 数据容器定义
采用内存字典（Dictionary）作为用户信息存储容器，模拟数据存储，无需持久化，容器定义如下：
// 全局用户数据容器，key为用户ID（正整数），value为用户信息字典
user_container = {} 
// 用户信息字典结构：{id: 正整数, username: 字符串, age: 正整数, gender: 字符串}
2.2 通用返回格式
所有接口返回值均为字典（Dictionary），统一格式如下，根据操作结果动态调整对应字段：
{
    "status": 状态码（1=成功，0=失败）,
    "message": 操作提示信息（中文，清晰说明结果）,
    "data": 返回数据（可选，如用户信息、ID列表等，失败时可为空）
}
2.3 通用校验函数
定义通用参数校验函数，供各功能接口调用，减少代码冗余，确保校验规则统一（符合 requirement.md 输入要求）：
// 校验用户ID合法性（正整数）
function validate_user_id(user_id):
    if 类型(user_id) != 整数 或 user_id <= 0:
        return False, "ID不合法，需为正整数"
    return True, ""

// 校验用户名合法性（2-10位，字母、数字、下划线）
function validate_username(username):
    if 类型(username) != 字符串 或 len(username) < 2 或 len(username) > 10:
        return False, "用户名长度需为2-10位"
    for 字符 in username:
        if 字符 not in 字母 + 数字 + "_":
            return False, "用户名仅允许包含字母、数字、下划线"
    return True, ""

// 校验年龄合法性（1-120岁，正整数）
function validate_age(age):
    if 类型(age) != 整数 或 age < 1 或 age > 120:
        return False, "年龄需为1-120岁的正整数"
    return True, ""

// 校验性别合法性（仅允许男、女、未知）
function validate_gender(gender):
    valid_genders = ["男", "女", "未知"]
    if 类型(gender) != 字符串 或 gender not in valid_genders:
        return False, "性别仅允许输入'男'、'女'、'未知'"
    return True, ""
3. 核心接口定义（按功能模块划分）
3.1 用户新增模块接口
3.1.1 接口名称
add_user(user_id, username, age, gender)
3.1.2 功能描述
接收用户输入的ID、用户名、年龄、性别，校验通过后将用户信息添加到user_container中，实现用户新增功能，符合 requirement.md 3.2.1 需求。
3.1.3 参数说明
- user_id：int，必填，用户唯一标识，正整数，不可重复
- username：str，必填，用户名，2-10位，仅含字母、数字、下划线
- age：int，必填，用户年龄，1-120岁的正整数
- gender：str，必填，用户性别，仅允许"男"、"女"、"未知"
3.1.4 返回值说明
- 成功返回：{"status": 1, "message": "用户新增成功", "data": {"id": user_id, "username": username, "age": age, "gender": gender}}
- 失败返回：{"status": 0, "message": 具体失败原因（如ID已存在、参数不合法）, "data": {}}
3.1.5 伪代码实现
function add_user(user_id, username, age, gender):
    // 1. 校验所有输入参数
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
    
    // 2. 校验用户ID是否已存在
    if user_id in user_container:
        return {"status": 0, "message": f"用户ID {user_id} 已存在", "data": {}}
    
    // 3. 新增用户到数据容器
    user_info = {
        "id": user_id,
        "username": username,
        "age": age,
        "gender": gender
    }
    user_container[user_id] = user_info
    
    // 4. 返回成功结果
    return {
        "status": 1,
        "message": "用户新增成功",
        "data": user_info
    }
3.2 用户查询模块接口
3.2.1 接口1：单个用户查询
接口名称：get_user_by_id(user_id)
功能描述
根据输入的用户ID，查询并返回该用户的完整信息，符合 requirement.md 3.2.2 中单个查询需求。
参数说明
- user_id：int，必填，要查询的用户ID，正整数
返回值说明
- 成功返回：{"status": 1, "message": "查询成功", "data": {"id": user_id, "username": username, "age": age, "gender": gender}}
- 失败返回：{"status": 0, "message": "查询ID不合法" 或 "未找到该用户", "data": {}}
伪代码实现
function get_user_by_id(user_id):
    // 1. 校验用户ID合法性
    id_valid, id_msg = validate_user_id(user_id)
    if not id_valid:
        return {"status": 0, "message": "查询ID不合法", "data": {}}
    
    // 2. 查询用户是否存在
    if user_id not in user_container:
        return {"status": 0, "message": "未找到该用户", "data": {}}
    
    // 3. 返回查询到的用户信息
    user_info = user_container[user_id]
    return {
        "status": 1,
        "message": "查询成功",
        "data": user_info
    }
3.2.2 接口2：批量查询所有用户
接口名称：get_all_users()
功能描述
无需输入参数，查询并返回所有用户的信息列表，若无用户则返回空列表，符合 requirement.md 3.2.2 中批量查询需求。
参数说明
无参数
返回值说明
- 成功返回：{"status": 1, "message": "查询成功", "data": [用户信息字典1, 用户信息字典2, ...]}
- 无用户时返回：{"status": 1, "message": "查询成功", "data": []}
伪代码实现
function get_all_users():
    // 1. 提取所有用户信息，转换为列表
    user_list = [user_info for user_id, user_info in user_container.items()]
    
    // 2. 返回查询结果
    return {
        "status": 1,
        "message": "查询成功",
        "data": user_list
    }
3.3 用户修改模块接口
3.3.1 接口名称
update_user(user_id, new_username=None, new_age=None, new_gender=None)
3.3.2 功能描述
根据输入的用户ID定位用户，接收修改后的用户名、年龄、性别（至少修改一个字段），校验通过后更新用户信息，符合 requirement.md 3.2.3 需求。
3.3.3 参数说明
- user_id：int，必填，要修改的用户ID，正整数，且必须存在于user_container中
- new_username：str，可选，修改后的用户名，符合用户名校验规则（2-10位，字母、数字、下划线）
- new_age：int，可选，修改后的年龄，符合年龄校验规则（1-120岁正整数）
- new_gender：str，可选，修改后的性别，符合性别校验规则（仅"男"、"女"、"未知"）
3.3.4 返回值说明
- 成功返回：{"status": 1, "message": "用户修改成功", "data": 修改后的用户信息字典}
- 失败返回：{"status": 0, "message": 具体失败原因（如未找到用户、参数不合法、未修改任何字段）, "data": {}}
3.3.5 伪代码实现
function update_user(user_id, new_username=None, new_age=None, new_gender=None):
    // 1. 校验用户ID合法性及是否存在
    id_valid, id_msg = validate_user_id(user_id)
    if not id_valid:
        return {"status": 0, "message": "修改ID不合法", "data": {}}
    
    if user_id not in user_container:
        return {"status": 0, "message": "未找到该用户", "data": {}}
    
    // 2. 校验是否修改了至少一个字段
    if new_username is None and new_age is None and new_gender is None:
        return {"status": 0, "message": "未修改任何字段", "data": {}}
    
    // 3. 校验修改字段的合法性（仅校验传入的字段）
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
    
    // 4. 更新用户信息
    user_info = user_container[user_id]
    if new_username is not None:
        user_info["username"] = new_username
    if new_age is not None:
        user_info["age"] = new_age
    if new_gender is not None:
        user_info["gender"] = new_gender
    
    // 更新数据容器中的用户信息
    user_container[user_id] = user_info
    
    // 5. 返回成功结果
    return {
        "status": 1,
        "message": "用户修改成功",
        "data": user_info
    }
3.4 用户删除模块接口
3.4.1 接口1：单个用户删除
接口名称：delete_user_by_id(user_id)
功能描述
根据输入的用户ID，删除该用户的信息，符合 requirement.md 3.2.4 中单个删除需求。
参数说明
- user_id：int，必填，要删除的用户ID，正整数
返回值说明
- 成功返回：{"status": 1, "message": "用户删除成功", "data": {}}
- 失败返回：{"status": 0, "message": "删除ID不合法" 或 "未找到该用户", "data": {}}
伪代码实现
function delete_user_by_id(user_id):
    // 1. 校验用户ID合法性
    id_valid, id_msg = validate_user_id(user_id)
    if not id_valid:
        return {"status": 0, "message": "删除ID不合法", "data": {}}
    
    // 2. 校验用户是否存在
    if user_id not in user_container:
        return {"status": 0, "message": "未找到该用户", "data": {}}
    
    // 3. 删除用户信息
    del user_container[user_id]
    
    // 4. 返回成功结果
    return {"status": 1, "message": "用户删除成功", "data": {}}
3.4.2 接口2：批量用户删除
接口名称：delete_users_by_ids(user_id_list)
功能描述
根据输入的用户ID列表，批量删除对应用户的信息，即使部分ID不存在，也执行存在ID的删除操作，符合 requirement.md 3.2.4 中批量删除需求。
参数说明
- user_id_list：list，必填，要删除的用户ID列表，列表中每个元素为正整数，且列表非空
返回值说明
- 全部成功：{"status": 1, "message": "批量删除成功", "data": {"success_ids": [删除成功的ID列表], "fail_ids": []}}
- 部分成功：{"status": 1, "message": "批量删除部分失败", "data": {"success_ids": [删除成功的ID列表], "fail_ids": [未找到的ID列表]}}
- 参数错误：{"status": 0, "message": "删除ID不合法" 或 "ID列表为空", "data": {}}
伪代码实现
function delete_users_by_ids(user_id_list):
    // 1. 校验ID列表非空
    if len(user_id_list) == 0:
        return {"status": 0, "message": "ID列表为空，无法执行批量删除", "data": {}}
    
    // 2. 校验列表中所有ID的合法性，筛选出合法ID
    valid_ids = []
    invalid_ids = []
    for user_id in user_id_list:
        id_valid, _ = validate_user_id(user_id)
        if id_valid:
            valid_ids.append(user_id)
        else:
            invalid_ids.append(user_id)
    
    // 3. 若存在非法ID，直接返回参数错误
    if len(invalid_ids) > 0:
        return {"status": 0, "message": f"删除ID不合法，非法ID：{invalid_ids}", "data": {}}
    
    // 4. 执行批量删除，区分成功和失败ID
    success_ids = []
    fail_ids = []
    for user_id in valid_ids:
        if user_id in user_container:
            del user_container[user_id]
            success_ids.append(user_id)
        else:
            fail_ids.append(user_id)
    
    // 5. 根据删除结果返回对应信息
    if len(fail_ids) == 0:
        return {
            "status": 1,
            "message": "批量删除成功",
            "data": {"success_ids": success_ids, "fail_ids": fail_ids}
        }
    else:
        return {
            "status": 1,
            "message": "批量删除部分失败",
            "data": {"success_ids": success_ids, "fail_ids": fail_ids}
        }
4. 接口调用说明
- 所有接口均依赖全局数据容器 user_container，调用前需确保该容器已初始化（空字典）。
- 接口调用顺序无强制要求，但新增用户后，方可执行查询、修改、删除操作。
- 所有接口均已包含参数校验逻辑，无需在调用时额外校验参数，直接传入对应参数即可。
- 伪代码中的“类型判断”“列表推导”等语法，可根据实际编程语言进行适配修改，核心逻辑保持不变。
5. 接口变更说明
若需变更接口定义（如参数、返回值、伪代码逻辑），需先修改 requirement.md 中的对应需求，再同步更新本文档，变更后需重新确认接口与需求的一致性，确保开发和测试不受影响。