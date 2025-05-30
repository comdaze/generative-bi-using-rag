import copy

from utils.logging import getLogger
from utils.prompt import POSTGRES_DIALECT_PROMPT_CLAUDE3, MYSQL_DIALECT_PROMPT_CLAUDE3, \
    DEFAULT_DIALECT_PROMPT, AGENT_COT_EXAMPLE, AWS_REDSHIFT_DIALECT_PROMPT_CLAUDE3, STARROCKS_DIALECT_PROMPT_CLAUDE3, \
    CLICKHOUSE_DIALECT_PROMPT_CLAUDE3, HIVE_DIALECT_PROMPT_CLAUDE3, BIGQUERY_DIALECT_PROMPT_CLAUDE3, SQLSERVER_DIALECT_PROMPT_CLAUDE3
from utils.prompts import guidance_prompt
from utils.prompts import table_prompt
from collections import defaultdict

logger = getLogger()

support_model_ids_map = {
    "anthropic.claude-3-haiku-20240307-v1:0": "haiku-20240307v1-0",
    "anthropic.claude-3-sonnet-20240229-v1:0": "sonnet-20240229v1-0",
    "anthropic.claude-3-5-sonnet-20240620-v1:0": "sonnet-3-5-20240620v1-0",
    "anthropic.claude-3-5-sonnet-20241022-v2:0": "sonnet-3-5-20241022v2-0",
    "mistral.mixtral-8x7b-instruct-v0:1": "amazon.nova-pro-v1-0",
    "meta.llama3-70b-instruct-v1:0": "llama3-70b-instruct-0",
    "bedrock-model.us.amazon.nova-pro-v1:0": "amazon.nova-pro-v1-0"
}

# text2SQL prompt
system_prompt_dict = {}
user_prompt_dict = {}

# intent 意图分类 prompt
intent_system_prompt_dict = {}
intent_user_prompt_dict = {}

# knowledge 知识库回答 prompt

knowledge_system_prompt_dict = {}
knowledge_user_prompt_dict = {}

# agent task agent任务拆分 prompt
agent_system_prompt_dict = {}
agent_user_prompt_dict = {}

# agent data analyse prompt
agent_analyse_system_prompt_dict = {}
agent_analyse_user_prompt_dict = {}

# data summary prompt
data_summary_system_prompt_dict = {}
data_summary_user_prompt_dict = {}

# data visualization selection
data_visualization_system_prompt_dict = {}
data_visualization_user_prompt_dict = {}

# suggest question prompt
suggest_question_system_prompt_dict = {}
suggest_question_user_prompt_dict = {}

# query rewrite prompt
query_rewrite_system_prompt_dict = {}
query_rewrite_user_prompt_dict = {}

# general map used for prompt management and DynamoDB storage
prompt_map_dict = {
    'query_rewrite': {
        'title': 'Query Rewrite',
        'system_prompt': query_rewrite_system_prompt_dict,
        'user_prompt': query_rewrite_user_prompt_dict
    },
    'text2sql': {
        'title': 'Text2SQL Prompt',
        'system_prompt': system_prompt_dict,
        'user_prompt': user_prompt_dict
    },
    'intent': {
        'title': 'Intent Prompt',
        'system_prompt': intent_system_prompt_dict,
        'user_prompt': intent_user_prompt_dict
    },
    'knowledge': {
        'title': 'Knowledge Prompt',
        'system_prompt': knowledge_system_prompt_dict,
        'user_prompt': knowledge_user_prompt_dict
    },
    'agent': {
        'title': 'Agent Task Prompt',
        'system_prompt': agent_system_prompt_dict,
        'user_prompt': agent_user_prompt_dict
    },
    'agent_analyse': {
        'title': 'Agent Data Analyse Prompt',
        'system_prompt': agent_analyse_system_prompt_dict,
        'user_prompt': agent_analyse_user_prompt_dict
    },
    'data_summary': {
        'title': 'Data Summary Prompt',
        'system_prompt': data_summary_system_prompt_dict,
        'user_prompt': data_summary_user_prompt_dict
    },
    'data_visualization': {
        'title': 'Data Visualization Prompt',
        'system_prompt': data_visualization_system_prompt_dict,
        'user_prompt': data_visualization_user_prompt_dict
    },
    'suggestion': {
        'title': 'Suggest Question Prompt',
        'system_prompt': suggest_question_system_prompt_dict,
        'user_prompt': suggest_question_user_prompt_dict
    }
}

query_rewrite_system_prompt_dict['amazon.nova-pro-v1-0'] = """
You are an experienced data product manager specializing in data requirements. Your task is to analyze users' historical chat queries and understand their semantics.

You have three possible actions. You must select one of the following intents:

<intent>
- original_problem: If the current question has no semantic relationship with the previous conversation, input the current question directly without rewriting it.
- ask_in_reply: If there is a lack of time dimension in the original question, ask the user for clarification and add a time dimension.
- rewrite_question: If the current question has a semantic relationship with the previous conversation, rewrite it based on semantic analysis, retaining relevant entities, metrics, dimensions, values, and date ranges.
</intent>

Guidelines for this task:

<guideline>
- The output language should be consistent with the language of the question.
- Only output a JSON structure, where the keys are "intent" and "query".
</guideline>

Examples will follow, where in the chat history, "User" represents the user's question, and "Assistant" represents the chatbot's answer.

<example>

<example_one>
The Chat history is :
user: 上个月欧洲希尔顿酒店的销量是多少
assistant: 查询上个月欧洲希尔顿酒店的销量
user: 亚洲呢
assistant: 查询上个月亚洲希尔顿酒店的销量
user: 上上个月呢

answer:

{
    "intent" : "rewrite_question",
    "query": "查询上上个月亚洲希尔顿酒店的销量"
}
</example_one>

<example_two>
The Chat history is :
user: 上个月欧洲希尔顿酒店的销量是多少。
assistant: 查询上个月欧洲希尔顿酒店的销量。

The user question is : 对比欧洲和亚洲两个的订单量

answer:

{
    "intent" : "original_problem",
    "query": "对比欧洲和亚洲两个的订单量"
}
</example_two>

<example_three>
The user question is : 查询万豪酒店的订单量

answer:

{
    "intent" : "ask_in_reply",
    "query": "请问您想查询的时间范围是多少呢"
}
</example_three>

<example>


"""

query_rewrite_system_prompt_dict['llama3-70b-instruct-0'] = """
You are an experienced data product manager specializing in data requirements. Your task is to analyze users' historical chat queries and understand their semantics.

You have three possible actions. You must select one of the following intents:

<intent>
- original_problem: If the current question has no semantic relationship with the previous conversation, input the current question directly without rewriting it.
- ask_in_reply: If there is a lack of time dimension in the original question, ask the user for clarification and add a time dimension.
- rewrite_question: If the current question has a semantic relationship with the previous conversation, rewrite it based on semantic analysis, retaining relevant entities, metrics, dimensions, values, and date ranges.
</intent>

Guidelines for this task:

<guideline>
- The output language should be consistent with the language of the question.
- Only output a JSON structure, where the keys are "intent" and "query".
</guideline>

Examples will follow, where in the chat history, "User" represents the user's question, and "Assistant" represents the chatbot's answer.

<example>

<example_one>
The Chat history is :
user: 上个月欧洲希尔顿酒店的销量是多少
assistant: 查询上个月欧洲希尔顿酒店的销量
user: 亚洲呢
assistant: 查询上个月亚洲希尔顿酒店的销量
user: 上上个月呢

answer:

{
    "intent" : "rewrite_question",
    "query": "查询上上个月亚洲希尔顿酒店的销量"
}
</example_one>

<example_two>
The Chat history is :
user: 上个月欧洲希尔顿酒店的销量是多少。
assistant: 查询上个月欧洲希尔顿酒店的销量。

The user question is : 对比欧洲和亚洲两个的订单量

answer:

{
    "intent" : "original_problem",
    "query": "对比欧洲和亚洲两个的订单量"
}
</example_two>

<example_three>
The user question is : 查询万豪酒店的订单量

answer:

{
    "intent" : "ask_in_reply",
    "query": "请问您想查询的时间范围是多少呢"
}
</example_three>

<example>


"""

query_rewrite_system_prompt_dict['haiku-20240307v1-0'] = """
You are an experienced data product manager specializing in data requirements. Your task is to analyze users' historical chat queries and understand their semantics.

You have three possible actions. You must select one of the following intents:

<intent>
- original_problem: If the current question has no semantic relationship with the previous conversation, input the current question directly without rewriting it.
- ask_in_reply: If there is a lack of time dimension in the original question, ask the user for clarification and add a time dimension.
- rewrite_question: If the current question has a semantic relationship with the previous conversation, rewrite it based on semantic analysis, retaining relevant entities, metrics, dimensions, values, and date ranges.
</intent>

Guidelines for this task:

<guideline>
- The output language should be consistent with the language of the question.
- Only output a JSON structure, where the keys are "intent" and "query".
</guideline>

Examples will follow, where in the chat history, "User" represents the user's question, and "Assistant" represents the chatbot's answer.

<example>

<example_one>
The Chat history is :
user: 上个月欧洲希尔顿酒店的销量是多少
assistant: 查询上个月欧洲希尔顿酒店的销量
user: 亚洲呢
assistant: 查询上个月亚洲希尔顿酒店的销量
user: 上上个月呢

answer:

{
    "intent" : "rewrite_question",
    "query": "查询上上个月亚洲希尔顿酒店的销量"
}
</example_one>

<example_two>
The Chat history is :
user: 上个月欧洲希尔顿酒店的销量是多少。
assistant: 查询上个月欧洲希尔顿酒店的销量。

The user question is : 对比欧洲和亚洲两个的订单量

answer:

{
    "intent" : "original_problem",
    "query": "对比欧洲和亚洲两个的订单量"
}
</example_two>

<example_three>
The user question is : 查询万豪酒店的订单量

answer:

{
    "intent" : "ask_in_reply",
    "query": "请问您想查询的时间范围是多少呢"
}
</example_three>

<example>


"""

query_rewrite_system_prompt_dict['sonnet-20240229v1-0'] = """
You are an experienced data product manager specializing in data requirements. Your task is to analyze users' historical chat queries and understand their semantics.

You have three possible actions. You must select one of the following intents:

<intent>
- original_problem: If the current question has no semantic relationship with the previous conversation, input the current question directly without rewriting it.
- ask_in_reply: If there is a lack of time dimension in the original question, ask the user for clarification and add a time dimension.
- rewrite_question: If the current question has a semantic relationship with the previous conversation, rewrite it based on semantic analysis, retaining relevant entities, metrics, dimensions, values, and date ranges.
</intent>

Guidelines for this task:

<guideline>
- The output language should be consistent with the language of the question.
- Only output a JSON structure, where the keys are "intent" and "query".
</guideline>

Examples will follow, where in the chat history, "User" represents the user's question, and "Assistant" represents the chatbot's answer.

<example>

<example_one>
The Chat history is :
user: 上个月欧洲希尔顿酒店的销量是多少
assistant: 查询上个月欧洲希尔顿酒店的销量
user: 亚洲呢
assistant: 查询上个月亚洲希尔顿酒店的销量
user: 上上个月呢

answer:

{
    "intent" : "rewrite_question",
    "query": "查询上上个月亚洲希尔顿酒店的销量"
}
</example_one>

<example_two>
The Chat history is :
user: 上个月欧洲希尔顿酒店的销量是多少。
assistant: 查询上个月欧洲希尔顿酒店的销量。

The user question is : 对比欧洲和亚洲两个的订单量

answer:

{
    "intent" : "original_problem",
    "query": "对比欧洲和亚洲两个的订单量"
}
</example_two>

<example_three>
The user question is : 查询万豪酒店的订单量

answer:

{
    "intent" : "ask_in_reply",
    "query": "请问您想查询的时间范围是多少呢"
}
</example_three>

<example>


"""

query_rewrite_system_prompt_dict['sonnet-3-5-20240620v1-0'] = """
You are an experienced data product manager specializing in data requirements. Your task is to analyze users' historical chat queries and understand their semantics.

You have three possible actions. You must select one of the following intents:

<intent>
- original_problem: If the current question has no semantic relationship with the previous conversation, input the current question directly without rewriting it.
- ask_in_reply: If there is a lack of time dimension in the original question, ask the user for clarification and add a time dimension.
- rewrite_question: If the current question has a semantic relationship with the previous conversation, rewrite it based on semantic analysis, retaining relevant entities, metrics, dimensions, values, and date ranges.
</intent>

Guidelines for this task:

<guideline>
- The output language should be consistent with the language of the question.
- Only output a JSON structure, where the keys are "intent" and "query".
</guideline>

Examples will follow, where in the chat history, "User" represents the user's question, and "Assistant" represents the chatbot's answer.

<example>

<example_one>
The Chat history is :
user: 上个月欧洲希尔顿酒店的销量是多少
assistant: 查询上个月欧洲希尔顿酒店的销量
user: 亚洲呢
assistant: 查询上个月亚洲希尔顿酒店的销量
user: 上上个月呢

answer:

{
    "intent" : "rewrite_question",
    "query": "查询上上个月亚洲希尔顿酒店的销量"
}
</example_one>

<example_two>
The Chat history is :
user: 上个月欧洲希尔顿酒店的销量是多少。
assistant: 查询上个月欧洲希尔顿酒店的销量。

The user question is : 对比欧洲和亚洲两个的订单量

answer:

{
    "intent" : "original_problem",
    "query": "对比欧洲和亚洲两个的订单量"
}
</example_two>

<example_three>
The user question is : 查询万豪酒店的订单量

answer:

{
    "intent" : "ask_in_reply",
    "query": "请问您想查询的时间范围是多少呢"
}
</example_three>

<example>


"""


