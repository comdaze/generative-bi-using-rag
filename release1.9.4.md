# Generative BI Using RAG - Release Notes v1.9.4

## 中文

### 新功能

#### 增强的 LLM 管理与 Bedrock Converse API 支持
- 在 LLM 管理界面中添加了对 Amazon Bedrock Converse API 的支持
- 在 `utils/llm.py` 中实现了 `invoke_bedrock_converse` 函数以处理 Converse API 调用
- 通过 Bedrock Converse API 创建了统一的模型连接处理
- 如果 Converse API 失败，添加了自动回退到传统 invoke_model API 的功能

#### 用户自定义 AWS 凭证 (AK/SK) 支持
- 添加了用户在创建或更新 Bedrock 模型时提供自己的 AWS 凭证的功能
- 实现了将凭证以 JSON 格式安全存储在模型的 `input_format` 字段中
- 增强了模型调用函数中的凭证处理
- 在模型创建和更新表单中添加了凭证输入界面元素

### 改进
- 增强了 `get_query_intent` 和 `get_query_rewrite` 函数中的错误处理
- 改进了日志记录，以便更好地排查模型连接问题
- 为模型调用失败添加了详细的错误消息
- 通过更好的错误处理优化了模型响应提取

### 错误修复
- 修复了查询处理函数中的错误处理
- 解决了凭证验证和使用的问题
- 修复了不同模型类型的响应格式处理
- 改进了失败 API 调用的错误日志记录

### 技术细节
- Converse API 实现为所有 Bedrock 模型提供了更一致的接口
- 用户凭证以 JSON 格式安全存储在模型配置中
- 错误处理现在包括详细的日志记录，便于故障排除
- 模型调用现在支持自定义区域和凭证

---

## English

### New Features

#### Enhanced LLM Management with Bedrock Converse API Support
- Added support for Amazon Bedrock Converse API in the LLM management interface
- Implemented `invoke_bedrock_converse` function in `utils/llm.py` to handle Converse API calls
- Created unified model connection handling through Bedrock Converse API
- Added automatic fallback to traditional invoke_model API if Converse API fails

#### User-Defined AWS Credentials (AK/SK) Support
- Added ability for users to provide their own AWS credentials when creating or updating Bedrock models
- Implemented secure storage of credentials in the model's `input_format` field as JSON
- Enhanced credential handling in model invocation functions
- Added UI elements for credential input in model creation and update forms

### Improvements
- Enhanced error handling in `get_query_intent` and `get_query_rewrite` functions
- Improved logging for better troubleshooting of model connection issues
- Added detailed error messages for failed model invocations
- Optimized model response extraction with better error handling

### Bug Fixes
- Fixed error handling in query processing functions
- Resolved issues with credential validation and usage
- Fixed response format handling for different model types
- Improved error logging for failed API calls

### Technical Details
- The Converse API implementation provides a more consistent interface for all Bedrock models
- User credentials are securely stored in JSON format in the model configuration
- Error handling now includes detailed logging for easier troubleshooting
- Model invocation now supports custom regions and credentials



