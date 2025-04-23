import time
import sys
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from nlq.business.profile import ProfileManagement
from nlq.business.vector_store import VectorStore
from utils.logging import getLogger
from utils.navigation import make_sidebar
from utils.env_var import opensearch_info
from nlq.business.connection import ConnectionManagement
from nlq.core.chat_context import ProcessingContext
from nlq.core.state import QueryState
from nlq.core.state_machine import QueryStateMachine
from config_files.language_config import get_text

logger = getLogger()


def test_all_sample(selected_profile, model_type):
    logger.info(f'profile_name={selected_profile}')
    result = []
    # Initialize or set up state variables
    if 'profiles' not in st.session_state:
        # get all user defined profiles with info (db_url, conn_name, tables_info, hints, search_samples)
        all_profiles = ProfileManagement.get_all_profiles_with_info()
        st.session_state['profiles'] = all_profiles
    else:
        all_profiles = ProfileManagement.get_all_profiles_with_info()
        st.session_state['profiles'] = all_profiles

    if 'current_profile' not in st.session_state:
        st.session_state['current_profile'] = ''

    if 'current_model_id' not in st.session_state:
        st.session_state['current_model_id'] = ''

    if "messages" not in st.session_state:
        st.session_state.messages = {selected_profile: []}

    all_samples = VectorStore.get_all_samples(selected_profile)
    total_rows = len(all_samples)
    progress_bar = st.progress(0)
    for i, sample in list(enumerate(all_samples)):
        status_text = st.empty()
        status_text.text(f"Processing {i + 1} of {total_rows} - {[sample['text']]} ")
        progress = (i + 1) / total_rows
        progress_bar.progress(progress)

        logger.info("===>> \n\n")

        logger.info(f'session:{st.session_state}')

        database_profile = st.session_state.profiles[selected_profile]
        with st.spinner('Connecting to database...'):
            # fix db url is Empty
            if database_profile['db_url'] == '':
                conn_name = database_profile['conn_name']
                db_url = ConnectionManagement.get_db_url_by_name(conn_name)
                database_profile['db_url'] = db_url
                database_profile['db_type'] = ConnectionManagement.get_db_type_by_name(conn_name)

        logger.info(f'database_profile={database_profile}')

        processing_context = ProcessingContext(
            search_box=sample['text'],
            query_rewrite="",
            session_id="",
            user_id=st.session_state['auth_username'],
            username=st.session_state['username'],
            selected_profile=selected_profile,
            database_profile=database_profile,
            model_type=model_type,
            use_rag_flag=True,
            intent_ner_recognition_flag=True,
            agent_cot_flag=False,
            explain_gen_process_flag=False,
            visualize_results_flag=True,
            data_with_analyse=False,
            gen_suggested_question_flag=False,
            auto_correction_flag=True,
            context_window=0,
            entity_same_name_select={},
            user_query_history=[],
            opensearch_info=opensearch_info,
            previous_state="INITIAL"
        )
        state_machine = QueryStateMachine(processing_context)
        language = st.session_state.get('language', 'en')
        
        while state_machine.get_state() != QueryState.COMPLETE and state_machine.get_state() != QueryState.ERROR:
            if state_machine.get_state() == QueryState.INITIAL:
                with st.status(get_text("query_context_understanding", language)) as status_text:
                    state_machine.handle_initial()
                    st.write(state_machine.get_answer().query_rewrite)
            elif state_machine.get_state() == QueryState.REJECT_INTENT:
                state_machine.handle_reject_intent()
                st.write(get_text("query_not_supported", language))
            elif state_machine.get_state() == QueryState.KNOWLEDGE_SEARCH:
                state_machine.handle_knowledge_search()
                st.write(state_machine.get_answer().knowledge_search_result.knowledge_response)
                st.session_state.messages[selected_profile].append(
                    {"role": "assistant",
                     "content": state_machine.get_answer().knowledge_search_result.knowledge_response,
                     "type": "text"})
            elif state_machine.get_state() == QueryState.ENTITY_RETRIEVAL:
                with st.status(get_text("entity_retrieval", language)) as status_text:
                    state_machine.handle_entity_retrieval()
                    examples = []
                    for example in state_machine.normal_search_entity_slot:
                        examples.append({'Score': example['_score'],
                                         'Question': example['_source']['entity'],
                                         'Answer': example['_source']['comment'].strip()})
                    st.write(examples)
                    status_text.update(
                        label=get_text("entity_retrieval_completed", language).format(len(state_machine.normal_search_entity_slot)),
                        state="complete", expanded=False)
            elif state_machine.get_state() == QueryState.QA_RETRIEVAL:
                state_machine.handle_qa_retrieval()
                with st.status(get_text("qa_retrieval", language)) as status_text:
                    examples = []
                    for example in state_machine.normal_search_qa_retrival:
                        examples.append({'Score': example['_score'],
                                         'Question': example['_source']['text'],
                                         'Answer': example['_source']['sql'].strip()})
                    st.write(examples)
                    status_text.update(
                        label=get_text("qa_retrieval_completed", language).format(len(state_machine.normal_search_qa_retrival)),
                        state="complete", expanded=False)
            elif state_machine.get_state() == QueryState.SQL_GENERATION:
                with st.status(get_text("generating_sql", language)) as status_text:
                    state_machine.handle_sql_generation()
                    sql = state_machine.get_answer().sql_search_result.sql
                    st.code(sql, language="sql")
                    st.session_state.messages[selected_profile].append(
                        {"role": "assistant", "content": sql, "type": "sql"})
                    status_text.update(
                        label=get_text("generating_sql_done", language),
                        state="complete", expanded=True)

            elif state_machine.get_state() == QueryState.INTENT_RECOGNITION:
                with st.status(get_text("intent_recognition", language)) as status_text:
                    state_machine.handle_intent_recognition()
                    intent = state_machine.intent_response.get("intent", "normal_search")
                    st.write(state_machine.intent_response)
                status_text.update(label=get_text("intent_recognition_completed", language).format(intent),
                                   state="complete", expanded=False)
            elif state_machine.get_state() == QueryState.EXECUTE_QUERY:
                state_machine.handle_execute_query()
            elif state_machine.get_state() == QueryState.ASK_ENTITY_SELECT:
                state_machine.handle_entity_selection()
                if state_machine.get_answer().query_intent == "entity_select":
                    st.session_state.previous_state[selected_profile] = "ASK_ENTITY_SELECT"
                    st.markdown(state_machine.get_answer().ask_entity_select.entity_select)
                    st.session_state.query_rewrite_history[selected_profile].append(
                        {"role": "assistant", "content": state_machine.get_answer().ask_entity_select.entity_select})
                    st.session_state.messages[selected_profile].append(
                        {"role": "assistant", "content": state_machine.get_answer().ask_entity_select.entity_select,
                         "type": "text"})
            elif state_machine.get_state() == QueryState.AGENT_TASK:
                with st.status(get_text("agent_cot_retrieval", language)) as status_text:
                    state_machine.handle_agent_task()
                    agent_examples = []
                    for example in state_machine.agent_cot_retrieve:
                        agent_examples.append({'Score': example['_score'],
                                               'Question': example['_source']['query'],
                                               'Answer': example['_source']['comment'].strip()})
                    st.write(agent_examples)
                status_text.update(label=get_text("agent_cot_retrieval_completed", language),
                                   state="complete", expanded=False)
                with st.status(get_text("agent_task_split", language)) as status_text:
                    st.write(state_machine.agent_task_split)
                status_text.update(label=get_text("agent_task_split_completed", language),
                                   state="complete", expanded=False)
            elif state_machine.get_state() == QueryState.AGENT_SEARCH:
                with st.status(get_text("multiple_sql_generated", language)) as status_text:
                    state_machine.handle_agent_sql_generation()
                    st.write(state_machine.agent_search_result)
                status_text.update(label=get_text("multiple_sql_generated_completed", language),
                                   state="complete", expanded=False)
            elif state_machine.get_state() == QueryState.AGENT_DATA_SUMMARY:
                with st.spinner(get_text("generating_data_summarize", language)):
                    state_machine.handle_agent_analyze_data()
                    for i in range(len(state_machine.agent_valid_data)):
                        st.write(state_machine.agent_valid_data[i]["query"])
                        st.dataframe(pd.read_json(state_machine.agent_valid_data[i]["data_result"],
                                                  orient='records'), hide_index=True)
                    st.session_state.messages[selected_profile].append(
                        {"role": "assistant", "content": state_machine.agent_valid_data, "type": "pandas"})

                    st.markdown(state_machine.get_answer().agent_search_result.agent_summary)
                    st.session_state.messages[selected_profile].append(
                        {"role": "assistant", "content": state_machine.get_answer().agent_search_result.agent_summary,
                         "type": "text"})
            else:
                state_machine.state = QueryState.ERROR

        index = i + 1
        inputQuestion = sample['text']
        sampleSQL = sample['sql']
        testResult = state_machine.intent_search_result["sql_execute_result"]

        if state_machine.get_state() == QueryState.COMPLETE:
            if state_machine.get_answer().query_intent == "normal_search":
                if state_machine.intent_search_result["sql_execute_result"]["status_code"] == 200:
                    result.append([
                        i,
                        sample['text'],
                        sample['sql'],
                        state_machine.intent_search_result["sql_execute_result"]
                    ])
                    st.session_state.current_sql_result = \
                        state_machine.intent_search_result["sql_execute_result"]["data"]
                    # do_visualize_results()

        result.append({
            'index': index,
            'inputQuestion': inputQuestion,
            'sampleSQL': sampleSQL,
            'testResult': testResult

        })
    return result