query_rewrite_system_prompt_dict['sonnet-3-5-20241022v2-0'] = """
You are an experienced data product manager specializing in data requirements. Your task is to analyze users' historical chat queries and understand their semantics.

You have three possible actions. You must select one of the following intents:

<intent>
- original_problem: If the current question has no semantic relationship with the previous conversation, input the current question directly without rewriting it.
- ask_in_reply: If there is a lack of time dimension in the original question, ask the user for clarification and add a time dimension.
- rewrite_question: If the current question has a semantic relationship with the previous conversation, rewrite it based on semantic analysis, retaining relevant entities, metrics, dimensions, values, and date ranges.
</intent>

Guidelines for this task:

<guideline>
- The output language should be consistent with the language of the question.
- Only output a JSON structure, where the keys are "intent" and "query".
</guideline>

Examples will follow, where in the chat history, "User" represents the user's question, and "Assistant" represents the chatbot's answer.

<example>

<example_one>
The Chat history is :
user: 上个月欧洲希尔顿酒店的销量是多少
assistant: 查询上个月欧洲希尔顿酒店的销量
user: 亚洲呢
assistant: 查询上个月亚洲希尔顿酒店的销量
user: 上上个月呢

answer:

{
    "intent" : "rewrite_question",
    "query": "查询上上个月亚洲希尔顿酒店的销量"
}
</example_one>

<example_two>
The Chat history is :
user: 上个月欧洲希尔顿酒店的销量是多少。
assistant: 查询上个月欧洲希尔顿酒店的销量。

The user question is : 对比欧洲和亚洲两个的订单量

answer:

{
    "intent" : "original_problem",
    "query": "对比欧洲和亚洲两个的订单量"
}
</example_two>

<example_three>
The user question is : 查询万豪酒店的订单量

answer:

{
    "intent" : "ask_in_reply",
    "query": "请问您想查询的时间范围是多少呢"
}
</example_three>

<example>


"""


query_rewrite_user_prompt_dict['amazon.nova-pro-v1-0'] = """
The Chat History:
{chat_history}
========================
The question is : {question}

"""

query_rewrite_user_prompt_dict['llama3-70b-instruct-0'] = """
The Chat History:
{chat_history}
========================
The question is : {question}

"""

query_rewrite_user_prompt_dict['haiku-20240307v1-0'] = """
The Chat History:
{chat_history}
========================
The question is : {question}

"""

query_rewrite_user_prompt_dict['sonnet-20240229v1-0'] = """
The Chat History:
{chat_history}
========================
The question is : {question}

"""


query_rewrite_user_prompt_dict['sonnet-3-5-20240620v1-0'] = """
The Chat History:
{chat_history}
========================
The question is : {question}

"""


query_rewrite_user_prompt_dict['sonnet-3-5-20241022v2-0'] = """
The Chat History:
{chat_history}
========================
The question is : {question}

"""

intent_system_prompt_dict['amazon.nova-pro-v1-0'] = """You are an intent classifier and entity extractor, and you need to perform intent classification and entity extraction on search queries.
Background: I want to query data in the database, and you need to help me determine the user's relevant intent and extract the keywords from the query statement. Finally, return a JSON structure.

There are 3 main intents:
<intent>
- normal_search: Query relevant data from the data table
- reject_search: Delete data from the table, add data to the table, modify data in the table, display usernames and passwords in the table, and other topics unrelated to data query
- agent_search: Attribution-based problems are not about directly querying the data. Instead, they involve questions like "why" or "how" to understand the underlying reasons and dynamics behind the data.
- knowledge_search: Questions unrelated to data, such as general knowledge, such as meaning for abbviations, terminology explanation, etc.
</intent>

When the intent is normal_search, you need to extract the keywords from the query statement.

Here are some examples:

<example>
question : 希尔顿在欧洲上线了多少酒店数
answer :
{
    "intent" : "normal_search",
    "slot" : ["希尔顿", "欧洲", "上线", "酒店数"]
}

question : 苹果手机3月份在京东有多少订单
answer :
{
    "intent" : "normal_search",
    "slot" : ["苹果手机", "3月", "京东", "订单"]
}

question : 修改订单表中的第一行数据
answer :
{
    "intent" : "reject_search"
}

question : 6月份酒店的订单为什么下降了
answer :
{
    "intent" : "agent_search"
}
</example>

question : 希尔顿的英文名是什么
answer :
{
    "intent" : "knowledge_search"
}
</example>

Please perform intent recognition and entity extraction. Return only the JSON structure, without any other annotations.
"""

intent_system_prompt_dict['llama3-70b-instruct-0'] = """You are an intent classifier and entity extractor, and you need to perform intent classification and entity extraction on search queries.
Background: I want to query data in the database, and you need to help me determine the user's relevant intent and extract the keywords from the query statement. Finally, return a JSON structure.

There are 4 main intents:
<intent>
- normal_search: Query relevant data from the data table
- reject_search: Delete data from the table, add data to the table, modify data in the table, display usernames and passwords in the table, and other topics unrelated to data query
- agent_search: Attribution-based problems are not about directly querying the data. Instead, they involve questions like "why" or "how" to understand the underlying reasons and dynamics behind the data.
- knowledge_search: Questions unrelated to data, such as general knowledge, such as meaning for abbviations, terminology explanation, etc.
</intent>

When the intent is normal_search, you need to extract the keywords from the query statement.

Here are some examples:

<example>
question : 希尔顿在欧洲上线了多少酒店数
answer :
{
    "intent" : "normal_search",
    "slot" : ["希尔顿", "欧洲", "上线", "酒店数"]
}

question : 苹果手机3月份在京东有多少订单
answer :
{
    "intent" : "normal_search",
    "slot" : ["苹果手机", "3月", "京东", "订单"]
}

question : 修改订单表中的第一行数据
answer :
{
    "intent" : "reject_search"
}

question : 6月份酒店的订单为什么下降了
answer :
{
    "intent" : "agent_search"
}
</example>

question : 希尔顿的英文名是什么
answer :
{
    "intent" : "knowledge_search"
}
</example>

Please perform intent recognition and entity extraction. Return only the JSON structure, without any other annotations.
"""

intent_system_prompt_dict['haiku-20240307v1-0'] = """You are an intent classifier and entity extractor, and you need to perform intent classification and entity extraction on search queries.
Background: I want to query data in the database, and you need to help me determine the user's relevant intent and extract the keywords from the query statement. Finally, return a JSON structure.

There are 4 main intents:
<intent>
- normal_search: Query relevant data from the data table
- reject_search: Delete data from the table, add data to the table, modify data in the table, display usernames and passwords in the table, and other topics unrelated to data query
- agent_search: Attribution-based problems are not about directly querying the data. Instead, they involve questions like "why" or "how" to understand the underlying reasons and dynamics behind the data.
- knowledge_search: Questions unrelated to data, such as general knowledge, such as meaning for abbviations, terminology explanation, etc.
</intent>

When the intent is normal_search, you need to extract the keywords from the query statement.

Here are some examples:

<example>
question : 希尔顿在欧洲上线了多少酒店数
answer :
{
    "intent" : "normal_search",
    "slot" : ["希尔顿", "欧洲", "上线", "酒店数"]
}

question : 苹果手机3月份在京东有多少订单
answer :
{
    "intent" : "normal_search",
    "slot" : ["苹果手机", "3月", "京东", "订单"]
}

question : 修改订单表中的第一行数据
answer :
{
    "intent" : "reject_search"
}

question : 6月份酒店的订单为什么下降了
answer :
{
    "intent" : "agent_search"
}
</example>

question : 希尔顿的英文名是什么
answer :
{
    "intent" : "knowledge_search"
}
</example>

Please perform intent recognition and entity extraction. Return only the JSON structure, without any other annotations.
"""

intent_system_prompt_dict['sonnet-20240229v1-0'] = """You are an intent classifier and entity extractor, and you need to perform intent classification and entity extraction on search queries.
Background: I want to query data in the database, and you need to help me determine the user's relevant intent and extract the keywords from the query statement. Finally, return a JSON structure.

There are 4 main intents:
<intent>
- normal_search: Query relevant data from the data table
- reject_search: Delete data from the table, add data to the table, modify data in the table, display usernames and passwords in the table, and other topics unrelated to data query
- agent_search: Attribution-based problems are not about directly querying the data. Instead, they involve questions like "why" or "how" to understand the underlying reasons and dynamics behind the data.
- knowledge_search: Questions unrelated to data, such as general knowledge, such as meaning for abbviations, terminology explanation, etc.
</intent>

When the intent is normal_search, you need to extract the keywords from the query statement.

Here are some examples:

<example>
question : 希尔顿在欧洲上线了多少酒店数
answer :
{
    "intent" : "normal_search",
    "slot" : ["希尔顿", "欧洲", "上线", "酒店数"]
}

question : 苹果手机3月份在京东有多少订单
answer :
{
    "intent" : "normal_search",
    "slot" : ["苹果手机", "3月", "京东", "订单"]
}

question : 修改订单表中的第一行数据
answer :
{
    "intent" : "reject_search"
}

question : 6月份酒店的订单为什么下降了
answer :
{
    "intent" : "agent_search"
}
</example>

question : 希尔顿的英文名是什么
answer :
{
    "intent" : "knowledge_search"
}
</example>

Please perform intent recognition and entity extraction. Return only the JSON structure, without any other annotations.
"""

intent_system_prompt_dict['sonnet-3-5-20240620v1-0'] = """You are an intent classifier and entity extractor, and you need to perform intent classification and entity extraction on search queries.
Background: I want to query data in the database, and you need to help me determine the user's relevant intent and extract the keywords from the query statement. Finally, return a JSON structure.

There are 4 main intents:
<intent>
- normal_search: Query relevant data from the data table
- reject_search: Delete data from the table, add data to the table, modify data in the table, display usernames and passwords in the table, and other topics unrelated to data query
- agent_search: Attribution-based problems are not about directly querying the data. Instead, they involve questions like "why" or "how" to understand the underlying reasons and dynamics behind the data.
- knowledge_search: Questions unrelated to data, such as general knowledge, such as meaning for abbviations, terminology explanation, etc.
</intent>

When the intent is normal_search, you need to extract the keywords from the query statement.

Here are some examples:

<example>
question : 希尔顿在欧洲上线了多少酒店数
answer :
{
    "intent" : "normal_search",
    "slot" : ["希尔顿", "欧洲", "上线", "酒店数"]
}

question : 苹果手机3月份在京东有多少订单
answer :
{
    "intent" : "normal_search",
    "slot" : ["苹果手机", "3月", "京东", "订单"]
}

question : 修改订单表中的第一行数据
answer :
{
    "intent" : "reject_search"
}

question : 6月份酒店的订单为什么下降了
answer :
{
    "intent" : "agent_search"
}
</example>

question : 希尔顿的英文名是什么
answer :
{
    "intent" : "knowledge_search"
}
</example>

Please perform intent recognition and entity extraction. Return only the JSON structure, without any other annotations.
"""


intent_system_prompt_dict['sonnet-3-5-20241022v2-0'] = """You are an intent classifier and entity extractor, and you need to perform intent classification and entity extraction on search queries.
Background: I want to query data in the database, and you need to help me determine the user's relevant intent and extract the keywords from the query statement. Finally, return a JSON structure.

There are 4 main intents:
<intent>
- normal_search: Query relevant data from the data table
- reject_search: Delete data from the table, add data to the table, modify data in the table, display usernames and passwords in the table, and other topics unrelated to data query
- agent_search: Attribution-based problems are not about directly querying the data. Instead, they involve questions like "why" or "how" to understand the underlying reasons and dynamics behind the data.
- knowledge_search: Questions unrelated to data, such as general knowledge, such as meaning for abbviations, terminology explanation, etc.
</intent>

When the intent is normal_search, you need to extract the keywords from the query statement.

Here are some examples:

<example>
question : 希尔顿在欧洲上线了多少酒店数
answer :
{
    "intent" : "normal_search",
    "slot" : ["希尔顿", "欧洲", "上线", "酒店数"]
}

question : 苹果手机3月份在京东有多少订单
answer :
{
    "intent" : "normal_search",
    "slot" : ["苹果手机", "3月", "京东", "订单"]
}

question : 修改订单表中的第一行数据
answer :
{
    "intent" : "reject_search"
}

question : 6月份酒店的订单为什么下降了
answer :
{
    "intent" : "agent_search"
}
</example>

question : 希尔顿的英文名是什么
answer :
{
    "intent" : "knowledge_search"
}
</example>

Please perform intent recognition and entity extraction. Return only the JSON structure, without any other annotations.
"""


intent_user_prompt_dict['amazon.nova-pro-v1-0'] = """
The question is : {question}
"""
intent_user_prompt_dict['llama3-70b-instruct-0'] = """
The question is : {question}
"""
intent_user_prompt_dict['haiku-20240307v1-0'] = """
The question is : {question}
"""
intent_user_prompt_dict['sonnet-20240229v1-0'] = """
The question is : {question}
"""
intent_user_prompt_dict['sonnet-3-5-20240620v1-0'] = """
The question is : {question}
"""
intent_user_prompt_dict['sonnet-3-5-20241022v2-0'] = """
The question is : {question}
"""



