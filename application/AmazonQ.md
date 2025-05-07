# 添加用户自定义凭证(AK/SK)功能实现说明

## 功能概述

为Model Provider页面添加用户自定义凭证(AK/SK)功能，使用户可以在创建或更新Bedrock相关模型时提供自己的AWS凭证。

## 实现方式

1. 在以下三种模型类型的表单中添加AK/SK输入字段：
   - Bedrock API
   - Bedrock Anthropic Model
   - Bedrock Amazon Model

2. 将用户提供的凭证以JSON格式存储在模型的`input_format`字段中：
   ```json
   {
     "credentials": {
       "access_key_id": "用户的访问密钥ID",
       "secret_access_key": "用户的秘密访问密钥"
     }
   }
   ```

3. 修改`get_bedrock_client()`函数，使其能够接受并使用用户提供的凭证创建Bedrock客户端。

4. 在模型调用函数中，从模型配置中提取用户凭证并传递给`get_bedrock_client()`函数。

## 测试连接流程

1. 用户填写表单，包括模型信息和可选的AK/SK凭证。
2. 用户点击"测试连接"按钮。
3. 系统从表单中提取凭证信息。
4. 系统使用提供的凭证创建Bedrock客户端。
5. 系统使用该客户端调用Bedrock API进行测试。
6. 系统返回测试结果，显示连接是否成功。

## 凭证传递流程

1. 用户提供的凭证存储在模型的`input_format`字段中。
2. 当调用模型时，系统从`input_format`中提取凭证。
3. 系统将凭证传递给`get_bedrock_client()`函数。
4. `get_bedrock_client()`函数使用这些凭证创建Bedrock客户端。
5. 系统使用该客户端调用Bedrock API。

## 安全考虑

1. 凭证在UI中以密码形式显示，不会明文显示。
2. 凭证存储在数据库中，应确保数据库安全。
3. 日志中不应记录完整的凭证信息。
