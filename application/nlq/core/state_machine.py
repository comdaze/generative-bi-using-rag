import json
import string
import functools
import pandas as pd

from api.schemas import Answer, KnowledgeSearchResult, SQLSearchResult, AgentSearchResult, AskReplayResult, \
    AskEntitySelect, ChartEntity, TaskSQLSearchResult
from nlq.business.datasource.factory import DataSourceFactory
from nlq.business.log_store import LogManagement
from nlq.core.chat_context import ProcessingContext
from nlq.core.state import QueryState
from utils.apis import get_sql_result_tool
from utils.llm import get_query_intent, get_query_rewrite, knowledge_search, text_to_sql, data_analyse_tool, \
    generate_suggested_question, get_agent_cot_task, data_visualization
from utils.logging import getLogger
from utils.opensearch import get_retrieve_opensearch
from utils.text_search import entity_retrieve_search, qa_retrieve_search, agent_text_search, agent_text_search_websocket
from utils.tool import get_generated_sql, get_generated_sql_explain, change_class_to_str, get_current_time

logger = getLogger()


def log_execution(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        state_name = self.get_state().name if self.get_state() else "Unknown State"
        logger.info(f"Executing {func.__name__} in state {state_name}")
        return func(self, *args, **kwargs)

    return wrapper


class QueryStateMachine:
    def __init__(self, context: ProcessingContext):
        self.state = self.get_state_from_name("INITIAL")
        self.previous_state = self.get_state_from_name(context.previous_state)
        self.context = context
        self.answer = Answer(
            query="",
            query_rewrite="",
            query_intent="",
            knowledge_search_result=KnowledgeSearchResult(
                knowledge_response=""
            ),
            sql_search_result=SQLSearchResult(
                sql="",
                sql_data=[],
                data_show_type="table",
                sql_gen_process="",
                data_analyse="",
                sql_data_chart=[]
            ),
            agent_search_result=AgentSearchResult(
                agent_sql_search_result=[],
                agent_summary=""
            ),
            ask_rewrite_result=AskReplayResult(
                query_rewrite=""
            ),
            suggested_question=[],
            ask_entity_select=AskEntitySelect(
                entity_select_info={},
                entity_retrieval=[]
            ),
            error_log={}
        )

        self.search_intent_flag = False
        self.reject_intent_flag = False
        self.agent_intent_flag = False
        self.knowledge_search_flag = False

        self.intent_search_result = {}
        self.intent_response = {}
        self.entity_slot = []
        self.normal_search_entity_slot = []
        self.normal_search_qa_retrival = []
        self.agent_cot_retrieve = []
        self.agent_task_split = {}
        self.agent_search_result = []
        self.agent_data_analyse_result = ""
        self.agent_valid_data = []
        self.use_auto_correction_flag = False
        self.first_sql_execute_info = {}
        self.token_info = {}

    def transition(self, new_state):
        self.state = new_state

    def get_answer(self):
        return self.answer

    def get_state(self):
        return self.state

    def get_state_from_name(self, state_name):
        if state_name == QueryState.INITIAL.name:
            return QueryState.INITIAL
        elif state_name == QueryState.USER_SELECT_ENTITY.name:
            return QueryState.USER_SELECT_ENTITY

    def run(self):
        if self.previous_state == QueryState.USER_SELECT_ENTITY:
            self.transition(QueryState.USER_SELECT_ENTITY)

        while self.state != QueryState.COMPLETE and self.state != QueryState.ERROR:
            if self.state == QueryState.INITIAL:
                self.handle_initial()
            elif self.get_state() == QueryState.REJECT_INTENT:
                self.handle_reject_intent()
            elif self.get_state() == QueryState.KNOWLEDGE_SEARCH:
                self.handle_knowledge_search()
            elif self.state == QueryState.ENTITY_RETRIEVAL:
                self.handle_entity_retrieval()
            elif self.state == QueryState.QA_RETRIEVAL:
                self.handle_qa_retrieval()
            elif self.state == QueryState.SQL_GENERATION:
                self.handle_sql_generation()
            elif self.state == QueryState.INTENT_RECOGNITION:
                self.handle_intent_recognition()
            elif self.state == QueryState.EXECUTE_QUERY:
                self.handle_execute_query()
            elif self.state == QueryState.ANALYZE_DATA:
                self.handle_analyze_data()
            elif self.state == QueryState.ASK_ENTITY_SELECT:
                self.handle_entity_selection()
            elif self.state == QueryState.AGENT_TASK:
                self.handle_agent_task()
            elif self.state == QueryState.AGENT_SEARCH:
                self.handle_agent_sql_generation()
            elif self.state == QueryState.AGENT_DATA_SUMMARY:
                self.handle_agent_analyze_data()
            elif self.state == QueryState.USER_SELECT_ENTITY:
                self.handle_user_select_entity()
            else:
                self.state = QueryState.ERROR

        if self.state == QueryState.COMPLETE:
            self.handle_data_visualization()
        if self.context.gen_suggested_question_flag:
            self.handle_suggest_question()

    @log_execution
    def handle_initial(self):
        try:
            self.answer.query = self.context.search_box
            self.answer.query_rewrite = self.context.search_box
            self.answer.query_intent = "normal_search"
            if self.context.context_window > 0:
                self._handle_query_rewrite()
            else:
                self.context.query_rewrite = self.context.search_box
                self.transition(QueryState.INTENT_RECOGNITION)
        except Exception as e:
            self.answer.error_log[QueryState.INITIAL.name] = str(e)
            logger.error(f"The context is {self.context.search_box}, handle_initial encountered an error: {e}")
            self.transition(QueryState.ERROR)

    def _handle_query_rewrite(self):
        try:
            query_rewrite_result, model_response = get_query_rewrite(self.context.model_type, self.context.search_box,
                                                                     self.context.database_profile['prompt_map'],
                                                                     self.context.user_query_history,
                                                                     self.context.database_profile['prompt_environment'])
            self.token_info[QueryState.QUERY_REWRITE.name] = model_response.token_info
            query_rewrite_intent = query_rewrite_result.get("intent")
            self.context.query_rewrite = query_rewrite_result.get("query")
            if query_rewrite_intent == "ask_in_reply":
                self._set_ask_in_reply_result()
            else:
                self.answer.query_rewrite = query_rewrite_result.get("query")
                self.answer.query = self.context.search_box
                self.transition(QueryState.INTENT_RECOGNITION)
        except Exception as e:
            self.answer.error_log[QueryState.QUERY_REWRITE.name] = str(e)
            logger.error(f"The context is {self.context.search_box}, handle_initial encountered an error: {e}")
            self.transition(QueryState.ERROR)

    def _set_ask_in_reply_result(self):
        self.answer.query = self.context.search_box
        self.answer.query_intent = "ask_in_reply"
        self.answer.query_rewrite = self.context.query_rewrite

        self.answer.ask_rewrite_result.query_rewrite = self.context.query_rewrite
        self.transition(QueryState.COMPLETE)

    def handle_entity_retrieval(self):
        try:
            self.normal_search_entity_slot = self._perform_entity_retrieval()
            entity_retrieve = []
            same_name_entity = {}
            for each_entity in self.normal_search_entity_slot:
                each_item_dict = {}
                each_item_dict["_score"] = each_entity["_score"]
                each_item_dict["_source"] = each_entity["_source"]
                if "vector_field" in each_item_dict["_source"]:
                    del each_item_dict["_source"]["vector_field"]
                if each_entity['_score'] > 0.8:
                    entity_retrieve.append(each_item_dict)
                if each_entity['_source']['entity_count'] > 1 and each_entity['_score'] > 0.98:
                    same_name_entity[each_entity['_source']['entity']] = each_entity['_source']['entity_table_info']
            # 保存实体信息到answer对象中
            self.answer.ask_entity_select.entity_retrieval = entity_retrieve
        
            # 如果是knowledge_search意图，直接转向KNOWLEDGE_SEARCH状态
            if self.answer.query_intent == "knowledge_search":
                self.transition(QueryState.KNOWLEDGE_SEARCH)
                return
                               
            if len(same_name_entity) > 0 and self.answer.query_intent == "normal_search":
                for key, value in same_name_entity.items():
                    change_value = []
                    for each_value in value:
                        new_each_value = each_value
                        new_each_value["id"] = new_each_value["table_name"] + "#" + new_each_value[
                            "column_name"] + "#" + new_each_value["value"]
                        new_each_value["text"] = "实体名称：" + key + ", 数据表：" + each_value[
                            "table_name"] + "，" + "列名是：" + each_value[
                                                     "column_name"] + "，" + "查询值是：" + each_value["value"] + "\n"
                        change_value.append(new_each_value)
                    same_name_entity[key] = change_value

                self.answer.ask_entity_select.entity_select_info = same_name_entity
                self.answer.ask_entity_select.entity_retrieval = entity_retrieve
                self.transition(QueryState.ASK_ENTITY_SELECT)
            else:
                self.transition(QueryState.QA_RETRIEVAL)
        except Exception as e:
            self.answer.error_log[QueryState.ENTITY_RETRIEVAL.name] = str(e)
            logger.error(f"The context is {self.context.search_box}, handle_entity_retrieval encountered an error: {e}")
            self.transition(QueryState.ERROR)

    def _perform_entity_retrieval(self):
        if self.context.use_rag_flag:
            return entity_retrieve_search(self.entity_slot, self.context.opensearch_info, self.context.selected_profile)
        else:
            return []

    @log_execution
    def handle_qa_retrieval(self):
        try:
            self.normal_search_qa_retrival = self._perform_qa_retrieval()
            self.transition(QueryState.SQL_GENERATION)
        except Exception as e:
            self.answer.error_log[QueryState.QA_RETRIEVAL.name] = str(e)
            logger.error(f"The context is {self.context.search_box}, handle_qa_retrieval encountered an error: {e}")
            self.transition(QueryState.ERROR)

    def _perform_qa_retrieval(self):
        if self.context.use_rag_flag:
            return qa_retrieve_search(self.context.query_rewrite, self.context.opensearch_info,
                                      self.context.selected_profile)
        return []

    @log_execution
    def handle_sql_generation(self):
        sql, response, original_sql = self._generate_sql()
        self.intent_search_result["sql"] = sql
        self.intent_search_result["response"] = response
        self.intent_search_result["original_sql"] = original_sql
        self.answer.sql_search_result.sql = sql.strip()
        self.answer.sql_search_result.sql_gen_process = get_generated_sql_explain(response).strip()
        if self.context.visualize_results_flag:
            self.transition(QueryState.EXECUTE_QUERY)
        else:
            self.transition(QueryState.COMPLETE)

    def _apply_row_level_security_for_sql(self, sql):
        post_sql = DataSourceFactory.apply_row_level_security_for_sql(
            self.context.database_profile['db_type'],
            sql,
            self.context.database_profile['row_level_security_config'],
            self.context.username
        )
        return post_sql

    def _generate_sql(self):
        try:
            response, model_response = text_to_sql(self.context.database_profile['tables_info'],
                                                   self.context.database_profile['hints'],
                                                   self.context.database_profile['prompt_map'],
                                                   self.context.query_rewrite,
                                                   model_id=self.context.model_type,
                                                   sql_examples=self.normal_search_qa_retrival,
                                                   ner_example=self.normal_search_entity_slot,
                                                   dialect=self.context.database_profile['db_type'],
                                                   environment_dict=self.context.database_profile['prompt_environment'])
            self.token_info[QueryState.SQL_GENERATION.name] = model_response.token_info
            sql = get_generated_sql(response)
            # post-processing the sql
            post_sql = self._apply_row_level_security_for_sql(sql)
            return post_sql, response, sql
        except Exception as e:
            self.answer.error_log[QueryState.SQL_GENERATION.name] = str(e)
            logger.error(f"The context is {self.context.search_box}, _generate_sql encountered an error: {e}")
            return "", "", ""

    def _generate_sql_again(self):
        try:
            response, model_response = text_to_sql(self.context.database_profile['tables_info'],
                                                   self.context.database_profile['hints'],
                                                   self.context.database_profile['prompt_map'],
                                                   self.context.query_rewrite,
                                                   model_id=self.context.model_type,
                                                   sql_examples=self.normal_search_qa_retrival,
                                                   ner_example=self.normal_search_entity_slot,
                                                   dialect=self.context.database_profile['db_type'],
                                                   model_provider=None,
                                                   additional_info='''\n NOTE: when I try to write a SQL <sql>{sql_statement}</sql>, I got an error <error>{error}</error>. Please consider and avoid this problem. '''.format(
                                                       sql_statement=self.intent_search_result["original_sql"],
                                                       error=self.intent_search_result["sql_execute_result"][
                                                           "error_info"]))
            self.token_info[QueryState.SQL_GENERATION.name + "_AGAIN"] = model_response.token_info
            sql = get_generated_sql(response)
            post_sql = self._apply_row_level_security_for_sql(sql)
            self.delete_error_log_entry(QueryState.SQL_GENERATION.name)
            return post_sql, response, sql
        except Exception as e:
            self.answer.error_log[QueryState.SQL_GENERATION.name] = str(e)
            logger.error(f"The context is {self.context.search_box}, _generate_sql encountered an error: {e}")
            return "", "", ""

    @log_execution
    def handle_agent_sql_generation(self):
        agent_search_result, token_info = agent_text_search(self.context.query_rewrite, self.context.model_type,
                                                            self.context.database_profile,
                                                            self.entity_slot, self.context.opensearch_info,
                                                            self.context.selected_profile, self.context.use_rag_flag,
                                                            self.agent_task_split)
        self.token_info[QueryState.SQL_GENERATION.name + "AGENT"] = token_info
        self.agent_search_result = agent_search_result
        self.transition(QueryState.AGENT_DATA_SUMMARY)

    async def handle_agent_sql_generation_websocket(self, websocket, session_id, user_id):
        state_name = self.get_state().name if self.get_state() else "Unknown State"
        logger.info(f"Executing handle_agent_sql_generation_websocket in state {state_name}")
        agent_search_result, token_info = await agent_text_search_websocket(websocket, session_id, user_id, self.context.query_rewrite, self.context.model_type,
                                                            self.context.database_profile,
                                                            self.entity_slot, self.context.opensearch_info,
                                                            self.context.selected_profile, self.context.use_rag_flag,
                                                            self.agent_task_split)
        self.token_info[QueryState.SQL_GENERATION.name + "AGENT"] = token_info
        self.agent_search_result = agent_search_result
        self.transition(QueryState.AGENT_DATA_SUMMARY)

    @log_execution
    def handle_intent_recognition(self):
        try:
            if self.context.intent_ner_recognition_flag:
                intent_response, model_response = get_query_intent(self.context.model_type, self.context.query_rewrite,
                                                                   self.context.database_profile['prompt_map'],
                                                                   self.context.database_profile['prompt_environment'])
                self.token_info[QueryState.INTENT_RECOGNITION.name] = model_response.token_info
                self.intent_response = intent_response
                self._process_intent_response(intent_response)
            else:
                self.search_intent_flag = True
            self._transition_based_on_intent()
        except Exception as e:
            self.answer.error_log[QueryState.INTENT_RECOGNITION.name] = str(e)
            logger.error(
                f"The context is {self.context.search_box}, handle_intent_recognition encountered an error: {e}")
            self.transition(QueryState.ERROR)

    def _process_intent_response(self, intent_response):
        intent = intent_response.get("intent", "normal_search")
        self.entity_slot = intent_response.get("slot", [])
        if intent == "reject_search":
            self.reject_intent_flag = True
            self.search_intent_flag = False
        elif intent == "agent_search":
            self.agent_intent_flag = True
            if self.context.agent_cot_flag:
                self.search_intent_flag = False
            else:
                self.search_intent_flag = True
                self.agent_intent_flag = False
        elif intent == "knowledge_search":
            self.knowledge_search_flag = True
            self.search_intent_flag = False
            self.agent_intent_flag = False
        else:
            self.search_intent_flag = True

    def _transition_based_on_intent(self):
        if self.reject_intent_flag:
            self.answer.query_intent = "reject_search"
            self.transition(QueryState.REJECT_INTENT)
        elif self.knowledge_search_flag:
            #self.transition(QueryState.KNOWLEDGE_SEARCH)
            self.answer.query_intent = "knowledge_search"
            # 先进入实体检索状态
            self.transition(QueryState.ENTITY_RETRIEVAL)
        elif self.agent_intent_flag:
            self.answer.query_intent = "agent_search"
            self.transition(QueryState.AGENT_TASK)
        else:
            self.answer.query_intent = "normal_search"
            self.transition(QueryState.ENTITY_RETRIEVAL)

    @log_execution
    def handle_reject_intent(self):
        self.answer.query = self.context.search_box
        self.answer.query_rewrite = self.context.query_rewrite
        self.answer.query_intent = "reject_search"
        self.transition(QueryState.COMPLETE)

    @log_execution
    def handle_knowledge_search(self):
        # 使用已经保存在 answer 对象中的实体信息
        entity_info = self.answer.ask_entity_select.entity_retrieval
        response, model_response = knowledge_search(search_box=self.context.query_rewrite,
                                                    model_id=self.context.model_type,
                                                    prompt_map=self.context.database_profile["prompt_map"],
                                                    environment_dict=self.context.database_profile["prompt_environment"],
                                                    entity_info=entity_info  # 添加实体信息参数
                                                    )
        self.token_info[QueryState.KNOWLEDGE_SEARCH.name] = model_response.token_info
        self.answer.query = self.context.search_box
        self.answer.query_rewrite = self.context.query_rewrite
        self.answer.query_intent = "knowledge_search"
        self.answer.knowledge_search_result.knowledge_response = response
        self.transition(QueryState.COMPLETE)

    @log_execution
    def handle_entity_selection(self):
        # Handle entity selection
        entity_select_format = "根据您的描述，检索到多个相同名称的实体，请选择您想要查询的实体。\n"
        alphabet_list = list(string.ascii_uppercase)
        index = 0
        for entity in self.answer.ask_entity_select.entity_select_info:
            entity_value = self.answer.ask_entity_select.entity_select_info[entity]
            entity_name = entity
            entity_desc = "实体：" + entity_name + "，有如下维度值：\n"
            for each_value in entity_value:
                if index < len(alphabet_list):
                    entity_desc += alphabet_list[index] + " ："
                    entity_desc = entity_desc + "数据表：" + each_value["table_name"] + "，" + "列名是：" + each_value[
                        "column_name"] + "，" + "查询值是：" + each_value["value"] + "\n"
                    index = index + 1
            entity_select_format += entity_desc
        self.answer.query_intent = "entity_select"
        self.transition(QueryState.COMPLETE)

    @log_execution
    def handle_execute_query(self):
        try:
            sql = self.intent_search_result.get("sql", "")
            sql_execute_result = self._execute_sql(sql)
            self.intent_search_result["sql_execute_result"] = sql_execute_result
            self.answer.sql_search_result.sql_data = sql_execute_result["data"]
            if self.context.data_with_analyse and sql_execute_result["status_code"] == 200:
                self.transition(QueryState.ANALYZE_DATA)
            elif sql_execute_result["status_code"] == 200:
                self.transition(QueryState.COMPLETE)
            elif sql_execute_result["status_code"] == 500 and self.context.auto_correction_flag:
                self.use_auto_correction_flag = True
                self.first_sql_execute_info = sql_execute_result
                sql, response, original_sql = self._generate_sql_again()
                sql_execute_result = self._execute_sql(sql)
                self.answer.sql_search_result.sql = sql
                self.answer.sql_search_result.sql_gen_process = get_generated_sql_explain(response)
                self.intent_search_result["sql_execute_result"] = sql_execute_result
                self.answer.sql_search_result.sql_data = sql_execute_result["data"]
                if self.context.data_with_analyse and sql_execute_result["status_code"] == 200:
                    self.transition(QueryState.ANALYZE_DATA)
                elif sql_execute_result["status_code"] == 200:
                    self.transition(QueryState.COMPLETE)
                else:
                    self.answer.error_log[QueryState.EXECUTE_QUERY.name] = sql_execute_result["error_info"]
                    self.transition(QueryState.ERROR)
            else:
                self.answer.error_log[QueryState.EXECUTE_QUERY.name] = sql_execute_result["error_info"]
                self.transition(QueryState.ERROR)
        except Exception as e:
            self.answer.error_log[QueryState.EXECUTE_QUERY.name] = str(e)
            logger.error(f"The context is {self.context.search_box}, handle_execute_query encountered an error: {e}")
            self.transition(QueryState.ERROR)

    def _execute_sql(self, sql):
        if sql == "":
            return {"data": [], "sql": sql, "status_code": 500, "error_info": "The SQL is empty."}
        return get_sql_result_tool(self.context.database_profile, sql)

    @log_execution
    def handle_analyze_data(self):
        # Analyze the data
        try:
            search_intent_analyse_result, model_response = data_analyse_tool(self.context.model_type,
                                                                             self.context.database_profile['prompt_map'],
                                                                             self.context.query_rewrite,
                                                                             self.intent_search_result[
                                                                                 "sql_execute_result"][
                                                                                 "data"].to_json(
                                                                                 orient='records',
                                                                                 force_ascii=False), "query",
                                                                             self.context.database_profile["prompt_environment"])
            self.token_info[QueryState.ANALYZE_DATA.name] = model_response.token_info
            self.answer.sql_search_result.data_analyse = search_intent_analyse_result
            self.transition(QueryState.COMPLETE)
        except Exception as e:
            self.answer.error_log[QueryState.ANALYZE_DATA.name] = str(e)
            logger.error(f"The context is {self.context.search_box}, handle_analyze_data encountered an error: {e}")
            self.transition(QueryState.ERROR)

    @log_execution
    def handle_agent_task(self):
        # Analyze the task
        try:
            self.agent_cot_retrieve = get_retrieve_opensearch(self.context.opensearch_info, self.context.query_rewrite,
                                                              "agent", self.context.selected_profile, 2, 0.5)

            agent_cot_task_result, model_response = get_agent_cot_task(self.context.model_type,
                                                                       self.context.database_profile["prompt_map"],
                                                                       self.context.query_rewrite,
                                                                       self.context.database_profile['tables_info'],
                                                                       self.agent_cot_retrieve,
                                                                       self.context.database_profile["prompt_environment"])
            self.token_info[QueryState.AGENT_TASK.name] = model_response.token_info
            self.agent_task_split = agent_cot_task_result
            self.transition(QueryState.AGENT_SEARCH)
        except Exception as e:
            self.answer.error_log[QueryState.AGENT_TASK.name] = str(e)
            logger.error(f"The context is {self.context.search_box}, handle_agent_task encountered an error: {e}")
            self.transition(QueryState.ERROR)

    @log_execution
    def handle_agent_analyze_data(self):
        # Analyze the data
        try:
            filter_deep_dive_sql_result = []
            agent_sql_search_result = []
            for i in range(len(self.agent_search_result)):
                each_task_res = get_sql_result_tool(
                    self.context.database_profile,
                    self.agent_search_result[i]["sql"])
                # 添加SQL自动纠错逻辑
                if each_task_res["status_code"] == 500 and self.context.auto_correction_flag:
                    logger.info(f"Attempting to correct SQL for agent task {i+1}")
                    # 保存原始SQL和错误信息
                    original_sql = self.agent_search_result[i]["sql"]
                    error_info = each_task_res["error_info"]
                    
                    # 重新生成SQL
                    corrected_sql, corrected_response = self._generate_agent_sql_again(
                        self.agent_search_result[i]["query"], 
                        original_sql, 
                        error_info
                    )
                    
                    if corrected_sql and corrected_sql != "":
                        # 使用修复后的SQL重新执行
                        logger.info(f"Retrying with corrected SQL: {corrected_sql}")
                        self.agent_search_result[i]["sql"] = corrected_sql
                        self.agent_search_result[i]["response"] = corrected_response
                        each_task_res = get_sql_result_tool(
                            self.context.database_profile,
                            corrected_sql
                        )
                if each_task_res["status_code"] == 200 and len(each_task_res["data"]) > 0:
                    self.agent_search_result[i]["data_result"] = each_task_res["data"].to_json(
                        orient='records')
                    filter_deep_dive_sql_result.append(self.agent_search_result[i])

                    show_select_data = [list(each_task_res["data"].columns)] + each_task_res["data"].values.tolist()
                    each_task_sql_response = get_generated_sql_explain(self.agent_search_result[i]["response"])
                    sub_task_sql_result = SQLSearchResult(sql_data=show_select_data,
                                                          sql=self.agent_search_result[i]["sql"],
                                                          data_show_type="table",
                                                          sql_gen_process=each_task_sql_response,
                                                          data_analyse="", sql_data_chart=[])
                    query_value = self.agent_search_result[i]["query"]
                    if isinstance(query_value, list):
                        try:
                            logger.info(f"Converting list to string for sub_task_query: {query_value}")
                            query_value = json.dumps(query_value)  # 将列表转换为JSON字符串
                        except Exception as e:
                            logger.error(f"Error converting list to JSON string: {e}")
                            query_value = str(query_value)  # 回退到简单的字符串转换
                    each_task_sql_search_result = TaskSQLSearchResult(
                        sub_task_query=query_value,
                        sql_search_result=sub_task_sql_result)
                    agent_sql_search_result.append(each_task_sql_search_result)

            # 如果没有成功执行的SQL，添加详细的错误信息但继续流程
            if len(filter_deep_dive_sql_result) == 0:
                error_details = []
                for i in range(len(self.agent_search_result)):
                    task_info = {
                        "query": self.agent_search_result[i]["query"],
                        "sql": self.agent_search_result[i]["sql"]
                    }
                    
                    # 获取错误信息（如果有）
                    task_res = get_sql_result_tool(
                        self.context.database_profile,
                        self.agent_search_result[i]["sql"])
                    if task_res["status_code"] == 500:
                        task_info["error"] = task_res["error_info"]
                    else:
                        task_info["error"] = "Unknown error or no data returned"
                        
                    error_details.append(task_info)
                
                # 记录详细的错误信息
                self.answer.error_log[QueryState.AGENT_DATA_SUMMARY.name] = {
                    "message": "All agent tasks failed to execute SQL successfully.",
                    "details": error_details
                }
                
                # 添加一个标志表示有SQL执行错误
                self.has_sql_errors = True
                
                # 创建一个特殊的错误消息
                self.agent_data_analyse_result = "No data was found for your query. This could be because the SQL queries failed to execute properly or because there is no matching data in the database."
                self.agent_valid_data = []

            # 只有当有成功执行的SQL结果时，才调用data_analyse_tool
            if len(filter_deep_dive_sql_result) > 0:
                agent_data_analyse_result, model_response = data_analyse_tool(self.context.model_type,
                                                                              self.context.database_profile["prompt_map"],
                                                                              self.context.query_rewrite,
                                                                              json.dumps(filter_deep_dive_sql_result,
                                                                                         ensure_ascii=False), "agent",
                                                                              self.context.database_profile["prompt_environment"])
                self.token_info[QueryState.AGENT_DATA_SUMMARY.name] = model_response.token_info
            else:
                # 使用之前设置的错误消息
                agent_data_analyse_result = self.agent_data_analyse_result if hasattr(self, 'agent_data_analyse_result') else "No data available for analysis."
                # 为空结果设置一个空的token_info
                if QueryState.AGENT_DATA_SUMMARY.name not in self.token_info:
                    self.token_info[QueryState.AGENT_DATA_SUMMARY.name] = {"input_tokens": 0, "output_tokens": 0}

            self.agent_valid_data = filter_deep_dive_sql_result
            self.agent_data_analyse_result = agent_data_analyse_result
            self.answer.agent_search_result.agent_summary = agent_data_analyse_result
            self.answer.agent_search_result.agent_sql_search_result = agent_sql_search_result
            self.transition(QueryState.COMPLETE)
        except Exception as e:
            self.answer.error_log[QueryState.AGENT_DATA_SUMMARY.name] = str(e)
            logger.error(
                f"The context is {self.context.search_box}, handle_agent_analyze_data encountered an error: {e}")
            self.transition(QueryState.ERROR)

    @log_execution
    def handle_suggest_question(self):
        # Handle suggest question
        if self.context.gen_suggested_question_flag:
            if self.search_intent_flag or self.agent_intent_flag:
                generated_sq, model_response = generate_suggested_question(self.context.database_profile['prompt_map'],
                                                                           self.context.query_rewrite,
                                                                           model_id=self.context.model_type,
                                                                           environment_dict=self.context.database_profile['prompt_environment'])
                self.token_info["SUGGEST_QUESTION"] = model_response.token_info
                split_strings = generated_sq.split("[generate]")
                gen_sq_list = [s.strip() for s in split_strings if s.strip()]
                self.answer.suggested_question = gen_sq_list

    def delete_error_log_entry(self, key):
        if key in self.answer.error_log:
            del self.answer.error_log[key]

    def handle_data_visualization(self):
        try:
            if self.answer.query_intent == "normal_search":
                model_select_type, show_select_data, select_chart_type, show_chart_data, model_response = data_visualization(
                    self.context.model_type,
                    self.context.query_rewrite,
                    self.get_answer().sql_search_result.sql_data,
                    self.context.database_profile['prompt_map'],
                    self.context.database_profile['prompt_environment'])
                self.token_info[QueryState.DATA_VISUALIZATION.name] = model_response.token_info
                if select_chart_type != "-1":
                    sql_chart_data = ChartEntity(chart_type="", chart_data=[])
                    sql_chart_data.chart_type = select_chart_type
                    sql_chart_data.chart_data = show_chart_data
                    self.get_answer().sql_search_result.sql_data_chart = [sql_chart_data]
                self.get_answer().sql_search_result.data_show_type = model_select_type
                self.get_answer().sql_search_result.sql_data = show_select_data
            elif self.answer.query_intent == "agent_search":
                agent_sql_search_result = self.answer.agent_search_result.agent_sql_search_result
                agent_sql_search_result_with_visualization = []
                for each in agent_sql_search_result:
                    model_select_type, show_select_data, select_chart_type, show_chart_data, model_response = data_visualization(
                        self.context.model_type,
                        each.sub_task_query,
                        each.sql_search_result.sql_data,
                        self.context.database_profile['prompt_map'],
                        self.context.database_profile['prompt_environment'])
                    if QueryState.DATA_VISUALIZATION.name not in self.token_info:
                        self.token_info[QueryState.DATA_VISUALIZATION.name] = model_response.token_info
                    else:
                        if "input_tokens" in model_response.token_info:
                            if "input_tokens" not in self.token_info[QueryState.DATA_VISUALIZATION.name]:
                                self.token_info[QueryState.DATA_VISUALIZATION.name]["input_tokens"] = 0
                            self.token_info[QueryState.DATA_VISUALIZATION.name]["input_tokens"] = self.token_info[
                                                                                                     QueryState.DATA_VISUALIZATION.name][
                                                                                                     "input_tokens"] + \
                                                                                                 model_response.token_info[
                                                                                                     "input_tokens"]
                        if "output_tokens" in model_response.token_info:
                            if "output_tokens" not in self.token_info[QueryState.DATA_VISUALIZATION.name]:
                                self.token_info[QueryState.DATA_VISUALIZATION.name]["output_tokens"] = 0
                            self.token_info[QueryState.DATA_VISUALIZATION.name]["output_tokens"] = self.token_info[
                                                                                                      QueryState.DATA_VISUALIZATION.name][
                                                                                                      "output_tokens"] + \
                                                                                                  model_response.token_info[
                                                                                                      "output_tokens"]
                    if select_chart_type != "-1":
                        sql_chart_data = ChartEntity(chart_type="", chart_data=[])
                        sql_chart_data.chart_type = select_chart_type
                        sql_chart_data.chart_data = show_chart_data
                        each.sql_search_result.sql_data_chart = [sql_chart_data]
                    each.sql_search_result.data_show_type = model_select_type
                    each.sql_search_result.sql_data = show_select_data
                    agent_sql_search_result_with_visualization.append(each)
                self.answer.agent_search_result.agent_sql_search_result = agent_sql_search_result_with_visualization
        except Exception as e:
            self.answer.error_log[QueryState.DATA_VISUALIZATION.name] = str(e)
            logger.error(
                f"The context is {self.context.search_box}, handle_data_visualization encountered an error: {e}")
            self.transition(QueryState.ERROR)

    def handle_user_select_entity(self):
        try:
            self.answer.query = self.context.search_box
            self.answer.query_rewrite = self.context.query_rewrite
            self.answer.query_intent = "normal_search"
            self.search_intent_flag = True
            comment_format = "{entity} is located in table {table_name}, column {column_name}, the dimension value is {value}"
            normal_search_entity_slot = self.context.entity_retrieval
            entity_user_select = self.context.entity_user_select
            entity_retrieval = []
            for each_entity in normal_search_entity_slot:
                entity = each_entity["_source"]["entity"]
                if entity in entity_user_select:
                    each_entity["_source"]["entity_table_info"] = [entity_user_select[entity]]
                    each_entity["_source"]["comment"] = comment_format.format(entity=entity,
                                                                              table_name=entity_user_select[entity][
                                                                                  "table_name"],
                                                                              comment_format=entity_user_select[entity][
                                                                                  "column_name"],
                                                                              value=entity_user_select[entity]["value"])
                    entity_retrieval.append(each_entity)
            self.normal_search_entity_slot = entity_retrieval
            logger.info(entity_retrieval)
            self.transition(QueryState.QA_RETRIEVAL)
        except Exception as e:
            self.answer.error_log[QueryState.USER_SELECT_ENTITY.name] = str(e)
            logger.error(
                f"The context is {self.context.search_box}, handle_user_select encountered an error: {e}")
            self.transition(QueryState.ERROR)

    def handle_add_to_log(self, log_id):
        answer_info = change_class_to_str(self.answer)
        current_time = get_current_time()
        sql = ""
        if self.answer.query_intent == "normal_search":
            sql = self.answer.sql_search_result.sql
        LogManagement.add_log_to_database(log_id=log_id, user_id=self.context.user_id,
                                          session_id=self.context.session_id,
                                          profile_name=self.context.selected_profile, sql=sql,
                                          query=self.context.search_box,
                                          intent=self.answer.query_intent,
                                          log_info=answer_info,
                                          log_type="chat_history",
                                          time_str=current_time)
    
    def _generate_agent_sql_again(self, task_query, original_sql, error_info):
    #重新生成agent任务的SQL，使用错误信息作为额外上下文
        try:
            # 构建包含错误信息的提示
            additional_info = f'''\n NOTE: when I try to write a SQL <sql>{original_sql}</sql>, I got an error <e>{error_info}</e>. Please consider and avoid this problem. '''
            
            # 调用LLM重新生成SQL
            response, model_response = text_to_sql(
                self.context.database_profile['tables_info'],
                self.context.database_profile['hints'],
                self.context.database_profile['prompt_map'],
                task_query,  # 使用子任务的查询而不是原始查询
                model_id=self.context.model_type,
                sql_examples=self.normal_search_qa_retrival if hasattr(self, 'normal_search_qa_retrival') else [],
                ner_example=self.normal_search_entity_slot if hasattr(self, 'normal_search_entity_slot') else [],
                dialect=self.context.database_profile['db_type'],
                model_provider=None,
                additional_info=additional_info
            )
            
            # 记录token使用情况
            if model_response.token_info is not None and len(model_response.token_info) > 0:
                if QueryState.SQL_GENERATION.name + "AGENT_CORRECTION" not in self.token_info:
                    self.token_info[QueryState.SQL_GENERATION.name + "AGENT_CORRECTION"] = {
                        "input_tokens": 0,
                        "output_tokens": 0
                    }
                
                if "input_tokens" in model_response.token_info:
                    self.token_info[QueryState.SQL_GENERATION.name + "AGENT_CORRECTION"]["input_tokens"] += model_response.token_info["input_tokens"]
                
                if "output_tokens" in model_response.token_info:
                    self.token_info[QueryState.SQL_GENERATION.name + "AGENT_CORRECTION"]["output_tokens"] += model_response.token_info["output_tokens"]
            
            # 提取SQL
            sql = get_generated_sql(response)
            
            # 应用行级安全策略
            post_sql = self._apply_row_level_security_for_sql(sql)
            
            return post_sql, response
        except Exception as e:
            logger.error(f"Error in _generate_agent_sql_again: {e}")
            return "", ""