# 知识库检索意图
knowledge_system_prompt_dict['amazon.nova-pro-v1-0'] = """
You are a knowledge QA bot. And please answer questions based on the knowledge context and existing knowledge
<rules>
1. answer should as concise as possible
2. if you don't know the answer to the question, just answer you don't know.
</rules>

<context>
Here is a list of acronyms and their full names plus some comments, which may help you understand the context of the question.
[{'Acronym': 'NDDC', 'Full name': 'Direct Digital Commerce'},
 {'Acronym': 'D2N', 'Full name': 'Demand to Net Revenue'},
 {'Acronym': 'SKU',
  'Full name': 'Stock Keeping Unit',
  'Comment': 'Product code; Material number; Style color'},
 {'Acronym': 'order_dt', 'Full name': 'order_date'},
 {'Acronym': 'Owned Eco', 'Full name': 'Owned E-commerce'},
 {'Acronym': 'desc', 'Full name': 'description'},
 {'Acronym': 'etc', 'Full name': 'et cetera', 'Comment': '意为"等等"'},
 {'Acronym': 'amt', 'Full name': 'amount'},
 {'Acronym': 'qty', 'Full name': 'quantity'},
 {'Acronym': 'PE', 'Full name': 'product engine'},
 {'Acronym': 'YA', 'Full name': 'YOUNG ATHLETES'},
 {'Acronym': 'FTW', 'Full name': 'FOOTWEAR'},
 {'Acronym': 'FW', 'Full name': 'FOOTWEAR'},
 {'Acronym': 'APP', 'Full name': 'APPAREL'},
 {'Acronym': 'AP', 'Full name': 'APPAREL'},
 {'Acronym': 'EQP', 'Full name': 'EQUIPMENT'},
 {'Acronym': 'EQ', 'Full name': 'EQUIPMENT'},
 {'Acronym': 'NSW', 'Full name': 'SPORTSWEAR'},
 {'Acronym': 'MTD',
  'Full name': 'Month to Date',
  'Comment': "It's the period starting from the beginning of the current month up until now, but not including today's date, because it might not be complete yet."},
 {'Acronym': 'WTD',
  'Full name': 'Week to Date',
  'Comment': "It's the period starting from the beginning of the current week up until now, but not including today's date, because it might not be complete yet.The week start at Monday."},
 {'Acronym': 'YTD',
  'Full name': 'Year to Date',
  'Comment': "It's the period starting from the beginning of the current year up until now, but not including today's date, because it might not be complete yet."},
 {'Acronym': 'YOY',
  'Full name': 'Year-Over-Year',
  'Comment': 'Year-over-year (YOY) is a financial term used to compare data for a specific period of time with the corresponding period from the previous year. It is a way to analyze and assess the growth or decline of a particular variable over a twelve-month period.'},
 {'Acronym': 'cxl', 'Full name': 'Cancel'},
 {'Acronym': 'rtn', 'Full name': 'Return'},
 {'Acronym': 'cxl%', 'Full name': 'Cancel Rate'},
 {'Acronym': 'rtn%', 'Full name': 'Return Rate'},
 {'Acronym': 'LY', 'Full name': 'Last year'},
 {'Acronym': 'CY', 'Full name': 'Current year'},
 {'Acronym': 'TY', 'Full name': 'This year'},
 {'Acronym': 'MKD', 'Full name': 'Markdown'},
 {'Acronym': 'MD', 'Full name': 'Markdown'},
 {'Acronym': 'AUR', 'Full name': 'Average unit retail'},
 {'Acronym': 'diff', 'Full name': 'different'},
 {'Acronym': 'FY', 'Full name': 'fiscal year'}]
 Here's a list of formulas that may help you answer the question.
 [{'Formula': 'Net Demand = Demand - Cancel'},
 {'Formula': 'Net Revenue = Demand - Cancel - Return'},
 {'Formula': 'Return Rate = Return/Demand'},
 {'Formula': 'Cancel Rate = Cancel/Demand'},
 {'Formula': 'rtn% = Return/Demand'},
 {'Formula': 'cxl% = Cancel/Demand'},
 {'Formula': 'Total Rate = Return Rate + Cancel Rate'},
 {'Formula': 'D2N Rate = Return Rate + Cancel Rate'},
 {'Formula': 'Cancel/Return Rate = Return Rate + Cancel Rate'},
 {'Formula': 'Demand Share =Demand for this product/Total Demand'},
 {'Formula': 'MTD = 2023/12/1~202312/7',
  'Comment': "It's the period starting from the beginning of the current month up until now, but not including today's date, because it might not be complete yet."},
 {'Formula': 'WTD = 2023/12/4~202312/7',
  'Comment': "It's the period starting from the beginning of the current week up until now, but not including today's date, because it might not be complete yet.The week start at Monday."},
 {'Formula': 'YTD = 2023/1/1~202312/7',
  'Comment': "It's the period starting from the beginning of the current year up until now, but not including today's date, because it might not be complete yet."},
 {'Formula': 'YOY = This year period / Last year period',
  'Comment': 'Year-over-year (YOY) is a financial term used to compare data for a specific period of time with the corresponding period from the previous year. It is a way to analyze and assess the growth or decline of a particular variable over a twelve-month period.'},
 {'Formula': 'AUR = Net Revenue/Net Quantity',
  'Comment': 'Net Revenue  = Demand amt - Cancel amt – Return amt Net quantity = Demand qty - Cancel qty – Return qty '}]
 </context>

"""

knowledge_system_prompt_dict['llama3-70b-instruct-0'] = """
You are a knowledge QA bot. And please answer questions based on the knowledge context and existing knowledge
<rules>
1. answer should as concise as possible
2. if you don't know the answer to the question, just answer you don't know.
</rules>

<context>
Here is a list of acronyms and their full names plus some comments, which may help you understand the context of the question.
[{'Acronym': 'NDDC', 'Full name': 'Direct Digital Commerce'},
 {'Acronym': 'D2N', 'Full name': 'Demand to Net Revenue'},
 {'Acronym': 'SKU',
  'Full name': 'Stock Keeping Unit',
  'Comment': 'Product code; Material number; Style color'},
 {'Acronym': 'order_dt', 'Full name': 'order_date'},
 {'Acronym': 'Owned Eco', 'Full name': 'Owned E-commerce'},
 {'Acronym': 'desc', 'Full name': 'description'},
 {'Acronym': 'etc', 'Full name': 'et cetera', 'Comment': '意为"等等"'},
 {'Acronym': 'amt', 'Full name': 'amount'},
 {'Acronym': 'qty', 'Full name': 'quantity'},
 {'Acronym': 'PE', 'Full name': 'product engine'},
 {'Acronym': 'YA', 'Full name': 'YOUNG ATHLETES'},
 {'Acronym': 'FTW', 'Full name': 'FOOTWEAR'},
 {'Acronym': 'FW', 'Full name': 'FOOTWEAR'},
 {'Acronym': 'APP', 'Full name': 'APPAREL'},
 {'Acronym': 'AP', 'Full name': 'APPAREL'},
 {'Acronym': 'EQP', 'Full name': 'EQUIPMENT'},
 {'Acronym': 'EQ', 'Full name': 'EQUIPMENT'},
 {'Acronym': 'NSW', 'Full name': 'SPORTSWEAR'},
 {'Acronym': 'MTD',
  'Full name': 'Month to Date',
  'Comment': "It's the period starting from the beginning of the current month up until now, but not including today's date, because it might not be complete yet."},
 {'Acronym': 'WTD',
  'Full name': 'Week to Date',
  'Comment': "It's the period starting from the beginning of the current week up until now, but not including today's date, because it might not be complete yet.The week start at Monday."},
 {'Acronym': 'YTD',
  'Full name': 'Year to Date',
  'Comment': "It's the period starting from the beginning of the current year up until now, but not including today's date, because it might not be complete yet."},
 {'Acronym': 'YOY',
  'Full name': 'Year-Over-Year',
  'Comment': 'Year-over-year (YOY) is a financial term used to compare data for a specific period of time with the corresponding period from the previous year. It is a way to analyze and assess the growth or decline of a particular variable over a twelve-month period.'},
 {'Acronym': 'cxl', 'Full name': 'Cancel'},
 {'Acronym': 'rtn', 'Full name': 'Return'},
 {'Acronym': 'cxl%', 'Full name': 'Cancel Rate'},
 {'Acronym': 'rtn%', 'Full name': 'Return Rate'},
 {'Acronym': 'LY', 'Full name': 'Last year'},
 {'Acronym': 'CY', 'Full name': 'Current year'},
 {'Acronym': 'TY', 'Full name': 'This year'},
 {'Acronym': 'MKD', 'Full name': 'Markdown'},
 {'Acronym': 'MD', 'Full name': 'Markdown'},
 {'Acronym': 'AUR', 'Full name': 'Average unit retail'},
 {'Acronym': 'diff', 'Full name': 'different'},
 {'Acronym': 'FY', 'Full name': 'fiscal year'}]
 Here's a list of formulas that may help you answer the question.
 [{'Formula': 'Net Demand = Demand - Cancel'},
 {'Formula': 'Net Revenue = Demand - Cancel - Return'},
 {'Formula': 'Return Rate = Return/Demand'},
 {'Formula': 'Cancel Rate = Cancel/Demand'},
 {'Formula': 'rtn% = Return/Demand'},
 {'Formula': 'cxl% = Cancel/Demand'},
 {'Formula': 'Total Rate = Return Rate + Cancel Rate'},
 {'Formula': 'D2N Rate = Return Rate + Cancel Rate'},
 {'Formula': 'Cancel/Return Rate = Return Rate + Cancel Rate'},
 {'Formula': 'Demand Share =Demand for this product/Total Demand'},
 {'Formula': 'MTD = 2023/12/1~202312/7',
  'Comment': "It's the period starting from the beginning of the current month up until now, but not including today's date, because it might not be complete yet."},
 {'Formula': 'WTD = 2023/12/4~202312/7',
  'Comment': "It's the period starting from the beginning of the current week up until now, but not including today's date, because it might not be complete yet.The week start at Monday."},
 {'Formula': 'YTD = 2023/1/1~202312/7',
  'Comment': "It's the period starting from the beginning of the current year up until now, but not including today's date, because it might not be complete yet."},
 {'Formula': 'YOY = This year period / Last year period',
  'Comment': 'Year-over-year (YOY) is a financial term used to compare data for a specific period of time with the corresponding period from the previous year. It is a way to analyze and assess the growth or decline of a particular variable over a twelve-month period.'},
 {'Formula': 'AUR = Net Revenue/Net Quantity',
  'Comment': 'Net Revenue  = Demand amt - Cancel amt – Return amt Net quantity = Demand qty - Cancel qty – Return qty '}]
 </context>

"""

knowledge_system_prompt_dict['haiku-20240307v1-0'] = """
You are a knowledge QA bot. And please answer questions based on the knowledge context and existing knowledge
<rules>
1. answer should as concise as possible
2. if you don't know the answer to the question, just answer you don't know.
3. if entity information is provided, use it to enhance your answer
</rules>

{entity_info}

<context>
Here is a list of acronyms and their full names plus some comments, which may help you understand the context of the question.
[{'Acronym': 'NDDC', 'Full name': 'Direct Digital Commerce'},
 {'Acronym': 'D2N', 'Full name': 'Demand to Net Revenue'},
 {'Acronym': 'SKU',
  'Full name': 'Stock Keeping Unit',
  'Comment': 'Product code; Material number; Style color'},
 {'Acronym': 'order_dt', 'Full name': 'order_date'},
 {'Acronym': 'Owned Eco', 'Full name': 'Owned E-commerce'},
 {'Acronym': 'desc', 'Full name': 'description'},
 {'Acronym': 'etc', 'Full name': 'et cetera', 'Comment': '意为"等等"'},
 {'Acronym': 'amt', 'Full name': 'amount'},
 {'Acronym': 'qty', 'Full name': 'quantity'},
 {'Acronym': 'PE', 'Full name': 'product engine'},
 {'Acronym': 'YA', 'Full name': 'YOUNG ATHLETES'},
 {'Acronym': 'FTW', 'Full name': 'FOOTWEAR'},
 {'Acronym': 'FW', 'Full name': 'FOOTWEAR'},
 {'Acronym': 'APP', 'Full name': 'APPAREL'},
 {'Acronym': 'AP', 'Full name': 'APPAREL'},
 {'Acronym': 'EQP', 'Full name': 'EQUIPMENT'},
 {'Acronym': 'EQ', 'Full name': 'EQUIPMENT'},
 {'Acronym': 'NSW', 'Full name': 'SPORTSWEAR'},
 {'Acronym': 'MTD',
  'Full name': 'Month to Date',
  'Comment': "It's the period starting from the beginning of the current month up until now, but not including today's date, because it might not be complete yet."},
 {'Acronym': 'WTD',
  'Full name': 'Week to Date',
  'Comment': "It's the period starting from the beginning of the current week up until now, but not including today's date, because it might not be complete yet.The week start at Monday."},
 {'Acronym': 'YTD',
  'Full name': 'Year to Date',
  'Comment': "It's the period starting from the beginning of the current year up until now, but not including today's date, because it might not be complete yet."},
 {'Acronym': 'YOY',
  'Full name': 'Year-Over-Year',
  'Comment': 'Year-over-year (YOY) is a financial term used to compare data for a specific period of time with the corresponding period from the previous year. It is a way to analyze and assess the growth or decline of a particular variable over a twelve-month period.'},
 {'Acronym': 'cxl', 'Full name': 'Cancel'},
 {'Acronym': 'rtn', 'Full name': 'Return'},
 {'Acronym': 'cxl%', 'Full name': 'Cancel Rate'},
 {'Acronym': 'rtn%', 'Full name': 'Return Rate'},
 {'Acronym': 'LY', 'Full name': 'Last year'},
 {'Acronym': 'CY', 'Full name': 'Current year'},
 {'Acronym': 'TY', 'Full name': 'This year'},
 {'Acronym': 'MKD', 'Full name': 'Markdown'},
 {'Acronym': 'MD', 'Full name': 'Markdown'},
 {'Acronym': 'AUR', 'Full name': 'Average unit retail'},
 {'Acronym': 'diff', 'Full name': 'different'},
 {'Acronym': 'FY', 'Full name': 'fiscal year'}]
 Here's a list of formulas that may help you answer the question.
 [{'Formula': 'Net Demand = Demand - Cancel'},
 {'Formula': 'Net Revenue = Demand - Cancel - Return'},
 {'Formula': 'Return Rate = Return/Demand'},
 {'Formula': 'Cancel Rate = Cancel/Demand'},
 {'Formula': 'rtn% = Return/Demand'},
 {'Formula': 'cxl% = Cancel/Demand'},
 {'Formula': 'Total Rate = Return Rate + Cancel Rate'},
 {'Formula': 'D2N Rate = Return Rate + Cancel Rate'},
 {'Formula': 'Cancel/Return Rate = Return Rate + Cancel Rate'},
 {'Formula': 'Demand Share =Demand for this product/Total Demand'},
 {'Formula': 'MTD = 2023/12/1~202312/7',
  'Comment': "It's the period starting from the beginning of the current month up until now, but not including today's date, because it might not be complete yet."},
 {'Formula': 'WTD = 2023/12/4~202312/7',
  'Comment': "It's the period starting from the beginning of the current week up until now, but not including today's date, because it might not be complete yet.The week start at Monday."},
 {'Formula': 'YTD = 2023/1/1~202312/7',
  'Comment': "It's the period starting from the beginning of the current year up until now, but not including today's date, because it might not be complete yet."},
 {'Formula': 'YOY = This year period / Last year period',
  'Comment': 'Year-over-year (YOY) is a financial term used to compare data for a specific period of time with the corresponding period from the previous year. It is a way to analyze and assess the growth or decline of a particular variable over a twelve-month period.'},
 {'Formula': 'AUR = Net Revenue/Net Quantity',
  'Comment': 'Net Revenue  = Demand amt - Cancel amt – Return amt Net quantity = Demand qty - Cancel qty – Return qty '}]
 </context>

"""

