import json
import boto3
from botocore.config import Config
import sys
import os
import logging

# 添加项目根目录到 Python 路径，以便导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置基本日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_converse_api(model_id, region, access_key=None, secret_key=None):
    """
    测试 Bedrock Converse API
    
    Args:
        model_id (str): Bedrock 模型 ID
        region (str): AWS 区域
        access_key (str, optional): AWS 访问密钥 ID
        secret_key (str, optional): AWS 秘密访问密钥
    """
    print(f"测试 Converse API - 模型: {model_id}, 区域: {region}")
    
    # 创建 Bedrock 客户端
    config = Config(
        region_name=region,
        signature_version='v4',
        retries={'max_attempts': 10, 'mode': 'standard'},
        read_timeout=600
    )
    
    # 使用提供的凭证或默认凭证
    if access_key and secret_key:
        print("使用提供的凭证创建客户端")
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            config=config,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
    else:
        print("使用默认凭证创建客户端")
        bedrock = boto3.client(service_name='bedrock-runtime', config=config)
    
    # 准备 Converse API 请求 - 注意格式必须正确
    system = [{"text": "你是一个友好的助手，请用中文回答问题。"}]
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "text": "你好，请介绍一下自己。"
                }
            ]
        }
    ]
    
    inference_config = {
        "temperature": 0.7,
        "maxTokens": 512,
        "topP": 0.8
    }
    
    try:
        print("调用 Converse API...")
        response = bedrock.converse(
            modelId=model_id,
            system=system,
            messages=messages,
            inferenceConfig=inference_config
        )
        
        print("\n=== Converse API 调用成功 ===")
        print(f"回复内容: {response['output']['message']['content'][0]['text']}")
        print(f"停止原因: {response.get('stopReason', 'N/A')}")
        print(f"令牌使用: {response.get('usage', {})}")
        return True, response
        
    except Exception as e:
        print(f"\n=== Converse API 调用失败 ===")
        print(f"错误信息: {str(e)}")
        
        # 尝试使用传统的 invoke_model API
        print("\n尝试使用传统的 invoke_model API...")
        try:
            # 根据模型类型准备请求体
            if "anthropic" in model_id.lower() or "claude" in model_id.lower():
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1024,
                    "temperature": 0.7,
                    "system": "你是一个友好的助手，请用中文回答问题。",
                    "messages": [{"role": "user", "content": "你好，请介绍一下自己。"}]
                })
            elif "amazon" in model_id.lower() or "titan" in model_id.lower():
                body = json.dumps({
                    "inputText": "System: 你是一个友好的助手，请用中文回答问题。\n\nHuman: 你好，请介绍一下自己。",
                    "textGenerationConfig": {
                        "maxTokenCount": 1024,
                        "temperature": 0.7,
                        "topP": 0.8
                    }
                })
            else:
                body = json.dumps({
                    "prompt": "你是一个友好的助手，请用中文回答问题。\n\n你好，请介绍一下自己。",
                    "max_tokens": 1024,
                    "temperature": 0.7
                })
            
            response = bedrock.invoke_model(body=body, modelId=model_id)
            response_body = json.loads(response.get('body').read())
            
            print("\n=== invoke_model API 调用成功 ===")
            print(f"响应: {response_body}")
            return False, response_body
            
        except Exception as invoke_error:
            print(f"\n=== invoke_model API 也调用失败 ===")
            print(f"错误信息: {str(invoke_error)}")
            return False, str(invoke_error)

# 使用示例
if __name__ == "__main__":
    # 替换为您的模型 ID 和区域
    model_id = "us.anthropic.claude-3-5-sonnet-20240620-v1:0"  # 或其他支持的模型
    region = "us-east-1"  # 替换为您的区域
    
    # 可选: 提供 AWS 凭证
    access_key = ""  # 替换为您的访问密钥 ID
    secret_key = ""  # 替换为您的秘密访问密钥
    
    success, response = test_converse_api(model_id, region, access_key, secret_key)
    
    if success:
        print("\n测试结果: Converse API 可用 ✓")
    else:
        print("\n测试结果: Converse API 不可用，但 invoke_model API 可能可用 ✗")
