import os

import boto3
from botocore.exceptions import ClientError

from utils.logging import getLogger

logger = getLogger()

# DynamoDB table name
EMBEDDING_MODEL_TABLE_NAME = 'NlqEmbeddingModelConfig'
GLOBAL_SETTINGS_TABLE_NAME = 'NlqGlobalSettings'
DYNAMODB_AWS_REGION = os.environ.get('DYNAMODB_AWS_REGION')


class EmbeddingModelEntity:

    def __init__(self, model_id: str, name: str, platform: str, model_name: str,
                 region: str = '', dimension: int = 1536, api_url: str = '', 
                 api_key: str = '', input_format: str = ''):
        self.model_id = model_id
        self.name = name
        self.platform = platform
        self.model_name = model_name
        self.region = region
        self.dimension = dimension
        self.api_url = api_url
        self.api_key = api_key
        self.input_format = input_format

    def to_dict(self):
        """Convert to DynamoDB item format"""
        return {
            'model_id': self.model_id,
            'name': self.name,
            'platform': self.platform,
            'model_name': self.model_name,
            'region': self.region,
            'dimension': self.dimension,
            'api_url': self.api_url,
            'api_key': self.api_key,
            'input_format': self.input_format
        }


class GlobalSettingEntity:

    def __init__(self, setting_key: str, setting_value: str, description: str = ''):
        self.setting_key = setting_key
        self.setting_value = setting_value
        self.description = description

    def to_dict(self):
        """Convert to DynamoDB item format"""
        return {
            'setting_key': self.setting_key,
            'setting_value': self.setting_value,
            'description': self.description
        }


class EmbeddingModelDao:

    def __init__(self, table_name_prefix=''):
        self.dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_AWS_REGION)
        self.table_name = table_name_prefix + EMBEDDING_MODEL_TABLE_NAME
        if not self.exists():
            self.create_table()
        self.table = self.dynamodb.Table(self.table_name)

    def exists(self):
        """
        Determines whether a table exists. As a side effect, stores the table in
        a member variable.

        :param table_name: The name of the table to check.
        :return: True when the table exists; otherwise, False.
        """
        try:
            table = self.dynamodb.Table(self.table_name)
            table.load()
            exists = True
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                exists = False
                logger.info("Table does not exist")
            else:
                logger.error(
                    "Couldn't check for existence of %s. Here's why: %s: %s",
                    self.table_name,
                    err.response["Error"]["Code"],
                    err.response["Error"]["Message"],
                )
                raise
        return exists

    def create_table(self):
        try:
            self.table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {"AttributeName": "model_id", "KeyType": "HASH"},  # Partition key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "model_id", "AttributeType": "S"},
                ],
                BillingMode='PAY_PER_REQUEST',
            )
            self.table.wait_until_exists()
            logger.info(f"DynamoDB Table {self.table_name} created")
        except ClientError as err:
            logger.error(
                "Couldn't create table %s. Here's why: %s: %s",
                self.table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def get_by_id(self, model_id):
        response = self.table.get_item(Key={'model_id': model_id})
        if 'Item' in response:
            return EmbeddingModelEntity(**response['Item'])
        return None

    def add(self, entity):
        self.table.put_item(Item=entity.to_dict())

    def update(self, entity):
        self.table.put_item(Item=entity.to_dict())

    def delete(self, model_id):
        self.table.delete_item(Key={'model_id': model_id})
        return True

    def get_model_list(self):
        response = self.table.scan()
        return [EmbeddingModelEntity(**item) for item in response['Items']]


class GlobalSettingsDao:

    def __init__(self, table_name_prefix=''):
        self.dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_AWS_REGION)
        self.table_name = table_name_prefix + GLOBAL_SETTINGS_TABLE_NAME
        if not self.exists():
            self.create_table()
            self.initialize_default_settings()
        self.table = self.dynamodb.Table(self.table_name)

    def exists(self):
        try:
            table = self.dynamodb.Table(self.table_name)
            table.load()
            exists = True
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                exists = False
                logger.info("Table does not exist")
            else:
                logger.error(
                    "Couldn't check for existence of %s. Here's why: %s: %s",
                    self.table_name,
                    err.response["Error"]["Code"],
                    err.response["Error"]["Message"],
                )
                raise
        return exists

    def create_table(self):
        try:
            self.table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {"AttributeName": "setting_key", "KeyType": "HASH"},  # Partition key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "setting_key", "AttributeType": "S"},
                ],
                BillingMode='PAY_PER_REQUEST',
            )
            self.table.wait_until_exists()
            logger.info(f"DynamoDB Table {self.table_name} created")
        except ClientError as err:
            logger.error(
                "Couldn't create table %s. Here's why: %s: %s",
                self.table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def initialize_default_settings(self):
        """Initialize default settings when table is first created"""
        table = self.dynamodb.Table(self.table_name)
        default_settings = [
            GlobalSettingEntity('default_llm_model', '', '默认大语言模型'),
            GlobalSettingEntity('default_embedding_model', '', '默认嵌入模型'),
            GlobalSettingEntity('default_profile', '', '默认配置文件')
        ]
        
        for setting in default_settings:
            table.put_item(Item=setting.to_dict())
        
        logger.info("Default global settings initialized")

    def get_by_key(self, setting_key):
        response = self.table.get_item(Key={'setting_key': setting_key})
        if 'Item' in response:
            return GlobalSettingEntity(**response['Item'])
        return None

    def update(self, entity):
        self.table.put_item(Item=entity.to_dict())

    def get_all_settings(self):
        response = self.table.scan()
        return [GlobalSettingEntity(**item) for item in response['Items']]