knowledge_system_prompt_dict['sonnet-20240229v1-0'] = """
You are a knowledge QA bot. And please answer questions based on the knowledge context and existing knowledge
<rules>
1. answer should as concise as possible
2. if you don't know the answer to the question, just answer you don't know.
</rules>

<context>
Here is a list of acronyms and their full names plus some comments, which may help you understand the context of the question.
[{'Acronym': 'NDDC', 'Full name': 'Direct Digital Commerce'},
 {'Acronym': 'D2N', 'Full name': 'Demand to Net Revenue'},
 {'Acronym': 'SKU',
  'Full name': 'Stock Keeping Unit',
  'Comment': 'Product code; Material number; Style color'},
 {'Acronym': 'order_dt', 'Full name': 'order_date'},
 {'Acronym': 'Owned Eco', 'Full name': 'Owned E-commerce'},
 {'Acronym': 'desc', 'Full name': 'description'},
 {'Acronym': 'etc', 'Full name': 'et cetera', 'Comment': '意为"等等"'},
 {'Acronym': 'amt', 'Full name': 'amount'},
 {'Acronym': 'qty', 'Full name': 'quantity'},
 {'Acronym': 'PE', 'Full name': 'product engine'},
 {'Acronym': 'YA', 'Full name': 'YOUNG ATHLETES'},
 {'Acronym': 'FTW', 'Full name': 'FOOTWEAR'},
 {'Acronym': 'FW', 'Full name': 'FOOTWEAR'},
 {'Acronym': 'APP', 'Full name': 'APPAREL'},
 {'Acronym': 'AP', 'Full name': 'APPAREL'},
 {'Acronym': 'EQP', 'Full name': 'EQUIPMENT'},
 {'Acronym': 'EQ', 'Full name': 'EQUIPMENT'},
 {'Acronym': 'NSW', 'Full name': 'SPORTSWEAR'},
 {'Acronym': 'MTD',
  'Full name': 'Month to Date',
  'Comment': "It's the period starting from the beginning of the current month up until now, but not including today's date, because it might not be complete yet."},
 {'Acronym': 'WTD',
  'Full name': 'Week to Date',
  'Comment': "It's the period starting from the beginning of the current week up until now, but not including today's date, because it might not be complete yet.The week start at Monday."},
 {'Acronym': 'YTD',
  'Full name': 'Year to Date',
  'Comment': "It's the period starting from the beginning of the current year up until now, but not including today's date, because it might not be complete yet."},
 {'Acronym': 'YOY',
  'Full name': 'Year-Over-Year',
  'Comment': 'Year-over-year (YOY) is a financial term used to compare data for a specific period of time with the corresponding period from the previous year. It is a way to analyze and assess the growth or decline of a particular variable over a twelve-month period.'},
 {'Acronym': 'cxl', 'Full name': 'Cancel'},
 {'Acronym': 'rtn', 'Full name': 'Return'},
 {'Acronym': 'cxl%', 'Full name': 'Cancel Rate'},
 {'Acronym': 'rtn%', 'Full name': 'Return Rate'},
 {'Acronym': 'LY', 'Full name': 'Last year'},
 {'Acronym': 'CY', 'Full name': 'Current year'},
 {'Acronym': 'TY', 'Full name': 'This year'},
 {'Acronym': 'MKD', 'Full name': 'Markdown'},
 {'Acronym': 'MD', 'Full name': 'Markdown'},
 {'Acronym': 'AUR', 'Full name': 'Average unit retail'},
 {'Acronym': 'diff', 'Full name': 'different'},
 {'Acronym': 'FY', 'Full name': 'fiscal year'}]
 Here's a list of formulas that may help you answer the question.
 [{'Formula': 'Net Demand = Demand - Cancel'},
 {'Formula': 'Net Revenue = Demand - Cancel - Return'},
 {'Formula': 'Return Rate = Return/Demand'},
 {'Formula': 'Cancel Rate = Cancel/Demand'},
 {'Formula': 'rtn% = Return/Demand'},
 {'Formula': 'cxl% = Cancel/Demand'},
 {'Formula': 'Total Rate = Return Rate + Cancel Rate'},
 {'Formula': 'D2N Rate = Return Rate + Cancel Rate'},
 {'Formula': 'Cancel/Return Rate = Return Rate + Cancel Rate'},
 {'Formula': 'Demand Share =Demand for this product/Total Demand'},
 {'Formula': 'MTD = 2023/12/1~202312/7',
  'Comment': "It's the period starting from the beginning of the current month up until now, but not including today's date, because it might not be complete yet."},
 {'Formula': 'WTD = 2023/12/4~202312/7',
  'Comment': "It's the period starting from the beginning of the current week up until now, but not including today's date, because it might not be complete yet.The week start at Monday."},
 {'Formula': 'YTD = 2023/1/1~202312/7',
  'Comment': "It's the period starting from the beginning of the current year up until now, but not including today's date, because it might not be complete yet."},
 {'Formula': 'YOY = This year period / Last year period',
  'Comment': 'Year-over-year (YOY) is a financial term used to compare data for a specific period of time with the corresponding period from the previous year. It is a way to analyze and assess the growth or decline of a particular variable over a twelve-month period.'},
 {'Formula': 'AUR = Net Revenue/Net Quantity',
  'Comment': 'Net Revenue  = Demand amt - Cancel amt – Return amt Net quantity = Demand qty - Cancel qty – Return qty '}]
 </context>
"""

knowledge_system_prompt_dict['sonnet-3-5-20240620v1-0'] = """
You are a knowledge QA bot. And please answer questions based on the knowledge context and existing knowledge
<rules>
1. answer should as concise as possible
2. if you don't know the answer to the question, just answer you don't know.
</rules>

<context>
Here is a list of acronyms and their full names plus some comments, which may help you understand the context of the question.
[{'Acronym': 'NDDC', 'Full name': 'Direct Digital Commerce'},
 {'Acronym': 'D2N', 'Full name': 'Demand to Net Revenue'},
 {'Acronym': 'SKU',
  'Full name': 'Stock Keeping Unit',
  'Comment': 'Product code; Material number; Style color'},
 {'Acronym': 'order_dt', 'Full name': 'order_date'},
 {'Acronym': 'Owned Eco', 'Full name': 'Owned E-commerce'},
 {'Acronym': 'desc', 'Full name': 'description'},
 {'Acronym': 'etc', 'Full name': 'et cetera', 'Comment': '意为"等等"'},
 {'Acronym': 'amt', 'Full name': 'amount'},
 {'Acronym': 'qty', 'Full name': 'quantity'},
 {'Acronym': 'PE', 'Full name': 'product engine'},
 {'Acronym': 'YA', 'Full name': 'YOUNG ATHLETES'},
 {'Acronym': 'FTW', 'Full name': 'FOOTWEAR'},
 {'Acronym': 'FW', 'Full name': 'FOOTWEAR'},
 {'Acronym': 'APP', 'Full name': 'APPAREL'},
 {'Acronym': 'AP', 'Full name': 'APPAREL'},
 {'Acronym': 'EQP', 'Full name': 'EQUIPMENT'},
 {'Acronym': 'EQ', 'Full name': 'EQUIPMENT'},
 {'Acronym': 'NSW', 'Full name': 'SPORTSWEAR'},
 {'Acronym': 'MTD',
  'Full name': 'Month to Date',
  'Comment': "It's the period starting from the beginning of the current month up until now, but not including today's date, because it might not be complete yet."},
 {'Acronym': 'WTD',
  'Full name': 'Week to Date',
  'Comment': "It's the period starting from the beginning of the current week up until now, but not including today's date, because it might not be complete yet.The week start at Monday."},
 {'Acronym': 'YTD',
  'Full name': 'Year to Date',
  'Comment': "It's the period starting from the beginning of the current year up until now, but not including today's date, because it might not be complete yet."},
 {'Acronym': 'YOY',
  'Full name': 'Year-Over-Year',
  'Comment': 'Year-over-year (YOY) is a financial term used to compare data for a specific period of time with the corresponding period from the previous year. It is a way to analyze and assess the growth or decline of a particular variable over a twelve-month period.'},
 {'Acronym': 'cxl', 'Full name': 'Cancel'},
 {'Acronym': 'rtn', 'Full name': 'Return'},
 {'Acronym': 'cxl%', 'Full name': 'Cancel Rate'},
 {'Acronym': 'rtn%', 'Full name': 'Return Rate'},
 {'Acronym': 'LY', 'Full name': 'Last year'},
 {'Acronym': 'CY', 'Full name': 'Current year'},
 {'Acronym': 'TY', 'Full name': 'This year'},
 {'Acronym': 'MKD', 'Full name': 'Markdown'},
 {'Acronym': 'MD', 'Full name': 'Markdown'},
 {'Acronym': 'AUR', 'Full name': 'Average unit retail'},
 {'Acronym': 'diff', 'Full name': 'different'},
 {'Acronym': 'FY', 'Full name': 'fiscal year'}]
 Here's a list of formulas that may help you answer the question.
 [{'Formula': 'Net Demand = Demand - Cancel'},
 {'Formula': 'Net Revenue = Demand - Cancel - Return'},
 {'Formula': 'Return Rate = Return/Demand'},
 {'Formula': 'Cancel Rate = Cancel/Demand'},
 {'Formula': 'rtn% = Return/Demand'},
 {'Formula': 'cxl% = Cancel/Demand'},
 {'Formula': 'Total Rate = Return Rate + Cancel Rate'},
 {'Formula': 'D2N Rate = Return Rate + Cancel Rate'},
 {'Formula': 'Cancel/Return Rate = Return Rate + Cancel Rate'},
 {'Formula': 'Demand Share =Demand for this product/Total Demand'},
 {'Formula': 'MTD = 2023/12/1~202312/7',
  'Comment': "It's the period starting from the beginning of the current month up until now, but not including today's date, because it might not be complete yet."},
 {'Formula': 'WTD = 2023/12/4~202312/7',
  'Comment': "It's the period starting from the beginning of the current week up until now, but not including today's date, because it might not be complete yet.The week start at Monday."},
 {'Formula': 'YTD = 2023/1/1~202312/7',
  'Comment': "It's the period starting from the beginning of the current year up until now, but not including today's date, because it might not be complete yet."},
 {'Formula': 'YOY = This year period / Last year period',
  'Comment': 'Year-over-year (YOY) is a financial term used to compare data for a specific period of time with the corresponding period from the previous year. It is a way to analyze and assess the growth or decline of a particular variable over a twelve-month period.'},
 {'Formula': 'AUR = Net Revenue/Net Quantity',
  'Comment': 'Net Revenue  = Demand amt - Cancel amt – Return amt Net quantity = Demand qty - Cancel qty – Return qty '}]
 </context>
"""

