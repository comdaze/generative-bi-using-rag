import json
import logging
import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

RDS_MYSQL_USERNAME = os.getenv('RDS_MYSQL_USERNAME')
RDS_MYSQL_PASSWORD = os.getenv('RDS_MYSQL_PASSWORD')
RDS_MYSQL_HOST = os.getenv('RDS_MYSQL_HOST')
RDS_MYSQL_PORT = os.getenv('RDS_MYSQL_PORT')
RDS_MYSQL_DBNAME = os.getenv('RDS_MYSQL_DBNAME')

RDS_PQ_SCHEMA = os.getenv('RDS_PQ_SCHEMA')

BEDROCK_REGION = os.getenv('BEDROCK_REGION')

DYNAMODB_AWS_REGION = os.getenv('DYNAMODB_AWS_REGION')
OPENSEARCH_REGION = os.getenv('AOS_AWS_REGION')

AOS_HOST = os.getenv('AOS_HOST')
AOS_PORT = os.getenv('AOS_PORT')
AOS_USER = os.getenv('AOS_USER')
AOS_PASSWORD = os.getenv('AOS_PASSWORD')
AOS_DOMAIN = os.getenv('AOS_DOMAIN')

AOS_INDEX = os.getenv('AOS_INDEX')
AOS_INDEX_NER = os.getenv('AOS_INDEX_NER')
AOS_INDEX_AGENT = os.getenv('AOS_INDEX_AGENT')
QUERY_LOG_INDEX = os.getenv('QUERY_LOG_INDEX')

EMBEDDING_DIMENSION = os.getenv('EMBEDDING_DIMENSION')

AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION')

OPENSEARCH_TYPE = os.getenv('OPENSEARCH_TYPE')

OPENSEARCH_SECRETS_URL_HOST = os.getenv('OPENSEARCH_SECRETS_URL_HOST', 'opensearch-host-url')

OPENSEARCH_SECRETS_USERNAME_PASSWORD = os.getenv('OPENSEARCH_SECRETS_USERNAME_PASSWORD', 'opensearch-master-user')

BEDROCK_SECRETS_AK_SK = os.getenv('BEDROCK_SECRETS_AK_SK', '')

SAGEMAKER_SQL_REGION = os.getenv('SAGEMAKER_SQL_REGION', '')


def get_opensearch_parameter():
    try:
        session = boto3.session.Session()
        sm_client = session.client(service_name='secretsmanager', region_name=AWS_DEFAULT_REGION)
        master_user = sm_client.get_secret_value(SecretId=OPENSEARCH_SECRETS_URL_HOST)['SecretString']
        data = json.loads(master_user)
        es_host_name = data.get('host')
        # cluster endpoint, for example: my-test-domain.us-east-1.es.amazonaws.com/
        # host = es_host_name + '/' if es_host_name[-1] != '/' else es_host_name
        host = es_host_name

        sm_client = session.client(service_name='secretsmanager', region_name=AWS_DEFAULT_REGION)
        master_user = sm_client.get_secret_value(SecretId=OPENSEARCH_SECRETS_USERNAME_PASSWORD)['SecretString']
        data = json.loads(master_user)
        username = data.get('username')
        password = data.get('password')
        port = 443
        return host, port, username, password
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e


def get_bedrock_parameter():
    bedrock_ak_sk_info = {}
    try:
        session = boto3.session.Session()
        sm_client = session.client(service_name='secretsmanager', region_name=AWS_DEFAULT_REGION)
        if BEDROCK_SECRETS_AK_SK is not None and BEDROCK_SECRETS_AK_SK != "":
            bedrock_info = sm_client.get_secret_value(SecretId=BEDROCK_SECRETS_AK_SK)['SecretString']
            data = json.loads(bedrock_info)
            access_key = data.get('access_key_id')
            secret_key = data.get('secret_access_key')
            bedrock_ak_sk_info['access_key_id'] = access_key
            bedrock_ak_sk_info['secret_access_key'] = secret_key
        else:
            return bedrock_ak_sk_info
    except ClientError as e:
        logging.error(e)
    return bedrock_ak_sk_info


if OPENSEARCH_TYPE == "service":
    opensearch_host, opensearch_port, opensearch_username, opensearch_password = get_opensearch_parameter()
    AOS_HOST = opensearch_host
    AOS_PORT = opensearch_port
    AOS_USER = opensearch_username
    AOS_PASSWORD = opensearch_password

opensearch_info = {
    'host': AOS_HOST,
    'port': AOS_PORT,
    'username': AOS_USER,
    'password': AOS_PASSWORD,
    'domain': AOS_DOMAIN,
    'region': OPENSEARCH_REGION,
    'sql_index': AOS_INDEX,
    'ner_index': AOS_INDEX_NER,
    'agent_index': AOS_INDEX_AGENT,
    'embedding_dimension': EMBEDDING_DIMENSION
}

query_log_name = os.getenv("QUERY_LOG_INDEX", "genbi_query_logging")

bedrock_ak_sk_info = get_bedrock_parameter()

# 初始化嵌入模型信息
embedding_info = {
    "embedding_platform": os.getenv('EMBEDDING_PLATFORM'),
    "embedding_name": os.getenv('EMBEDDING_NAME'),
    "embedding_dimension": int(os.getenv('EMBEDDING_DIMENSION', 1536)),
    "embedding_region": os.getenv('EMBEDDING_REGION', AWS_DEFAULT_REGION),
    "br_client_url": os.getenv('BR_CLIENT_URL', ""),
    "br_client_key": os.getenv('BR_CLIENT_KEY', "")
}

# 尝试从全局设置加载默认嵌入模型
def load_default_embedding_model():
    try:
        # 避免循环导入
        from nlq.business.embedding import EmbeddingModelManagement
        # 应用默认嵌入模型设置
        EmbeddingModelManagement.apply_default_embedding_model()
        return True
    except (ImportError, Exception) as e:
        logging.warning(f"Could not load default embedding model: {str(e)}")
        return False

# 应用程序启动后尝试加载默认设置
# 这将在应用程序完全初始化后执行

if embedding_info["embedding_platform"] == "bedrock":
    SAGEMAKER_EMBEDDING_REGION = ""
    SAGEMAKER_ENDPOINT_EMBEDDING = ""
elif embedding_info["embedding_platform"] == "brclient-api":
    SAGEMAKER_EMBEDDING_REGION = ""
    SAGEMAKER_ENDPOINT_EMBEDDING = ""
else:
    SAGEMAKER_EMBEDDING_REGION = embedding_info["embedding_region"]
    SAGEMAKER_ENDPOINT_EMBEDDING = embedding_info["embedding_name"]
