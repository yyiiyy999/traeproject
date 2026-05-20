SPEC - 项目开发规范文档
1. 项目基本信息
项目名称：Practice07 标准开发实践项目
开发范式：SPEC 范式（SPEC → Requirement → API → Test）
开发目标：完成文件规范定义、接口设计、代码开发与自动化测试全流程
适用场景：课程实践作业、标准化开发训练
2. 项目核心目标
遵循 SPEC 规范完成 4 类核心文档的编写：spec.md/requirement.md/api.md/test.md
基于文档完成代码开发
按照测试用例完成验证，确保程序运行稳定、结果正确
3. 开发流程规范
需求定义阶段：依据 spec.md 完成 requirement.md 需求拆解
接口设计阶段：依据 requirement.md 完成 api.md 接口与伪代码设计
开发实现阶段：严格按照 api.md 定义实现功能代码
测试验证阶段：按照 test.md 用例执行测试，修复问题直至全部通过
4. 文档职责规范
spec.md：项目总规划、目标、流程、规范
requirement.md：详细功能需求、输入输出、业务规则
api.md：函数定义、参数、返回值、伪代码逻辑
test.md：测试场景、测试用例、预期结果、测试步骤
5. 交付物要求
新建目录 practice07
目录中包含 4 个规范文档：spec.md、requirement.md、api.md、test.md
基于文档开发可运行的功能代码
所有测试用例执行通过
6. 约束与规则
所有文档必须遵循 Markdown 格式
接口设计必须清晰、无歧义
伪代码必须可直接翻译成代码
测试用例必须覆盖正常、异常边界场景