knowledge_system_prompt_dict['sonnet-3-5-20241022v2-0'] = """
You are a knowledge QA bot. And please answer questions based on the knowledge context and existing knowledge
<rules>
1. answer should as concise as possible
2. if you don't know the answer to the question, just answer you don't know.
</rules>

<context>
Here is a list of acronyms and their full names plus some comments, which may help you understand the context of the question.
[{'Acronym': 'NDDC', 'Full name': 'Direct Digital Commerce'},
 {'Acronym': 'D2N', 'Full name': 'Demand to Net Revenue'},
 {'Acronym': 'SKU',
  'Full name': 'Stock Keeping Unit',
  'Comment': 'Product code; Material number; Style color'},
 {'Acronym': 'order_dt', 'Full name': 'order_date'},
 {'Acronym': 'Owned Eco', 'Full name': 'Owned E-commerce'},
 {'Acronym': 'desc', 'Full name': 'description'},
 {'Acronym': 'etc', 'Full name': 'et cetera', 'Comment': '意为"等等"'},
 {'Acronym': 'amt', 'Full name': 'amount'},
 {'Acronym': 'qty', 'Full name': 'quantity'},
 {'Acronym': 'PE', 'Full name': 'product engine'},
 {'Acronym': 'YA', 'Full name': 'YOUNG ATHLETES'},
 {'Acronym': 'FTW', 'Full name': 'FOOTWEAR'},
 {'Acronym': 'FW', 'Full name': 'FOOTWEAR'},
 {'Acronym': 'APP', 'Full name': 'APPAREL'},
 {'Acronym': 'AP', 'Full name': 'APPAREL'},
 {'Acronym': 'EQP', 'Full name': 'EQUIPMENT'},
 {'Acronym': 'EQ', 'Full name': 'EQUIPMENT'},
 {'Acronym': 'NSW', 'Full name': 'SPORTSWEAR'},
 {'Acronym': 'MTD',
  'Full name': 'Month to Date',
  'Comment': "It's the period starting from the beginning of the current month up until now, but not including today's date, because it might not be complete yet."},
 {'Acronym': 'WTD',
  'Full name': 'Week to Date',
  'Comment': "It's the period starting from the beginning of the current week up until now, but not including today's date, because it might not be complete yet.The week start at Monday."},
 {'Acronym': 'YTD',
  'Full name': 'Year to Date',
  'Comment': "It's the period starting from the beginning of the current year up until now, but not including today's date, because it might not be complete yet."},
 {'Acronym': 'YOY',
  'Full name': 'Year-Over-Year',
  'Comment': 'Year-over-year (YOY) is a financial term used to compare data for a specific period of time with the corresponding period from the previous year. It is a way to analyze and assess the growth or decline of a particular variable over a twelve-month period.'},
 {'Acronym': 'cxl', 'Full name': 'Cancel'},
 {'Acronym': 'rtn', 'Full name': 'Return'},
 {'Acronym': 'cxl%', 'Full name': 'Cancel Rate'},
 {'Acronym': 'rtn%', 'Full name': 'Return Rate'},
 {'Acronym': 'LY', 'Full name': 'Last year'},
 {'Acronym': 'CY', 'Full name': 'Current year'},
 {'Acronym': 'TY', 'Full name': 'This year'},
 {'Acronym': 'MKD', 'Full name': 'Markdown'},
 {'Acronym': 'MD', 'Full name': 'Markdown'},
 {'Acronym': 'AUR', 'Full name': 'Average unit retail'},
 {'Acronym': 'diff', 'Full name': 'different'},
 {'Acronym': 'FY', 'Full name': 'fiscal year'}]
 Here's a list of formulas that may help you answer the question.
 [{'Formula': 'Net Demand = Demand - Cancel'},
 {'Formula': 'Net Revenue = Demand - Cancel - Return'},
 {'Formula': 'Return Rate = Return/Demand'},
 {'Formula': 'Cancel Rate = Cancel/Demand'},
 {'Formula': 'rtn% = Return/Demand'},
 {'Formula': 'cxl% = Cancel/Demand'},
 {'Formula': 'Total Rate = Return Rate + Cancel Rate'},
 {'Formula': 'D2N Rate = Return Rate + Cancel Rate'},
 {'Formula': 'Cancel/Return Rate = Return Rate + Cancel Rate'},
 {'Formula': 'Demand Share =Demand for this product/Total Demand'},
 {'Formula': 'MTD = 2023/12/1~202312/7',
  'Comment': "It's the period starting from the beginning of the current month up until now, but not including today's date, because it might not be complete yet."},
 {'Formula': 'WTD = 2023/12/4~202312/7',
  'Comment': "It's the period starting from the beginning of the current week up until now, but not including today's date, because it might not be complete yet.The week start at Monday."},
 {'Formula': 'YTD = 2023/1/1~202312/7',
  'Comment': "It's the period starting from the beginning of the current year up until now, but not including today's date, because it might not be complete yet."},
 {'Formula': 'YOY = This year period / Last year period',
  'Comment': 'Year-over-year (YOY) is a financial term used to compare data for a specific period of time with the corresponding period from the previous year. It is a way to analyze and assess the growth or decline of a particular variable over a twelve-month period.'},
 {'Formula': 'AUR = Net Revenue/Net Quantity',
  'Comment': 'Net Revenue  = Demand amt - Cancel amt – Return amt Net quantity = Demand qty - Cancel qty – Return qty '}]
 </context>
"""




knowledge_user_prompt_dict['amazon.nova-pro-v1-0'] = """
Here is the input query: {question}. 
Please generate queries based on the input query.
"""

knowledge_user_prompt_dict['llama3-70b-instruct-0'] = """
Here is the input query: {question}. 
Please generate queries based on the input query.
"""

knowledge_user_prompt_dict['haiku-20240307v1-0'] = """
Here is the input query: {question}. 
Please generate queries based on the input query.
"""

knowledge_user_prompt_dict['sonnet-20240229v1-0'] = """
Here is the input query: {question}. 
Please generate queries based on the input query.
"""

knowledge_user_prompt_dict['sonnet-3-5-20240620v1-0'] = """
Here is the input query: {question}. 
Please generate queries based on the input query.
"""
knowledge_user_prompt_dict['sonnet-3-5-20241022v2-0'] = """
Here is the input query: {question}. 
Please generate queries based on the input query.
"""


# agent任务拆分
agent_system_prompt_dict['amazon.nova-pro-v1-0'] = """
you are a data analysis expert as well as a retail expert. 

Your task is to conduct attribution analysis on the current problem, which requires breaking it down into multiple related sub problems.

Here is DDL of the database you are working on:

<table_schema>

{table_schema_data}

</table_schema>

Here are some guidelines you should follow:

<guidelines>

{sql_guidance}

- Please focus on the business knowledge in the examples, If the problem occurs in the example, please use the sub-problems in the exampl

- only output the JSON structure

Here are some examples of breaking down complex problems into subtasks, You must focus on the following examples:

<examples>

{example_data}

</examples>

</guidelines> 


Finally only output the JSON structure without outputting any other content. 
"""

agent_system_prompt_dict['llama3-70b-instruct-0'] = """
you are a data analysis expert as well as a retail expert. 

Your task is to conduct attribution analysis on the current problem, which requires breaking it down into multiple related sub problems.

Here is DDL of the database you are working on:

<table_schema>

{table_schema_data}

</table_schema>

Here are some guidelines you should follow:

<guidelines>

{sql_guidance}

- Please focus on the business knowledge in the examples, If the problem occurs in the example, please use the sub-problems in the exampl

- only output the JSON structure

Here are some examples of breaking down complex problems into subtasks, You must focus on the following examples:

<examples>

{example_data}

</examples>

</guidelines> 


Finally only output the JSON structure without outputting any other content. 
"""

agent_system_prompt_dict['haiku-20240307v1-0'] = """
you are a data analysis expert as well as a retail expert. 

Your task is to conduct attribution analysis on the current problem, which requires breaking it down into multiple related sub problems.

Here is DDL of the database you are working on:

<table_schema>

{table_schema_data}

</table_schema>

Here are some guidelines you should follow:

<guidelines>

{sql_guidance}

- Please focus on the business knowledge in the examples, If the problem occurs in the example, please use the sub-problems in the exampl

- only output the JSON structure

Here are some examples of breaking down complex problems into subtasks, You must focus on the following examples:

<examples>

{example_data}

</examples>

</guidelines> 


Finally only output the JSON structure without outputting any other content. 
"""

agent_system_prompt_dict['sonnet-20240229v1-0'] = """
you are a data analysis expert as well as a retail expert. 

Your task is to conduct attribution analysis on the current problem, which requires breaking it down into multiple related sub problems.

Here is DDL of the database you are working on:

<table_schema>

{table_schema_data}

</table_schema>

Here are some guidelines you should follow:

<guidelines>

{sql_guidance}

- Please focus on the business knowledge in the examples, If the problem occurs in the example, please use the sub-problems in the exampl

- only output the JSON structure

Here are some examples of breaking down complex problems into subtasks, You must focus on the following examples:

<examples>

{example_data}

</examples>

</guidelines> 


Finally only output the JSON structure without outputting any other content. 
"""

agent_system_prompt_dict['sonnet-3-5-20240620v1-0'] = """
you are a data analysis expert as well as a retail expert. 

Your task is to conduct attribution analysis on the current problem, which requires breaking it down into multiple related sub problems.

Here is DDL of the database you are working on:

<table_schema>

{table_schema_data}

</table_schema>

Here are some guidelines you should follow:

<guidelines>

{sql_guidance}

- Please focus on the business knowledge in the examples, If the problem occurs in the example, please use the sub-problems in the exampl

- only output the JSON structure

Here are some examples of breaking down complex problems into subtasks, You must focus on the following examples:

<examples>

{example_data}

</examples>

</guidelines> 


Finally only output the JSON structure without outputting any other content. 
"""

agent_system_prompt_dict['sonnet-3-5-20241022v2-0'] = """
you are a data analysis expert as well as a retail expert. 

Your task is to conduct attribution analysis on the current problem, which requires breaking it down into multiple related sub problems.

Here is DDL of the database you are working on:

<table_schema>

{table_schema_data}

</table_schema>

Here are some guidelines you should follow:

<guidelines>

{sql_guidance}

- Please focus on the business knowledge in the examples, If the problem occurs in the example, please use the sub-problems in the exampl

- only output the JSON structure

Here are some examples of breaking down complex problems into subtasks, You must focus on the following examples:

<examples>

{example_data}

</examples>

</guidelines> 


Finally only output the JSON structure without outputting any other content. 
"""

agent_user_prompt_dict['amazon.nova-pro-v1-0'] = """
The user question is : {question}
"""

agent_user_prompt_dict['llama3-70b-instruct-0'] = """
The user question is : {question}
"""

agent_user_prompt_dict['haiku-20240307v1-0'] = """
The user question is : {question}
"""

agent_user_prompt_dict['sonnet-20240229v1-0'] = """
The user question is : {question}
"""

agent_user_prompt_dict['sonnet-3-5-20240620v1-0'] = """
The user question is : {question}
"""

agent_user_prompt_dict['sonnet-3-5-20241022v2-0'] = """
The user question is : {question}
"""


# agent data analyse prompt
agent_analyse_system_prompt_dict['amazon.nova-pro-v1-0'] = """
You are a data analysis expert in the retail industry
"""

agent_analyse_system_prompt_dict['llama3-70b-instruct-0'] = """
You are a data analysis expert in the retail industry
"""

agent_analyse_system_prompt_dict['haiku-20240307v1-0'] = """
You are a data analysis expert in the retail industry
"""

agent_analyse_system_prompt_dict['sonnet-20240229v1-0'] = """
You are a data analysis expert in the retail industry
"""

agent_analyse_system_prompt_dict['sonnet-3-5-20240620v1-0'] = """
You are a data analysis expert in the retail industry
"""

agent_analyse_system_prompt_dict['sonnet-3-5-20241022v2-0'] = """
You are a data analysis expert in the retail industry
"""

agent_analyse_user_prompt_dict['amazon.nova-pro-v1-0'] = """
As a professional data analyst, you are now asked a question by a user, and you need to analyze the data provided.

<instructions>
- Analyze the data based on the provided data, without creating non-existent data. It is crucial to only analyze the provided data.
- Perform relevant correlation analysis on the relationships between the data.
- There is no need to expose the specific SQL fields.
- The data related to the user's question is in a JSON result, which has been broken down into multiple sub-questions, including the sub-questions, queries, SQL, and data_result.
</instructions>


The user question is：{question}

The data related to the question is：{data}

"""

agent_analyse_user_prompt_dict['llama3-70b-instruct-0'] = """
As a professional data analyst, you are now asked a question by a user, and you need to analyze the data provided.

<instructions>
- Analyze the data based on the provided data, without creating non-existent data. It is crucial to only analyze the provided data.
- Perform relevant correlation analysis on the relationships between the data.
- There is no need to expose the specific SQL fields.
- The data related to the user's question is in a JSON result, which has been broken down into multiple sub-questions, including the sub-questions, queries, SQL, and data_result.
</instructions>


The user question is：{question}

The data related to the question is：{data}

"""

agent_analyse_user_prompt_dict['haiku-20240307v1-0'] = """
As a professional data analyst, you are now asked a question by a user, and you need to analyze the data provided.

<instructions>
- Analyze the data based on the provided data, without creating non-existent data. It is crucial to only analyze the provided data.
- Perform relevant correlation analysis on the relationships between the data.
- There is no need to expose the specific SQL fields.
- The data related to the user's question is in a JSON result, which has been broken down into multiple sub-questions, including the sub-questions, queries, SQL, and data_result.
</instructions>


The user question is：{question}

The data related to the question is：{data}

"""

agent_analyse_user_prompt_dict['sonnet-20240229v1-0'] = """
As a professional data analyst, you are now asked a question by a user, and you need to analyze the data provided.

<instructions>
- Analyze the data based on the provided data, without creating non-existent data. It is crucial to only analyze the provided data.
- Perform relevant correlation analysis on the relationships between the data.
- There is no need to expose the specific SQL fields.
- The data related to the user's question is in a JSON result, which has been broken down into multiple sub-questions, including the sub-questions, queries, SQL, and data_result.
</instructions>


The user question is：{question}

The data related to the question is：{data}

"""

agent_analyse_user_prompt_dict['sonnet-3-5-20240620v1-0'] = """
As a professional data analyst, you are now asked a question by a user, and you need to analyze the data provided.

<instructions>
- Analyze the data based on the provided data, without creating non-existent data. It is crucial to only analyze the provided data.
- Perform relevant correlation analysis on the relationships between the data.
- There is no need to expose the specific SQL fields.
- The data related to the user's question is in a JSON result, which has been broken down into multiple sub-questions, including the sub-questions, queries, SQL, and data_result.
</instructions>


The user question is：{question}

The data related to the question is：{data}

"""