@st.dialog("Modify the SQL value")
def edit_value(profile, entity_item, entity_id):
    language = st.session_state.get('language', 'en')
    text_value = entity_item["text"]
    sql_value = entity_item["sql"]
    text = st.text_input(get_text("question", language), value=text_value)
    sql = st.text_area(get_text("answer_sql", language), value=sql_value, height=300)
    left_button, right_button = st.columns([1, 2])
    with right_button:
        if st.button("Submit"):
            if text == text_value:
                VectorStore.add_sample(profile, text, sql)
            else:
                VectorStore.delete_sample(profile, entity_id)
                VectorStore.add_sample(profile, text, sql)
            st.success(get_text("sample_updated", language))
            with st.spinner(get_text("updating_index", language)):
                time.sleep(2)
            st.session_state["sql_sample_search"][profile] = VectorStore.get_all_samples(profile)
            st.rerun()
    with left_button:
        if st.button("Cancel"):
            st.rerun()


def delete_sample(profile_name, id):
    language = st.session_state.get('language', 'en')
    VectorStore.delete_sample(profile_name, id)
    new_value = []
    for item in st.session_state["sql_sample_search"][profile_name]:
        if item["id"] != id:
            new_value.append(item)
    st.session_state["sql_sample_search"][profile_name] = new_value
    st.success(get_text("sample_deleted", language).format(id))


