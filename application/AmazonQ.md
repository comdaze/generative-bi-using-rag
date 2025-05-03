# 嵌入模型连接问题排查指南

## 问题描述
使用brclient apiplatform创建新的嵌入模型时无法连接。

## 排查步骤

### 1. 检查API URL格式
确保提供的API URL是完整且正确的，包括协议（http://或https://）。

### 2. 检查API Header
确保API Header格式正确，通常需要包含：
```json
{
  "Content-Type": "application/json"
}
```

如果API需要认证，可能还需要添加Authorization头：
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer YOUR_API_KEY"
}
```

### 3. 检查Input Format
确保Input Format格式正确，通常应该是JSON格式，例如：
```json
{
  "text": "INPUT_TEXT"
}
```
其中"INPUT_TEXT"是一个占位符，系统会自动替换为测试文本。

对于特定的模型（如Titan嵌入模型），需要使用特定的格式：
```json
{
  "model": "titan-embed-text-v2",
  "input": "INPUT_TEXT",
  "encoding_format": "float"
}
```

### 4. 检查API响应格式
确保API返回的响应包含"embedding"或"embeddings"字段，例如：
```json
{
  "embedding": [0.1, 0.2, 0.3, ...]
}
```

### 5. 网络连接问题
- 检查EC2实例的安全组设置，确保允许出站流量到API端点
- 检查API端点是否可以从EC2实例访问（可以使用curl命令测试）
- 如果API在VPC内，确保EC2实例可以访问该VPC
- 如果在Docker容器中运行，确保容器网络配置正确，允许外部访问

### 6. 测试连接
使用以下命令测试API连接：

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"text": "This is a test text for embedding generation"}' \
  YOUR_API_URL
```

对于Titan嵌入模型，使用以下命令：
```bash
curl -X POST "https://d3jg86bl5vfww5.cloudfront.net/v1/embeddings" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "titan-embed-text-v2",
    "input": "这是一个测试文本，用于生成嵌入向量",
    "encoding_format": "float"
  }'
```

### 7. 检查错误日志
查看应用程序日志以获取更详细的错误信息：

```bash
cd /home/ec2-user/generative-bi-using-rag/application
cat logs/app.log | grep -i error | tail -50
```

在Docker环境中，使用以下命令：
```bash
docker logs 容器ID | grep -i error | tail -50
```

## 常见错误及解决方案

1. **连接超时**：检查网络连接和API端点是否可用
2. **认证失败**：检查API密钥是否正确
3. **格式错误**：检查请求和响应格式是否符合API要求
4. **维度不匹配**：确保设置的向量维度与API返回的维度匹配
5. **400 Bad Request**：检查请求体格式是否符合API要求，特别是字段名称和结构

## 测试方法

1. 在Model Provider页面中，选择"Embedding Models"标签页
2. 点击"Create New Embedding Model"
3. 填写模型信息：
   - Model Name: 给模型起一个名称
   - Platform: 选择"brclient-api"
   - Model Name/Endpoint: 输入模型名称
   - Vector Dimension: 设置向量维度（通常为1536或768）
   - API URL: 输入完整的API URL
   - API Key: 如果需要，输入API密钥
   - Input Format: 设置输入格式，例如`{"model": "titan-embed-text-v2", "input": "INPUT_TEXT", "encoding_format": "float"}`
4. 在Test Text区域输入测试文本
5. 点击"Test Connection"按钮测试连接

如果测试成功，将显示生成的嵌入向量样本。如果失败，将显示错误信息。

## 修改默认嵌入模型后主页面错误处理

如果在Global Settings中修改默认嵌入模型后，在主页面看到"初始化示例实体时出错，但不影响系统使用: list indices must be integers or slices, not str"错误，这是因为嵌入模型返回的响应格式与系统期望的格式不匹配。

### 解决方案

在处理嵌入向量的代码中添加安全检查：

```python
try:
    # 假设embedding是从API获取的嵌入向量
    if isinstance(embedding, dict):
        # 如果是字典，尝试获取嵌入向量数组
        if 'embedding' in embedding:
            embedding = embedding['embedding']
        elif 'embeddings' in embedding:
            embedding = embedding['embeddings']
        else:
            # 如果找不到嵌入向量，创建一个空列表
            embedding = []
    
    # 确保embedding是一个列表
    if not isinstance(embedding, list):
        embedding = []
    
    # 现在可以安全地使用索引访问列表元素
    # 例如: first_element = embedding[0]
except Exception as e:
    logger.error(f"Error processing embedding: {str(e)}")
    # 使用空列表作为后备
    embedding = []
```

这种方法可以确保在处理不同格式的嵌入向量响应时不会出现类型错误，提高系统的健壮性。