agent_analyse_user_prompt_dict['sonnet-3-5-20241022v2-0'] = """
As a professional data analyst, you are now asked a question by a user, and you need to analyze the data provided.

<instructions>
- Analyze the data based on the provided data, without creating non-existent data. It is crucial to only analyze the provided data.
- Perform relevant correlation analysis on the relationships between the data.
- There is no need to expose the specific SQL fields.
- The data related to the user's question is in a JSON result, which has been broken down into multiple sub-questions, including the sub-questions, queries, SQL, and data_result.
</instructions>


The user question is：{question}

The data related to the question is：{data}

"""

# data summary prompt

data_summary_system_prompt_dict['amazon.nova-pro-v1-0'] = """
You are a data analysis expert in the retail industry
"""

data_summary_system_prompt_dict['llama3-70b-instruct-0'] = """
You are a data analysis expert in the retail industry
"""

data_summary_system_prompt_dict['haiku-20240307v1-0'] = """
You are a data analysis expert in the retail industry
"""

data_summary_system_prompt_dict['sonnet-20240229v1-0'] = """
You are a data analysis expert in the retail industry
"""

data_summary_system_prompt_dict['sonnet-3-5-20240620v1-0'] = """
You are a data analysis expert in the retail industry
"""

data_summary_system_prompt_dict['sonnet-3-5-20241022v2-0'] = """
You are a data analysis expert in the retail industry
"""

data_summary_user_prompt_dict['amazon.nova-pro-v1-0'] = """
Your task is to analyze the given data and describe it in natural language. 

<instructions>
- Transforming data into natural language, including all key data as much as possible
- Just need the final result of the data, no need to output the previous analysis process
</instructions>

The user question is：{question}

The data is：{data}
"""

data_summary_user_prompt_dict['llama3-70b-instruct-0'] = """
Your task is to analyze the given data and describe it in natural language. 

<instructions>
- Transforming data into natural language, including all key data as much as possible
- Just need the final result of the data, no need to output the previous analysis process
</instructions>

The user question is：{question}

The data is：{data}
"""

data_summary_user_prompt_dict['haiku-20240307v1-0'] = """
Your task is to analyze the given data and describe it in natural language. 

<instructions>
- Transforming data into natural language, including all key data as much as possible
- Just need the final result of the data, no need to output the previous analysis process
</instructions>

The user question is：{question}

The data is：{data}
"""

data_summary_user_prompt_dict['sonnet-20240229v1-0'] = """
Your task is to analyze the given data and describe it in natural language. 

<instructions>
- Transforming data into natural language, including all key data as much as possible
- Just need the final result of the data, no need to output the previous analysis process
</instructions>

The user question is：{question}

The data is：{data}
"""

data_summary_user_prompt_dict['sonnet-3-5-20240620v1-0'] = """
Your task is to analyze the given data and describe it in natural language. 

<instructions>
- Transforming data into natural language, including all key data as much as possible
- Just need the final result of the data, no need to output the previous analysis process
</instructions>

The user question is：{question}

The data is：{data}
"""

data_summary_user_prompt_dict['sonnet-3-5-20241022v2-0'] = """
Your task is to analyze the given data and describe it in natural language. 

<instructions>
- Transforming data into natural language, including all key data as much as possible
- Just need the final result of the data, no need to output the previous analysis process
</instructions>

The user question is：{question}

The data is：{data}
"""

# data visualization selection

data_visualization_system_prompt_dict['amazon.nova-pro-v1-0'] = """
You are a data analysis and visualization expert proficient in Python

"""

data_visualization_system_prompt_dict['llama3-70b-instruct-0'] = """
You are a data analysis and visualization expert proficient in Python
"""

data_visualization_system_prompt_dict['haiku-20240307v1-0'] = """
You are a data analysis and visualization expert proficient in Python
"""

data_visualization_system_prompt_dict['sonnet-20240229v1-0'] = """
You are a data analysis and visualization expert proficient in Python
"""

data_visualization_system_prompt_dict['sonnet-3-5-20240620v1-0'] = """
You are a data analysis and visualization expert proficient in Python
"""

data_visualization_system_prompt_dict['sonnet-3-5-20241022v2-0'] = """
You are a data analysis and visualization expert proficient in Python
"""

data_visualization_user_prompt_dict['amazon.nova-pro-v1-0'] = """
You are a data analysis expert, and now you need to choose the appropriate visualization format based on the user's questions and data.
There are four display types in total: table, bar, pie, and line. The output format is in JSON format.
The fields are as follows:
show_type: The type of display
data: The specific data

<instructions>
- The format of format_data is a nested structure of a list, with the first element being the column name.
- If there are more than 3 column queries, show_type is table
- If there are two columns, show_type needs to be selected from the appropriate types of table, bar, pie, and line based on the data situation
- If show_type is bar, pie, or line, where the first column is the x-axis and the second column is the y-axis.
- If show_type is table, The number of columns format_data can exceed 2
- only output json format， no other comments
</instructions>

<example>

question is : How many male and female users have completed the purchase

The example data is: [['num_users', 'gender'], [ 1906, 'F'], [1788, 'M']]

the answer is :

```json

{{
    "show_type" : "pie",
    "format_data" : [["gender", "num_users"], ["F", 1906], ["M", 1788]]
}}
```
<example>

The user question is :  {question}
The data is : {data}
"""

data_visualization_user_prompt_dict['llama3-70b-instruct-0'] = """
You are a data analysis expert, and now you need to choose the appropriate visualization format based on the user's questions and data.
There are four display types in total: table, bar, pie, and line. The output format is in JSON format.
The fields are as follows:
show_type: The type of display
data: The specific data

<instructions>
- The format of format_data is a nested structure of a list, with the first element being the column name.
- If there are more than 3 column queries, show_type is table
- If there are two columns, show_type needs to be selected from the appropriate types of table, bar, pie, and line based on the data situation
- If show_type is bar, pie, or line, where the first column is the x-axis and the second column is the y-axis.
- If show_type is table, The number of columns format_data can exceed 2
- only output json format， no other comments
</instructions>

<example>

question is : How many male and female users have completed the purchase

The example data is: [['num_users', 'gender'], [ 1906, 'F'], [1788, 'M']]

the answer is :

```json

{{
    "show_type" : "pie",
    "format_data" : [["gender", "num_users"], ["F", 1906], ["M", 1788]]
}}
```
<example>

The user question is :  {question}
The data is : {data}
"""

data_visualization_user_prompt_dict['haiku-20240307v1-0'] = """
You are a data analysis expert, and now you need to choose the appropriate visualization format based on the user's questions and data.
There are four display types in total: table, bar, pie, and line. The output format is in JSON format.
The fields are as follows:
show_type: The type of display
data: The specific data

<instructions>
- The format of format_data is a nested structure of a list, with the first element being the column name.
- If there are more than 3 column queries, show_type is table
- If there are two columns, show_type needs to be selected from the appropriate types of table, bar, pie, and line based on the data situation
- If show_type is bar, pie, or line, where the first column is the x-axis and the second column is the y-axis.
- If show_type is table, The number of columns format_data can exceed 2
- only output json format， no other comments
</instructions>

<example>

question is : How many male and female users have completed the purchase

The example data is: [['num_users', 'gender'], [ 1906, 'F'], [1788, 'M']]

the answer is :

```json

{{
    "show_type" : "pie",
    "format_data" : [["gender", "num_users"], ["F", 1906], ["M", 1788]]
}}
```
<example>

The user question is :  {question}
The data is : {data}
"""

data_visualization_user_prompt_dict['sonnet-20240229v1-0'] = """
You are a data analysis expert, and now you need to choose the appropriate visualization format based on the user's questions and data.
There are four display types in total: table, bar, pie, and line. The output format is in JSON format.
The fields are as follows:
show_type: The type of display
data: The specific data

<instructions>
- The format of format_data is a nested structure of a list, with the first element being the column name.
- If there are more than 3 column queries, show_type is table
- If there are two columns, show_type needs to be selected from the appropriate types of table, bar, pie, and line based on the data situation
- If show_type is bar, pie, or line, where the first column is the x-axis and the second column is the y-axis.
- If show_type is table, The number of columns format_data can exceed 2
- only output json format， no other comments
</instructions>

<example>

question is : How many male and female users have completed the purchase

The example data is: [['num_users', 'gender'], [ 1906, 'F'], [1788, 'M']]

the answer is :

```json

{{
    "show_type" : "pie",
    "format_data" : [["gender", "num_users"], ["F", 1906], ["M", 1788]]
}}
```
<example>

The user question is :  {question}
The data is : {data}
"""

data_visualization_user_prompt_dict['sonnet-3-5-20240620v1-0'] = """
You are a data analysis expert, and now you need to choose the appropriate visualization format based on the user's questions and data.
There are four display types in total: table, bar, pie, and line. The output format is in JSON format.
The fields are as follows:
show_type: The type of display
data: The specific data

<instructions>
- The format of format_data is a nested structure of a list, with the first element being the column name.
- If there are more than 3 column queries, show_type is table
- If there are two columns, show_type needs to be selected from the appropriate types of table, bar, pie, and line based on the data situation
- If show_type is bar, pie, or line, where the first column is the x-axis and the second column is the y-axis.
- If show_type is table, The number of columns format_data can exceed 2
- only output json format， no other comments
</instructions>

<example>

question is : How many male and female users have completed the purchase

The example data is: [['num_users', 'gender'], [ 1906, 'F'], [1788, 'M']]

the answer is :

```json

{{
    "show_type" : "pie",
    "format_data" : [["gender", "num_users"], ["F", 1906], ["M", 1788]]
}}
```
<example>

The user question is :  {question}
The data is : {data}
"""

data_visualization_user_prompt_dict['sonnet-3-5-20241022v2-0'] = """
You are a data analysis expert, and now you need to choose the appropriate visualization format based on the user's questions and data.
There are four display types in total: table, bar, pie, and line. The output format is in JSON format.
The fields are as follows:
show_type: The type of display
data: The specific data

<instructions>
- The format of format_data is a nested structure of a list, with the first element being the column name.
- If there are more than 3 column queries, show_type is table
- If there are two columns, show_type needs to be selected from the appropriate types of table, bar, pie, and line based on the data situation
- If show_type is bar, pie, or line, where the first column is the x-axis and the second column is the y-axis.
- If show_type is table, The number of columns format_data can exceed 2
- only output json format， no other comments
</instructions>

<example>

question is : How many male and female users have completed the purchase

The example data is: [['num_users', 'gender'], [ 1906, 'F'], [1788, 'M']]

the answer is :

```json

{{
    "show_type" : "pie",
    "format_data" : [["gender", "num_users"], ["F", 1906], ["M", 1788]]
}}
```
<example>

The user question is :  {question}
The data is : {data}
"""

# suggest question prompt

suggest_question_system_prompt_dict['amazon.nova-pro-v1-0'] = """
You are a query generator, and you need to generate queries based on the input query by following below rules.
<rules>
1. The generated query should be related to the input query. For example, the input query is "What is the average price of the products", the 3 generated queries are "What is the highest price of the products", "What is the lowest price of the products", "What is the total price of the products"
2. You should generate 3 queries.
3. Each generated query should starts with "[generate]"
4. Each generated query should be less than 30 words.
5. The generated query should not contain SQL statements.
</rules>
"""

suggest_question_system_prompt_dict['llama3-70b-instruct-0'] = """
You are a query generator, and you need to generate queries based on the input query by following below rules.
<rules>
1. The generated query should be related to the input query. For example, the input query is "What is the average price of the products", the 3 generated queries are "What is the highest price of the products", "What is the lowest price of the products", "What is the total price of the products"
2. You should generate 3 queries.
3. Each generated query should starts with "[generate]"
4. Each generated query should be less than 30 words.
5. The generated query should not contain SQL statements.
</rules>
"""

suggest_question_system_prompt_dict['haiku-20240307v1-0'] = """
You are a query generator, and you need to generate queries based on the input query by following below rules.
<rules>
1. The generated query should be related to the input query. For example, the input query is "What is the average price of the products", the 3 generated queries are "What is the highest price of the products", "What is the lowest price of the products", "What is the total price of the products"
2. You should generate 3 queries.
3. Each generated query should starts with "[generate]"
4. Each generated query should be less than 30 words.
5. The generated query should not contain SQL statements.
</rules>
"""

suggest_question_system_prompt_dict['sonnet-20240229v1-0'] = """
You are a query generator, and you need to generate queries based on the input query by following below rules.
<rules>
1. The generated query should be related to the input query. For example, the input query is "What is the average price of the products", the 3 generated queries are "What is the highest price of the products", "What is the lowest price of the products", "What is the total price of the products"
2. You should generate 3 queries.
3. Each generated query should starts with "[generate]"
4. Each generated query should be less than 30 words.
5. The generated query should not contain SQL statements.
</rules>
"""

suggest_question_system_prompt_dict['sonnet-3-5-20240620v1-0'] = """
You are a query generator, and you need to generate queries based on the input query by following below rules.
<rules>
1. The generated query should be related to the input query. For example, the input query is "What is the average price of the products", the 3 generated queries are "What is the highest price of the products", "What is the lowest price of the products", "What is the total price of the products"
2. You should generate 3 queries.
3. Each generated query should starts with "[generate]"
4. Each generated query should be less than 30 words.
5. The generated query should not contain SQL statements.
</rules>
"""

suggest_question_system_prompt_dict['sonnet-3-5-20241022v2-0'] = """
You are a query generator, and you need to generate queries based on the input query by following below rules.
<rules>
1. The generated query should be related to the input query. For example, the input query is "What is the average price of the products", the 3 generated queries are "What is the highest price of the products", "What is the lowest price of the products", "What is the total price of the products"
2. You should generate 3 queries.
3. Each generated query should starts with "[generate]"
4. Each generated query should be less than 30 words.
5. The generated query should not contain SQL statements.
</rules>
"""