def read_file(uploaded_file):
    """
    read upload csv file
    :param uploaded_file:
    :return:
    """
    language = st.session_state.get('language', 'en')
    file_type = uploaded_file.name.split('.')[-1].lower()
    if file_type == 'csv':
        uploaded_data = pd.read_csv(uploaded_file)
    elif file_type in ['xls', 'xlsx']:
        uploaded_data = pd.read_excel(uploaded_file)
    else:
        st.error(get_text("unsupported_file_type", language).format(file_type))
        return None
    columns = list(uploaded_data.columns)
    if "question" in columns and "sql" in columns:
        return uploaded_data
    else:
        st.error(get_text("columns_need_contain", language))
        return None


def main():
    load_dotenv()
    logger.info('start index management')
    language = st.session_state.get('language', 'en')
    st.set_page_config(page_title=get_text("index_management_title", language))
    make_sidebar()

    if 'profile_page_mode' not in st.session_state:
        st.session_state['index_mgt_mode'] = 'default'

    if 'current_profile' not in st.session_state:
        st.session_state['current_profile'] = ''

    if "update_profile" not in st.session_state:
        st.session_state.update_profile = False

    if "profiles_list" not in st.session_state:
        st.session_state["profiles_list"] = []

    if "sql_sample_search" not in st.session_state:
        st.session_state["sql_sample_search"] = {}

    if 'sql_refresh_view' not in st.session_state:
        st.session_state['sql_refresh_view'] = False

    if 'profiles' not in st.session_state:
        all_profiles = ProfileManagement.get_all_profiles_with_info()
        st.session_state['profiles'] = all_profiles
        st.session_state["profiles_list"] = list(all_profiles.keys())

    if st.session_state.update_profile:
        logger.info("session_state update_profile get_all_profiles_with_info")
        all_profiles = ProfileManagement.get_all_profiles_with_info()
        st.session_state["profiles_list"] = list(all_profiles.keys())
        st.session_state['profiles'] = all_profiles
        st.session_state.update_profile = False

    with st.sidebar:
        st.title(get_text("index_management_title", language))
        all_profiles_list = st.session_state["profiles_list"]
        if st.session_state.current_profile != "" and st.session_state.current_profile in all_profiles_list:
            profile_index = all_profiles_list.index(st.session_state.current_profile)
            current_profile = st.selectbox(get_text("my_data_profiles", language), all_profiles_list, index=profile_index)
        else:
            current_profile = st.selectbox(get_text("my_data_profiles", language), all_profiles_list,
                                           index=None,
                                           placeholder=get_text("select_profile", language), key='current_profile_name')

        if current_profile not in st.session_state["sql_sample_search"]:
            st.session_state["sql_sample_search"][current_profile] = None

    if current_profile is not None:
        if st.session_state.sql_refresh_view or st.session_state["sql_sample_search"][current_profile] is None:
            st.session_state["sql_sample_search"][current_profile] = VectorStore.get_all_samples(current_profile)
            st.session_state.sql_refresh_view = False

    tab_view, tab_add, tab_search, batch_insert, reg_testing = st.tabs([
        get_text("view_samples", language), 
        get_text("add_new_sample", language), 
        get_text("sample_search", language), 
        get_text("batch_insert_samples", language), 
        get_text("regression_test", language)
    ])

    if current_profile is not None:
        st.session_state['current_profile'] = current_profile
        with tab_view:
            if current_profile is not None:
                st.write(get_text("max_display_info", language))
                for sample in st.session_state["sql_sample_search"][current_profile]:
                    with st.expander(sample['text']):
                        st.code(sample['sql'])
                        st.button(get_text("edit", language) + sample['id'], on_click=edit_value,
                                  args=[current_profile, sample, sample['id']])
                        st.button(get_text("delete", language) + sample['id'], on_click=delete_sample,
                                  args=[current_profile, sample['id']])

        with tab_add:
            with st.form(key='sql_add_form'):
                question = st.text_input(get_text("question", language), key='index_question')
                answer = st.text_area(get_text("answer_sql", language), key='index_answer', height=300)

                if st.form_submit_button(get_text("add_sql_info", language), type='primary'):
                    if len(question) > 0 and len(answer) > 0:
                        VectorStore.add_sample(current_profile, question, answer)
                        st.success(get_text("sample_added", language))
                        st.success(get_text("update_index", language))
                        with st.spinner(get_text("updating_index", language)):
                            time.sleep(2)
                        st.session_state["sql_sample_search"][current_profile] = VectorStore.get_all_samples(current_profile)
                        st.rerun()
                    else:
                        st.error(get_text("input_valid_qa", language))
        with tab_search:
            if current_profile is not None:
                entity_search = st.text_input(get_text("question_search", language), key='index_entity_search')
                retrieve_number = st.slider(get_text("question_retrieve_number", language), 0, 100, 10)
                if st.button(get_text("search", language), type='primary'):
                    if len(entity_search) > 0:
                        search_sample_result = VectorStore.search_sample(current_profile, retrieve_number,
                                                                         opensearch_info['sql_index'],
                                                                         entity_search)
                        for sample in search_sample_result:
                            sample_res = {'Score': sample['_score'],
                                          'Entity': sample['_source']['text'],
                                          'Answer': sample['_source']['sql'].strip()}
                            st.code(sample_res)
                            st.button(get_text("delete", language) + sample['_id'], key=sample['_id'], on_click=delete_sample,
                                      args=[current_profile, sample['_id']])
        with batch_insert:
            if current_profile is not None:
                st.write(get_text("batch_insert_info", language))
                st.write(get_text("column_name_info", language))

                with st.form(key='upload_sql_form'):
                    uploaded_files = st.file_uploader(get_text("choose_files", language), accept_multiple_files=True,
                                                  type=['csv', 'xls', 'xlsx'])
                    sql_submit_button = st.form_submit_button(label=get_text("upload_sql_files", language))
                if uploaded_files and sql_submit_button:
                    for i, uploaded_file in enumerate(uploaded_files):
                        status_text = st.empty()
                        status_text.text(get_text("processing_file", language).format(i + 1, len(uploaded_files), uploaded_file.name))
                        each_upload_data = read_file(uploaded_file)
                        if each_upload_data is not None:
                            total_rows = len(each_upload_data)
                            progress_bar = st.progress(0)
                            progress_text = get_text("batch_insert_progress", language).format(uploaded_file.name)
                            for j, item in enumerate(each_upload_data.itertuples(), 1):
                                question = str(item.question)
                                sql = str(item.sql)
                                VectorStore.add_sample(current_profile, question, sql)
                                progress = (j * 1.0) / total_rows
                                progress_bar.progress(progress, text=progress_text)
                            progress_bar.empty()
                        st.success(get_text("uploaded_successfully", language).format(uploaded_file.name))
                        with st.spinner(get_text("updating_index", language)):
                            time.sleep(2)
                        st.session_state["sql_sample_search"][current_profile] = VectorStore.get_all_samples(current_profile)
                        st.rerun()


        with reg_testing:
            if current_profile is not None:
                total_sample_count = len(VectorStore.get_all_samples(current_profile))
                st.write(get_text("total_samples_test", language).format(total_sample_count))
                model_ids = ['anthropic.claude-3-5-sonnet-20241022-v2:0', 'anthropic.claude-3-5-sonnet-20240620-v1:0', 'anthropic.claude-3-sonnet-20240229-v1:0',
                             'anthropic.claude-3-opus-20240229-v1:0',
                             'anthropic.claude-3-haiku-20240307-v1:0', 'mistral.mixtral-8x7b-instruct-v0:1',
                             'meta.llama3-70b-instruct-v1:0']
                if 'current_model_id' in st.session_state.keys() and st.session_state.current_model_id != "" and st.session_state.current_model_id in model_ids:
                    model_index = model_ids.index(st.session_state.current_model_id)
                    model_type = st.selectbox(get_text("choose_model", language), model_ids, index=model_index)
                else:
                    model_type = st.selectbox(get_text("choose_model", language), model_ids)

                if st.button(get_text("test_all", language), type='primary'):
                    if total_sample_count > 0:
                        test_result = test_all_sample(current_profile, model_type)
                        st.write(get_text("regression_testing_result", language))
                        st.write(test_result)
                    st.success(get_text("testing_completed", language))

    else:
        st.info(get_text("select_profile", language))


if __name__ == '__main__':
    main()
