# 使用 Bedrock Converse API 改进模型连接功能

当前的 `bedrock_amazon_model_connect` 函数仅支持 Amazon Nova 模型，我们通过使用 Bedrock Converse API 对其进行了改进，使其能够支持更多类型的模型。

## 当前限制

现有函数存在以下限制：
- 仅为 Amazon Nova 模型设计
- 假设特定的负载结构
- 修改负载的方式仅适用于 Nova 模型
- 函数名称表明它仅适用于 Amazon 模型

## 改进方案

我们创建了一个新的 `/home/ec2-user/generative-bi-using-rag/application/utils/converse.py` 文件，实现了以下功能：

### 1. bedrock_model_connect 函数

这个函数使用 Bedrock Converse API 连接到任何 Bedrock 模型，主要特点：

- 支持所有 Bedrock 模型类型（Amazon、Anthropic、Meta、Mistral、Cohere 等）
- 自动处理模型 ID 前缀
- 支持用户自定义凭证（AK/SK）
- 使用统一的 Converse API 接口
- 包含错误处理和日志记录
- 如果 Converse API 失败，会自动回退到传统的 invoke_model API

### 2. test_bedrock_model_connect 函数

这个函数用于测试 Bedrock 模型连接：

- 从会话状态中获取用户凭证
- 检查必要的参数
- 调用 bedrock_model_connect 函数进行测试
- 显示测试结果

### 3. display_new_bedrock_model 函数

这个函数显示创建新的 Bedrock 模型的表单：

- 支持选择不同的模型类型（Amazon、Anthropic、Meta 等）
- 根据模型类型提供默认的输入负载模板和输出格式
- 支持输入用户凭证
- 包含测试连接和添加模型的功能
- 添加模型后自动更新提示模板

### 4. display_update_bedrock_model 函数

这个函数显示更新现有 Bedrock 模型的表单：

- 显示当前模型信息
- 支持更新输入负载和输出格式
- 支持更新用户凭证
- 包含测试连接和更新模型的功能

### 5. update_profile_prompts 函数

这个辅助函数用于更新所有配置文件的模型提示：

- 获取所有配置文件
- 为新模型添加系统提示和用户提示
- 更新配置文件的提示映射

## 实施步骤

1. 创建 `/home/ec2-user/generative-bi-using-rag/application/utils/converse.py` 文件
2. 在 Model Provider 页面中引入这些函数
3. 替换原来的特定模型连接函数
4. 更新模型添加和更新功能以使用新的通用函数

## 优势

- 代码更加简洁灵活
- 支持所有 Bedrock 模型类型
- 无需为每种模型类型编写不同的处理逻辑
- 自动检测模型类型并适配相应的请求格式
- 保持与现有 Nova 模型配置的向后兼容性
- 更好的错误处理和日志记录
- 更容易维护和扩展