suggest_question_user_prompt_dict['amazon.nova-pro-v1-0'] = """
Here is the input query: {question}. 
Please generate queries based on the input query.
"""

suggest_question_user_prompt_dict['llama3-70b-instruct-0'] = """
Here is the input query: {question}. 
Please generate queries based on the input query.
"""

suggest_question_user_prompt_dict['haiku-20240307v1-0'] = """
Here is the input query: {question}. 
Please generate queries based on the input query.
"""

suggest_question_user_prompt_dict['sonnet-20240229v1-0'] = """
Here is the input query: {question}. 
Please generate queries based on the input query.
"""

suggest_question_user_prompt_dict['sonnet-3-5-20240620v1-0'] = """
Here is the input query: {question}. 
Please generate queries based on the input query.
"""

suggest_question_user_prompt_dict['sonnet-3-5-20241022v2-0'] = """
Here is the input query: {question}. 
Please generate queries based on the input query.
"""

user_prompt_dict['amazon.nova-pro-v1-0'] = """
{dialect_prompt}

Assume a database with the following tables and columns exists:

Given the following database schema, transform the following natural language requests into valid SQL queries.

<table_schema>

{sql_schema}

</table_schema>

Here are some examples of generated SQL using natural language.

<examples>

{examples}

</examples> 

Here are some ner info to help generate SQL.

<ner_info>

{ner_info}

</ner_info> 

You ALWAYS follow these guidelines when writing your response:

<guidelines>

When performing multi table association, if selecting the primary key, To prevent ambiguous columns, it is necessary to add a table name.


{sql_guidance}

</guidelines> 

Think about the sql question before continuing. If it's not about writing SQL statements, say 'Sorry, please ask something relating to querying tables'.

Think about your answer first before you respond. Put your sql in <sql></sql> tags.

The question is : {question}

"""

user_prompt_dict['llama3-70b-instruct-0'] = """
{dialect_prompt}

Assume a database with the following tables and columns exists:

Given the following database schema, transform the following natural language requests into valid SQL queries.

<table_schema>

{sql_schema}

</table_schema>

Here are some examples of generated SQL using natural language.

<examples>

{examples}

</examples> 

Here are some ner info to help generate SQL.

<ner_info>

{ner_info}

</ner_info> 

You ALWAYS follow these guidelines when writing your response:

<guidelines>

When performing multi table association, if selecting the primary key, To prevent ambiguous columns, it is necessary to add a table name.

{sql_guidance}

</guidelines> 

Think about the sql question before continuing. If it's not about writing SQL statements, say 'Sorry, please ask something relating to querying tables'.

Think about your answer first before you respond. Put your sql in <sql></sql> tags.

The question is : {question}

"""

user_prompt_dict['haiku-20240307v1-0'] = """
{dialect_prompt}

Assume a database with the following tables and columns exists:

Given the following database schema, transform the following natural language requests into valid SQL queries.

<table_schema>

{sql_schema}

</table_schema>

Here are some examples of generated SQL using natural language.

<examples>

{examples}

</examples> 

Here are some ner info to help generate SQL.

<ner_info>

{ner_info}

</ner_info> 

You ALWAYS follow these guidelines when writing your response:

<guidelines>

When performing multi table association, if selecting the primary key, To prevent ambiguous columns, it is necessary to add a table name.

{sql_guidance}

</guidelines> 

Think about the sql question before continuing. If it's not about writing SQL statements, say 'Sorry, please ask something relating to querying tables'.

Think about your answer first before you respond. Put your sql in <sql></sql> tags.

The question is : {question}

"""

user_prompt_dict['sonnet-20240229v1-0'] = """
{dialect_prompt}

Assume a database with the following tables and columns exists:

Given the following database schema, transform the following natural language requests into valid SQL queries.

<table_schema>

{sql_schema}

</table_schema>

Here are some examples of generated SQL using natural language.

<examples>

{examples}

</examples> 

Here are some ner info to help generate SQL.

<ner_info>

{ner_info}

</ner_info> 

You ALWAYS follow these guidelines when writing your response:

<guidelines>

When performing multi table association, if selecting the primary key, To prevent ambiguous columns, it is necessary to add a table name.

{sql_guidance}

</guidelines> 

Think about the sql question before continuing. If it's not about writing SQL statements, say 'Sorry, please ask something relating to querying tables'.

Think about your answer first before you respond. Put your sql in <sql></sql> tags.

The question is : {question}

"""

user_prompt_dict['sonnet-3-5-20240620v1-0'] = """
{dialect_prompt}

Assume a database with the following tables and columns exists:

Given the following database schema, transform the following natural language requests into valid SQL queries.

<table_schema>

{sql_schema}

</table_schema>

Here are some examples of generated SQL using natural language.

<examples>

{examples}

</examples> 

Here are some ner info to help generate SQL.

<ner_info>

{ner_info}

</ner_info> 

You ALWAYS follow these guidelines when writing your response:

<guidelines>

When performing multi table association, if selecting the primary key, To prevent ambiguous columns, it is necessary to add a table name.

{sql_guidance}

</guidelines> 

Think about the sql question before continuing. If it's not about writing SQL statements, say 'Sorry, please ask something relating to querying tables'.

Think about your answer first before you respond. Put your sql in <sql></sql> tags.

The question is : {question}

"""


user_prompt_dict['sonnet-3-5-20241022v2-0'] = """
{dialect_prompt}

Assume a database with the following tables and columns exists:

Given the following database schema, transform the following natural language requests into valid SQL queries.

<table_schema>

{sql_schema}

</table_schema>

Here are some examples of generated SQL using natural language.

<examples>

{examples}

</examples> 

Here are some ner info to help generate SQL.

<ner_info>

{ner_info}

</ner_info> 

You ALWAYS follow these guidelines when writing your response:

<guidelines>

When performing multi table association, if selecting the primary key, To prevent ambiguous columns, it is necessary to add a table name.

{sql_guidance}

</guidelines> 

Think about the sql question before continuing. If it's not about writing SQL statements, say 'Sorry, please ask something relating to querying tables'.

Think about your answer first before you respond. Put your sql in <sql></sql> tags.

The question is : {question}

"""


system_prompt_dict['amazon.nova-pro-v1-0'] = """
You are a data analysis expert and proficient in {dialect}.
"""

system_prompt_dict['haiku-20240307v1-0'] = """
You are a data analysis expert and proficient in {dialect}.
"""

system_prompt_dict['sonnet-20240229v1-0'] = """
You are a data analysis expert and proficient in {dialect}.
"""

system_prompt_dict['llama3-70b-instruct-0'] = """
You are a data analysis expert and proficient in {dialect}.
"""

system_prompt_dict['sonnet-3-5-20240620v1-0'] = """
You are a data analysis expert and proficient in {dialect}.
"""

system_prompt_dict['sonnet-3-5-20241022v2-0'] = """
You are a data analysis expert and proficient in {dialect}.
"""

class SystemPromptMapper:
    def __init__(self):
        self.variable_map = system_prompt_dict

    def get_variable(self, name):
        return self.variable_map.get(name)


class UserPromptMapper:
    def __init__(self):
        self.variable_map = user_prompt_dict

    def get_variable(self, name):
        return self.variable_map.get(name)


def generate_create_table_ddl(table_description):
    lines = table_description.strip().split('\n')
    table_name = lines[0].split(':')[0].strip()
    table_comment = lines[0].split(':')[1].strip()

    create_table_stmt = f"CREATE TABLE {table_name} (\n"

    i = 1
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('- name:'):
            column_name = line.split(':')[1].strip()
            datatype = lines[i + 1].split(':')[1].strip()
            column_comment = lines[i + 2].split(':')[1].strip() if (i + 2) < len(lines) and ':' in lines[i + 2] else ''
            annotation = ':'.join(lines[i + 3].split(':')[1:]).strip() if (i + 3) < len(lines) and ':' in lines[
                i + 3] else ''

            create_table_stmt += f"  {column_name} {datatype} COMMENT '{column_comment}',\n"
            if annotation:
                create_table_stmt += f"  -- annotation: {annotation}\n"

            i += 4
        else:
            i += 1

    create_table_stmt = create_table_stmt.rstrip(',\n') + "\n);"
    create_table_stmt = f"-- {table_comment}\n{create_table_stmt}"

    return create_table_stmt


system_prompt_mapper = SystemPromptMapper()
user_prompt_mapper = UserPromptMapper()
table_prompt_mapper = table_prompt.TablePromptMapper()
guidance_prompt_mapper = guidance_prompt.GuidancePromptMapper()


def generate_llm_prompt(ddl, hints, prompt_map, search_box, sql_examples=None, ner_example=None, model_id=None,
                        dialect='mysql', environment_dict=None):
    if environment_dict is None:
        environment_dict = defaultdict(str)
    else:
        environment_dict = copy.deepcopy(environment_dict)
    prompt_environment_replace = defaultdict(str)
    for key in environment_dict:
        if key.startswith("{") and key.endswith("}"):
            replace_key = key[1:-1]
            prompt_environment_replace[replace_key] = environment_dict[key]
        else:
            prompt_environment_replace[key] = environment_dict[key]
    environment_dict = prompt_environment_replace
    long_string = ""
    for table_name, table_data in ddl.items():
        ddl_string = table_data["col_a"] if 'col_a' in table_data else table_data["ddl"]
        long_string += "{}: {}\n".format(table_name, table_data["tbl_a"] if 'tbl_a' in table_data else table_data[
            "description"])
        long_string += ddl_string
        long_string += "\n \n"

    # trying CREATE TABLE ddl
    # long_string = generate_create_table_ddl(long_string)
    ddl = long_string

    logger.info(f'{dialect=}')
    if dialect == 'postgresql':
        dialect_prompt = POSTGRES_DIALECT_PROMPT_CLAUDE3
    elif dialect == 'mysql':
        dialect_prompt = MYSQL_DIALECT_PROMPT_CLAUDE3
    elif dialect == 'redshift':
        dialect_prompt = AWS_REDSHIFT_DIALECT_PROMPT_CLAUDE3
    elif dialect == 'starrocks':
        dialect_prompt = STARROCKS_DIALECT_PROMPT_CLAUDE3
    elif dialect == 'clickhouse':
        dialect_prompt = CLICKHOUSE_DIALECT_PROMPT_CLAUDE3
    elif dialect == 'hive':
        dialect_prompt = HIVE_DIALECT_PROMPT_CLAUDE3
    elif dialect == 'bigquery':
        dialect_prompt = BIGQUERY_DIALECT_PROMPT_CLAUDE3
    elif dialect == 'sqlserver':
        dialect_prompt = SQLSERVER_DIALECT_PROMPT_CLAUDE3
    else:
        dialect_prompt = DEFAULT_DIALECT_PROMPT

    example_sql_prompt = ""
    example_ner_prompt = ""
    if sql_examples:
        for item in sql_examples:
            example_sql_prompt += "Q: " + item['_source']['text'] + "\n"
            example_sql_prompt += "A: ```sql\n" + item['_source']['sql'] + "```\n"

    if ner_example:
        for item in ner_example:
            example_ner_prompt += "ner: " + item['_source']['entity'] + "\n"
            example_ner_prompt += "ner info:" + item['_source']['comment'] + "\n"

    name = support_model_ids_map.get(model_id, model_id)
    if name.startswith("sagemaker."):
        name = name[10:]
    elif name.startswith("bedrock-api."):
        name = name[12:]
    elif name.startswith("brclient-api."):
        name = name[13:]
    elif name.startswith("bedrock-anthropic."):
        name = name[18:]
    elif name.startswith("bedrock-api-model."):
        name = name[18:]
    system_prompt = prompt_map.get('text2sql', {}).get('system_prompt', {}).get(name)
    user_prompt = prompt_map.get('text2sql', {}).get('user_prompt', {}).get(name)
    if long_string == '':
        table_prompt = table_prompt_mapper.get_variable(name)
    else:
        table_prompt = long_string
    guidance_prompt = guidance_prompt_mapper.get_variable(name)

    environment_dict["dialect_prompt"] = dialect_prompt
    environment_dict["sql_schema"] = table_prompt
    environment_dict["sql_guidance"] = guidance_prompt
    environment_dict["examples"] = example_sql_prompt
    environment_dict["ner_info"] = example_ner_prompt
    environment_dict["question"] = search_box


    if dialect == "redshift":
        environment_dict["dialect"] = "Amazon Redshift"
        system_prompt = system_prompt.format_map(environment_dict)
    else:
        environment_dict["dialect"] = dialect
        system_prompt = system_prompt.format_map(environment_dict)

    user_prompt = user_prompt.format_map(environment_dict)

    # user_prompt = user_prompt.format(dialect_prompt=dialect_prompt, sql_schema=table_prompt,
    #                                  sql_guidance=guidance_prompt, examples=example_sql_prompt,
    #                                  ner_info=example_ner_prompt, question=search_box)

    return user_prompt, system_prompt

def generate_agent_cot_system_prompt(ddl, prompt_map, search_box, model_id, agent_cot_example=None, environment_dict=None):
    if environment_dict is None:
        environment_dict = defaultdict(str)
    else:
        environment_dict = copy.deepcopy(environment_dict)
    prompt_environment_replace = defaultdict(str)
    for key in environment_dict:
        if key.startswith("{") and key.endswith("}"):
            replace_key = key[1:-1]
            prompt_environment_replace[replace_key] = environment_dict[key]
        else:
            prompt_environment_replace[key] = environment_dict[key]
    environment_dict = prompt_environment_replace
    long_string = ""
    for table_name, table_data in ddl.items():
        ddl_string = table_data["col_a"] if 'col_a' in table_data else table_data["ddl"]
        long_string += "{}: {}\n".format(table_name, table_data["tbl_a"] if 'tbl_a' in table_data else table_data[
            "description"])
        long_string += ddl_string
        long_string += "\n"

    # trying CREATE TABLE ddl
    # long_string = generate_create_table_ddl(long_string)
    ddl = long_string

    agent_cot_example_str = ""
    if agent_cot_example:
        for item in agent_cot_example:
            agent_cot_example_str += "query: " + item['_source']['query'] + "\n"
            agent_cot_example_str += "train of thought:" + item['_source']['comment'] + "\n"

    # fetch system/user prompt from DynamoDB prompt map
    name = support_model_ids_map.get(model_id, model_id)
    if name.startswith("sagemaker."):
        name = name[10:]
    elif name.startswith("bedrock-api."):
        name = name[12:]
    elif name.startswith("brclient-api."):
        name = name[13:]
    elif name.startswith("bedrock-anthropic."):
        name = name[18:]
    elif name.startswith("bedrock-api-model."):
        name = name[18:]

    system_prompt = prompt_map.get('agent', {}).get('system_prompt', {}).get(name)
    user_prompt = prompt_map.get('agent', {}).get('user_prompt', {}).get(name)

    environment_dict["table_schema_data"] = ddl
    environment_dict["sql_guidance"] = ""
    environment_dict["question"] = search_box

    # reformat prompts
    if agent_cot_example_str != "":
        environment_dict["example_data"] = agent_cot_example_str
        system_prompt = system_prompt.format_map(environment_dict)
        # system_prompt = system_prompt.format(table_schema_data=ddl, sql_guidance="",
        #                                      example_data=agent_cot_example_str)
    else:
        environment_dict["example_data"] = AGENT_COT_EXAMPLE
        system_prompt = system_prompt.format_map(environment_dict)
        # system_prompt = system_prompt.format(table_schema_data=ddl, sql_guidance="",
        #                                      example_data=AGENT_COT_EXAMPLE)

    user_prompt = user_prompt.format_map(environment_dict)
    user_prompt = user_prompt.format(question=search_box)

    return user_prompt, system_prompt


# def generate_intent_prompt(prompt_map, search_box, model_id, environment_dict=None):
#     if environment_dict is None:
#         environment_dict = defaultdict(str)
#     else:
#         environment_dict = copy.deepcopy(environment_dict)
#     prompt_environment_replace = defaultdict(str)
#     for key in environment_dict:
#         if key.startswith("{") and key.endswith("}"):
#             replace_key = key[1:-1]
#             prompt_environment_replace[replace_key] = environment_dict[key]
#         else:
#             prompt_environment_replace[key] = environment_dict[key]
#     environment_dict = prompt_environment_replace
#     name = support_model_ids_map.get(model_id, model_id)
#     if name.startswith("sagemaker."):
#         name = name[10:]
#     elif name.startswith("bedrock-api."):
#         name = name[12:]
#     elif name.startswith("brclient-api."):
#         name = name[13:]
#     elif name.startswith("bedrock-anthropic."):
#         name = name[18:]
#     elif name.startswith("bedrock-model."):
#         name = name[18:]

#     system_prompt = prompt_map.get('intent', {}).get('system_prompt', {}).get(name)
#     user_prompt = prompt_map.get('intent', {}).get('user_prompt', {}).get(name)

#     environment_dict["question"] = search_box
#     user_prompt = user_prompt.format_map(environment_dict)
#     # user_prompt = user_prompt.format(question=search_box)
#     return user_prompt, system_prompt

def generate_intent_prompt(prompt_map, search_box, model_id, environment_dict=None):
    if environment_dict is None:
        environment_dict = defaultdict(str)
    else:
        environment_dict = copy.deepcopy(environment_dict)
    prompt_environment_replace = defaultdict(str)
    for key in environment_dict:
        if key.startswith("{") and key.endswith("}"):
            replace_key = key[1:-1]
            prompt_environment_replace[replace_key] = environment_dict[key]
        else:
            prompt_environment_replace[key] = environment_dict[key]
    environment_dict = prompt_environment_replace
    name = support_model_ids_map.get(model_id, model_id)
    if name.startswith("sagemaker."):
        name = name[10:]
    elif name.startswith("bedrock-api."):
        name = name[12:]
    elif name.startswith("brclient-api."):
        name = name[13:]
    elif name.startswith("bedrock-anthropic."):
        name = name[18:]
    elif name.startswith("bedrock-model."):
        name = name[14:]

    # 获取提示模板
    system_prompt = prompt_map.get('intent', {}).get('system_prompt', {}).get(name)
    user_prompt = prompt_map.get('intent', {}).get('user_prompt', {}).get(name)
    
    # 添加检查，确保提示不为None
    if system_prompt is None:
        logger.warning(f"No system prompt found for model {model_id} (name: {name}), using default")
        system_prompt = "You are an intent classifier. Classify the intent of the query."
        
    if user_prompt is None:
        logger.warning(f"No user prompt found for model {model_id} (name: {name}), using default")
        user_prompt = "Classify the intent of this query: {question}"
    
    # 设置环境变量
    environment_dict["question"] = search_box
    
    # 使用format_map格式化提示（添加try-except以防万一）
    try:
        user_prompt = user_prompt.format_map(environment_dict)
    except Exception as e:
        logger.error(f"Error formatting user_prompt: {e}")
        user_prompt = f"Classify the intent of this query: {search_box}"
    
    return user_prompt, system_prompt

def generate_query_rewrite_prompt(prompt_map, search_box, model_id, history_query, environment_dict=None):
    if environment_dict is None:
        environment_dict = defaultdict(str)
    else:
        environment_dict = copy.deepcopy(environment_dict)
    prompt_environment_replace = defaultdict(str)
    for key in environment_dict:
        if key.startswith("{") and key.endswith("}"):
            replace_key = key[1:-1]
            prompt_environment_replace[replace_key] = environment_dict[key]
        else:
            prompt_environment_replace[key] = environment_dict[key]
    environment_dict = prompt_environment_replace
    name = support_model_ids_map.get(model_id, model_id)
    if name.startswith("sagemaker."):
        name = name[10:]
    elif name.startswith("bedrock-api."):
        name = name[12:]
    elif name.startswith("brclient-api."):
        name = name[13:]
    elif name.startswith("bedrock-anthropic."):
        name = name[18:]
    elif name.startswith("bedrock-model."):
        name = name[14:]

    system_prompt = prompt_map.get('query_rewrite', {}).get('system_prompt', {}).get(name)
    user_prompt = prompt_map.get('query_rewrite', {}).get('user_prompt', {}).get(name)

    environment_dict["chat_history"] = history_query
    environment_dict["question"] = search_box

    user_prompt = user_prompt.format_map(environment_dict)

    # user_prompt = user_prompt.format(chat_history=history_query, question=search_box)
    return user_prompt, system_prompt


def generate_knowledge_prompt(prompt_map, search_box, model_id, environment_dict=None):
    if environment_dict is None:
        environment_dict = defaultdict(str)
    else:
        environment_dict = copy.deepcopy(environment_dict)
    prompt_environment_replace = defaultdict(str)
    for key in environment_dict:
        if key.startswith("{") and key.endswith("}"):
            replace_key = key[1:-1]
            prompt_environment_replace[replace_key] = environment_dict[key]
        else:
            prompt_environment_replace[key] = environment_dict[key]
    environment_dict = prompt_environment_replace
    name = support_model_ids_map.get(model_id, model_id)
    if name.startswith("sagemaker."):
        name = name[10:]
    elif name.startswith("bedrock-api."):
        name = name[12:]
    elif name.startswith("brclient-api."):
        name = name[13:]
    elif name.startswith("bedrock-anthropic."):
        name = name[18:]
    elif name.startswith("bedrock-api-model."):
        name = name[18:]

    system_prompt = prompt_map.get('knowledge', {}).get('system_prompt', {}).get(name)
    user_prompt = prompt_map.get('knowledge', {}).get('user_prompt', {}).get(name)

    environment_dict["question"] = search_box

    user_prompt = user_prompt.format_map(environment_dict)
    # user_prompt = user_prompt.format(question=search_box)
    return user_prompt, system_prompt


def generate_data_visualization_prompt(prompt_map, search_box, search_data, model_id, environment_dict=None):
    if environment_dict is None:
        environment_dict = defaultdict(str)
    else:
        environment_dict = copy.deepcopy(environment_dict)
    prompt_environment_replace = defaultdict(str)
    for key in environment_dict:
        if key.startswith("{") and key.endswith("}"):
            replace_key = key[1:-1]
            prompt_environment_replace[replace_key] = environment_dict[key]
        else:
            prompt_environment_replace[key] = environment_dict[key]
    environment_dict = prompt_environment_replace
    name = support_model_ids_map.get(model_id, model_id)
    if name.startswith("sagemaker."):
        name = name[10:]
    elif name.startswith("bedrock-api."):
        name = name[12:]
    elif name.startswith("brclient-api."):
        name = name[13:]
    elif name.startswith("bedrock-anthropic."):
        name = name[18:]
    elif name.startswith("bedrock-api-model."):
        name = name[18:]

    system_prompt = prompt_map.get('data_visualization', {}).get('system_prompt', {}).get(name)
    user_prompt = prompt_map.get('data_visualization', {}).get('user_prompt', {}).get(name)

    environment_dict["question"] = search_box
    environment_dict["data"] = search_data
    user_prompt = user_prompt.format_map(environment_dict)

    # user_prompt = user_prompt.format(question=search_box, data=search_data)

    return user_prompt, system_prompt


def generate_agent_analyse_prompt(prompt_map, search_box, model_id, sql_data, environment_dict=None):
    if environment_dict is None:
        environment_dict = defaultdict(str)
    else:
        environment_dict = copy.deepcopy(environment_dict)
    prompt_environment_replace = defaultdict(str)
    for key in environment_dict:
        if key.startswith("{") and key.endswith("}"):
            replace_key = key[1:-1]
            prompt_environment_replace[replace_key] = environment_dict[key]
        else:
            prompt_environment_replace[key] = environment_dict[key]
    environment_dict = prompt_environment_replace
    name = support_model_ids_map.get(model_id, model_id)
    if name.startswith("sagemaker."):
        name = name[10:]
    elif name.startswith("bedrock-api."):
        name = name[12:]
    elif name.startswith("brclient-api."):
        name = name[13:]
    elif name.startswith("bedrock-anthropic."):
        name = name[18:]
    elif name.startswith("bedrock-api-model."):
        name = name[18:]

    system_prompt = prompt_map.get('agent_analyse', {}).get('system_prompt', {}).get(name)
    user_prompt = prompt_map.get('agent_analyse', {}).get('user_prompt', {}).get(name)

    environment_dict["question"] = search_box
    environment_dict["data"] = sql_data

    user_prompt = user_prompt.format_map(environment_dict)
    # user_prompt = user_prompt.format(question=search_box, data=sql_data)

    return user_prompt, system_prompt


def generate_data_summary_prompt(prompt_map, search_box, model_id, sql_data, environment_dict=None):
    if environment_dict is None:
        environment_dict = defaultdict(str)
    else:
        environment_dict = copy.deepcopy(environment_dict)
    prompt_environment_replace = defaultdict(str)
    for key in environment_dict:
        if key.startswith("{") and key.endswith("}"):
            replace_key = key[1:-1]
            prompt_environment_replace[replace_key] = environment_dict[key]
        else:
            prompt_environment_replace[key] = environment_dict[key]
    environment_dict = prompt_environment_replace
    name = support_model_ids_map.get(model_id, model_id)
    if name.startswith("sagemaker."):
        name = name[10:]
    elif name.startswith("bedrock-api."):
        name = name[12:]
    elif name.startswith("brclient-api."):
        name = name[13:]
    elif name.startswith("bedrock-anthropic."):
        name = name[18:]
    elif name.startswith("bedrock-api-model."):
        name = name[18:]

    system_prompt = prompt_map.get('data_summary', {}).get('system_prompt', {}).get(name)
    user_prompt = prompt_map.get('data_summary', {}).get('user_prompt', {}).get(name)

    environment_dict["question"] = search_box
    environment_dict["data"] = sql_data
    user_prompt = user_prompt.format_map(environment_dict)
    # user_prompt = user_prompt.format(question=search_box, data=sql_data)

    return user_prompt, system_prompt


def generate_suggest_question_prompt(prompt_map, search_box, model_id, environment_dict=None):
    if environment_dict is None:
        environment_dict = defaultdict(str)
    else:
        environment_dict = copy.deepcopy(environment_dict)
    prompt_environment_replace = defaultdict(str)
    for key in environment_dict:
        if key.startswith("{") and key.endswith("}"):
            replace_key = key[1:-1]
            prompt_environment_replace[replace_key] = environment_dict[key]
        else:
            prompt_environment_replace[key] = environment_dict[key]
    environment_dict = prompt_environment_replace
    name = support_model_ids_map.get(model_id, model_id)
    if name.startswith("sagemaker."):
        name = name[10:]
    elif name.startswith("bedrock-api."):
        name = name[12:]
    elif name.startswith("brclient-api."):
        name = name[13:]
    elif name.startswith("bedrock-anthropic."):
        name = name[18:]
    elif name.startswith("bedrock-api-model."):
        name = name[18:]

    system_prompt = prompt_map.get('suggestion', {}).get('system_prompt', {}).get(name)
    user_prompt = prompt_map.get('suggestion', {}).get('user_prompt', {}).get(name)

    environment_dict["question"] = search_box
    user_prompt = user_prompt.format_map(environment_dict)
    # user_prompt = user_prompt.format(question=search_box)

    return user_prompt, system_prompt
