from collections import defaultdict

import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from api.service import user_feedback_downvote
from nlq.business.connection import ConnectionManagement
from nlq.business.model import ModelManagement
from nlq.business.profile import ProfileManagement
from nlq.business.vector_store import VectorStore
from nlq.business.embedding import EmbeddingModelManagement
from nlq.core.chat_context import ProcessingContext
from nlq.core.state import QueryState
from nlq.core.state_machine import QueryStateMachine
from utils.logging import getLogger
from utils.navigation import make_sidebar
from utils.env_var import opensearch_info
from config_files.language_config import get_text

logger = getLogger()


def sample_question_clicked(sample):
    """Update the selected_sample variable with the text of the clicked button"""
    st.session_state['selected_sample'] = sample


def upvote_clicked(question, sql):
    """
    add upvote button to opensearch
    :param question: user question
    :param sql: true SQL
    :param env_vars:
    :return:
    """
    current_profile = st.session_state.current_profile
    VectorStore.add_sample(current_profile, question, sql)
    logger.info(f'up voted "{question}" with sql "{sql}"')


def upvote_agent_clicked(question, comment):
    # HACK: configurable opensearch endpoint

    current_profile = st.session_state.current_profile
    VectorStore.add_agent_cot_sample(current_profile, question, str(comment))
    logger.info(f'up voted "{question}" with sql "{comment}"')


def downvote_clicked(question, comment):
    current_profile = st.session_state.current_profile
    user_id = "admin"
    session_id = "-1"
    query = question
    query_intent = "normal_search"
    query_answer = str(comment)
    user_feedback_downvote(current_profile, user_id, session_id, query, query_intent, query_answer)


def clean_st_history(selected_profile):
    st.session_state.messages[selected_profile] = []
    st.session_state.query_rewrite_history[selected_profile] = []
    st.session_state.current_sql_result = None


def set_vision_change():
    st.session_state.vision_change = True


def get_user_history(selected_profile: str):
    """
    get user history for selected profile
    :param selected_profile:
    :return: history for selected profile list type
    """
    history_list = st.session_state.query_rewrite_history[selected_profile]
    history_query = []
    for messages in history_list:
        if messages["content"] is not None:
            history_query.append(messages["role"] + ":" + messages["content"])
    return history_query


def do_visualize_results():
    sql_query_result = st.session_state.current_sql_result
    lang = st.session_state['language']
    
    if sql_query_result is not None:
        # Auto-detect columns
        available_columns = sql_query_result.columns.tolist()

        # Initialize session state for x_column and y_column if not already present
        if 'x_column' not in st.session_state or st.session_state.x_column is None:
            st.session_state.x_column = available_columns[0] if available_columns else None
        if 'y_column' not in st.session_state or st.session_state.x_column is None:
            st.session_state.y_column = available_columns[0] if available_columns else None

        # Layout configuration
        col1, col2, col3 = st.columns([1, 1, 2])

        # Chart type selection
        chart_type = col1.selectbox(get_text('choose_chart_type', lang), 
                                   [get_text('table', lang), get_text('bar', lang), get_text('line', lang), get_text('pie', lang)],
                                   on_change=set_vision_change)

        if chart_type != get_text('table', lang):
            # X-axis and Y-axis selection
            st.session_state.x_column = col2.selectbox(get_text('choose_x_axis', lang), available_columns,
                                                       on_change=set_vision_change,
                                                       index=available_columns.index(
                                                           st.session_state.x_column) if st.session_state.x_column in available_columns else 0)
            st.session_state.y_column = col3.selectbox(get_text('choose_y_axis', lang), available_columns,
                                                       on_change=set_vision_change,
                                                       index=available_columns.index(
                                                           st.session_state.y_column) if st.session_state.y_column in available_columns else 0)

        # Visualization
        if chart_type == get_text('table', lang):
            st.dataframe(sql_query_result, hide_index=True)
        elif chart_type == get_text('bar', lang):
            st.plotly_chart(px.bar(sql_query_result, x=st.session_state.x_column, y=st.session_state.y_column))
        elif chart_type == get_text('line', lang):
            st.plotly_chart(px.line(sql_query_result, x=st.session_state.x_column, y=st.session_state.y_column))
        elif chart_type == get_text('pie', lang):
            st.plotly_chart(px.pie(sql_query_result, names=st.session_state.x_column, values=st.session_state.y_column))


def recurrent_display(messages, i):
    # hacking way of displaying messages, since the chat_message does not support multiple messages outside of "with" statement
    current_role = messages[i]["role"]
    message = messages[i]
    if message["type"] == "pandas":
        if isinstance(message["content"], pd.DataFrame):
            st.dataframe(message["content"], hide_index=True)
        elif isinstance(message["content"], list):
            for each_content in message["content"]:
                st.write(each_content["query"])
                st.dataframe(pd.read_json(each_content["data_result"], orient='records'), hide_index=True)
    elif message["type"] == "text":
        st.markdown(message["content"])
    elif message["type"] == "error":
        st.error(message["content"])
    elif message["type"] == "sql":
        with st.expander("The Generate SQL"):
            st.code(message["content"], language="sql")
    return i


def main():
    load_dotenv()

    # 必须是第一个Streamlit命令
    st.set_page_config(page_title="Demo", layout="wide")
    
    # Initialize language preference in session state if not already set
    if 'language' not in st.session_state:
        st.session_state['language'] = 'en'
    
    make_sidebar()
    
    # Language selector is now handled in make_sidebar() function
    
    # Get current language
    lang = st.session_state['language']
    
    # Title and Description
    st.subheader(get_text('page_title', lang))

    st.write(f"{get_text('current_username', lang)}: {st.session_state['auth_username']}")

    # Initialize or set up state variables

    if "update_profile" not in st.session_state:
        st.session_state.update_profile = False

    if "profiles_list" not in st.session_state:
        st.session_state["profiles_list"] = []

    if 'profiles' not in st.session_state:
        # get all user defined profiles with info (db_url, conn_name, tables_info, hints, search_samples)
        all_profiles = ProfileManagement.get_all_profiles_with_info()
        # all_profiles.update(demo_profile)
        st.session_state['profiles'] = all_profiles
        st.session_state["profiles_list"] = list(all_profiles.keys())
    else:
        if st.session_state.update_profile:
            logger.info("session_state update_profile get_all_profiles_with_info")
            all_profiles = ProfileManagement.get_all_profiles_with_info()
            st.session_state["profiles_list"] = list(all_profiles.keys())
            st.session_state['profiles'] = all_profiles
            st.session_state.update_profile = False

    if "vision_change" not in st.session_state:
        st.session_state["vision_change"] = False

    if 'selected_sample' not in st.session_state:
        st.session_state['selected_sample'] = ''

    if 'ask_replay' not in st.session_state:
        st.session_state.ask_replay = False

    if 'current_profile' not in st.session_state:
        st.session_state['current_profile'] = ''

    if 'current_model_id' not in st.session_state:
        st.session_state['current_model_id'] = ''

    if 'config_data_with_analyse' not in st.session_state:
        st.session_state['config_data_with_analyse'] = False

    if "messages" not in st.session_state:
        st.session_state.messages = {}

    if "query_rewrite_history" not in st.session_state:
        st.session_state.query_rewrite_history = {}

    if "current_sql_result" not in st.session_state:
        st.session_state.current_sql_result = None

    if "previous_state" not in st.session_state:
        st.session_state.previous_state = {}

    if "samaker_model" not in st.session_state:
        st.session_state.samaker_model = ModelManagement.get_all_models()
        
    # 获取全局设置
    global_settings = EmbeddingModelManagement.get_all_global_settings()
    
    # 应用默认embedding模型
    EmbeddingModelManagement.apply_default_embedding_model()
    
    # 设置默认LLM模型
    default_llm = global_settings.get('default_llm_model', {}).get('value', '')
    if default_llm and not st.session_state.current_model_id:
        st.session_state.current_model_id = default_llm
        logger.info(f"Using default LLM model from global settings: {default_llm}")
    
    # 设置默认Profile
    default_profile = global_settings.get('default_profile', {}).get('value', '')
    if default_profile and not st.session_state.current_profile and default_profile in st.session_state.get("profiles_list", []):
        st.session_state.current_profile = default_profile
        logger.info(f"Using default profile from global settings: {default_profile}")


    model_ids = []

    if len(st.session_state.samaker_model) > 0:
        model_ids.extend(st.session_state.samaker_model)

    session_state_list = list(st.session_state.get('profiles', {}).keys())

    hava_session_state_flag = False
    if len(session_state_list) > 0:
        hava_session_state_flag = True

    with st.sidebar:
        st.title(get_text('settings_title', lang))
        # The default option can be the first one in the profiles dictionary, if exists
        session_state_list = list(st.session_state.get('profiles', {}).keys())
        if st.session_state.current_profile != "":
            if st.session_state.current_profile in session_state_list:
                profile_index = session_state_list.index(st.session_state.current_profile)
                selected_profile = st.selectbox(get_text("data_profile", lang), session_state_list, index=profile_index)
            else:
                selected_profile = st.selectbox(get_text("data_profile", lang), session_state_list)
        else:
            selected_profile = st.selectbox(get_text("data_profile", lang), session_state_list)
        if selected_profile != st.session_state.current_profile:
            # clear session state
            st.session_state.selected_sample = ''
            st.session_state.current_profile = selected_profile
            if selected_profile not in st.session_state.messages:
                st.session_state.messages[selected_profile] = []
            if selected_profile not in st.session_state.query_rewrite_history:
                st.session_state.query_rewrite_history[selected_profile] = []
        else:
            if selected_profile not in st.session_state.messages:
                st.session_state.messages[selected_profile] = []
            if selected_profile not in st.session_state.query_rewrite_history:
                st.session_state.query_rewrite_history[selected_profile] = []

        if selected_profile not in st.session_state.previous_state:
            st.session_state.previous_state[selected_profile] = "INITIAL"

        if st.session_state.current_model_id != "" and st.session_state.current_model_id in model_ids:
            model_index = model_ids.index(st.session_state.current_model_id)
            model_type = st.selectbox(get_text("choose_model", lang), model_ids, index=model_index)
        else:
            model_type = st.selectbox(get_text("choose_model", lang), model_ids)

        use_rag_flag = st.checkbox(get_text("using_rag", lang), True)
        visualize_results_flag = st.checkbox(get_text("visualize_results", lang), True)
        intent_ner_recognition_flag = st.checkbox(get_text("intent_ner", lang), True)
        agent_cot_flag = st.checkbox(get_text("agent_cot", lang), True)
        explain_gen_process_flag = st.checkbox(get_text("explain_gen_process", lang), True)
        data_with_analyse = st.checkbox(get_text("answer_with_insights", lang), False)
        gen_suggested_question_flag = st.checkbox(get_text("gen_suggested_questions", lang), False)
        auto_correction_flag = st.checkbox(get_text("auto_correcting_sql", lang), True)
        show_token_cost = st.checkbox(get_text("show_token_cost", lang), False)
        context_window = st.slider(get_text("context_window", lang), 0, 10, 5)

        clean_history = st.button(get_text("clean_history", lang), on_click=clean_st_history, args=[selected_profile])

    st.chat_message("assistant").write(
        get_text("assistant_intro", lang))

    if not hava_session_state_flag:
        st.info(get_text("no_profile_warning", lang))
        return

    # Display sample questions
    comments = st.session_state.profiles[selected_profile]['comments']
    comments_questions = []
    if len(comments.split("Examples:")) > 1:
        comments_questions_txt = comments.split("Examples:")[1]
        comments_questions = [i for i in comments_questions_txt.split("\n") if i != '']

    search_samples = st.session_state.profiles[selected_profile]['search_samples']
    search_samples = search_samples + comments_questions
    question_column_number = 3
    search_sample_columns = st.columns(question_column_number)

    for i, sample in enumerate(search_samples):
        i = i % question_column_number
        search_sample_columns[i].button(sample, use_container_width=True, on_click=sample_question_clicked,
                                        args=[sample])

    # Display chat messages from history
    logger.info(f'{st.session_state.messages}')
    if selected_profile in st.session_state.messages:
        current_role = ""
        new_index = 0
        for i in range(len(st.session_state.messages[selected_profile])):
            print('!!!!!')
            print(i, new_index)
            # if i - 1 < new_index:
            #     continue
            with st.chat_message(st.session_state.messages[selected_profile][i]["role"]):
                new_index = recurrent_display(st.session_state.messages[selected_profile], i)

    text_placeholder = get_text("query_placeholder", lang)

    search_box = st.chat_input(placeholder=text_placeholder)
    if st.session_state['selected_sample'] != "":
        search_box = st.session_state['selected_sample']
        st.session_state['selected_sample'] = ""

    database_profile = st.session_state.profiles[selected_profile]
    with st.spinner('Connecting to database...'):
        # fix db url is Empty
        if database_profile['db_url'] == '':
            conn_name = database_profile['conn_name']
            db_url = ConnectionManagement.get_db_url_by_name(conn_name)
            database_profile['db_url'] = db_url
            database_profile['db_type'] = ConnectionManagement.get_db_type_by_name(conn_name)

    st.session_state.ask_replay = False

    # add select box for which model to use
    if search_box != "Type your query here..." or st.session_state.vision_change:
        if search_box is not None and len(search_box) > 0:
            st.session_state.current_sql_result = None
            with st.chat_message("user"):
                st.session_state.messages[selected_profile].append(
                    {"role": "user", "content": search_box, "type": "text"})
                st.session_state.query_rewrite_history[selected_profile].append(
                    {"role": "user", "content": search_box})
                st.markdown(search_box)
            user_query_history = get_user_history(selected_profile)
            with (st.chat_message("assistant")):
                previous_state = st.session_state.previous_state[selected_profile]
                processing_context = ProcessingContext(
                    search_box=search_box,
                    query_rewrite="",
                    session_id="",
                    user_id=st.session_state['auth_username'],
                    username=st.session_state['auth_username'],
                    selected_profile=selected_profile,
                    database_profile=database_profile,
                    model_type=model_type,
                    use_rag_flag=use_rag_flag,
                    intent_ner_recognition_flag=intent_ner_recognition_flag,
                    agent_cot_flag=agent_cot_flag,
                    explain_gen_process_flag=explain_gen_process_flag,
                    visualize_results_flag=visualize_results_flag,
                    data_with_analyse=data_with_analyse,
                    gen_suggested_question_flag=gen_suggested_question_flag,
                    auto_correction_flag=auto_correction_flag,
                    context_window=context_window,
                    entity_same_name_select={},
                    user_query_history=user_query_history,
                    opensearch_info=opensearch_info,
                    previous_state=previous_state)
                st.session_state.previous_state[selected_profile] = "INITIAL"
                state_machine = QueryStateMachine(processing_context)
                while state_machine.get_state() != QueryState.COMPLETE and state_machine.get_state() != QueryState.ERROR:
                    if state_machine.get_state() == QueryState.INITIAL:
                        with st.status(get_text("query_context_understanding", lang)) as status_text:
                            state_machine.handle_initial()
                            st.write(state_machine.get_answer().query_rewrite)
                        status_text.update(label=get_text("query_context_rewrite_completed", lang), state="complete", expanded=False)
                        if state_machine.get_answer().query_intent == "ask_in_reply":
                            st.session_state.query_rewrite_history[selected_profile].append(
                                {"role": "assistant", "content": state_machine.get_answer().query_rewrite})
                            st.session_state.messages[selected_profile].append(
                                {"role": "assistant", "content": state_machine.get_answer().query_rewrite,
                                 "type": "text"})
                            st.write(state_machine.get_answer().query_rewrite)
                    elif state_machine.get_state() == QueryState.REJECT_INTENT:
                        state_machine.handle_reject_intent()
                        st.write(get_text("query_not_supported", lang))
                    elif state_machine.get_state() == QueryState.KNOWLEDGE_SEARCH:
                        state_machine.handle_knowledge_search()
                        st.write(state_machine.get_answer().knowledge_search_result.knowledge_response)
                        st.session_state.messages[selected_profile].append(
                            {"role": "assistant",
                             "content": state_machine.get_answer().knowledge_search_result.knowledge_response,
                             "type": "text"})
                    elif state_machine.get_state() == QueryState.ENTITY_RETRIEVAL:
                        with st.status(get_text("entity_retrieval", lang)) as status_text:
                            state_machine.handle_entity_retrieval()
                            examples = []
                            for example in state_machine.normal_search_entity_slot:
                                examples.append({'Score': example['_score'],
                                                 'Question': example['_source']['entity'],
                                                 'Answer': example['_source']['comment'].strip()})
                            st.write(examples)
                            status_text.update(
                                label=get_text("entity_retrieval_completed", lang).format(len(state_machine.normal_search_entity_slot)),
                                state="complete", expanded=False)
                    elif state_machine.get_state() == QueryState.QA_RETRIEVAL:
                        state_machine.handle_qa_retrieval()
                        with st.status(get_text("qa_retrieval", lang)) as status_text:
                            examples = []
                            for example in state_machine.normal_search_qa_retrival:
                                examples.append({'Score': example['_score'],
                                                 'Question': example['_source']['text'],
                                                 'Answer': example['_source']['sql'].strip()})
                            st.write(examples)
                            status_text.update(
                                label=get_text("qa_retrieval_completed", lang).format(len(state_machine.normal_search_qa_retrival)),
                                state="complete", expanded=False)
                    elif state_machine.get_state() == QueryState.SQL_GENERATION:
                        with st.status(get_text("generating_sql", lang)) as status_text:
                            state_machine.handle_sql_generation()
                            sql = state_machine.get_answer().sql_search_result.sql
                            st.code(sql, language="sql")
                            if not visualize_results_flag:
                                st.session_state.messages[selected_profile].append(
                                {"role": "assistant", "content": sql, "type": "sql"})
                            feedback = st.columns(2)
                            feedback[0].button(get_text("upvote", lang), type='secondary',
                                               key="upvote",
                                               use_container_width=True,
                                               on_click=upvote_clicked,
                                               args=[state_machine.get_answer().query_rewrite,
                                                     sql])
                            feedback[1].button(get_text("downvote", lang), type='secondary', use_container_width=True,
                                               key="downvote",
                                               on_click=downvote_clicked,
                                               args=[state_machine.get_answer().query_rewrite, sql])
                            status_text.update(
                                label=get_text("generating_sql_done", lang),
                                state="complete", expanded=True)
                        if state_machine.context.explain_gen_process_flag:
                            with st.status(get_text("generating_explanations", lang)) as status_text:
                                st.markdown(state_machine.get_answer().sql_search_result.sql_gen_process)
                                status_text.update(
                                    label=get_text("generating_explanations_done", lang),
                                    state="complete", expanded=False)

                    elif state_machine.get_state() == QueryState.INTENT_RECOGNITION:
                        with st.status(get_text("intent_recognition", lang)) as status_text:
                            state_machine.handle_intent_recognition()
                            intent = state_machine.intent_response.get("intent", "normal_search")
                            st.write(state_machine.intent_response)
                        status_text.update(label=get_text("intent_recognition_completed", lang).format(intent),
                                           state="complete", expanded=False)
                    elif state_machine.get_state() == QueryState.EXECUTE_QUERY:
                        with st.status(get_text("execute_sql", lang)) as status_text:
                            state_machine.handle_execute_query()
                        status_text.update(label=get_text("execute_sql_done", lang),
                                           state="complete", expanded=False)
                        sql = state_machine.get_answer().sql_search_result.sql
                        if state_machine.use_auto_correction_flag:
                            with st.expander(get_text("sql_error_info", lang)):
                                st.markdown(state_machine.first_sql_execute_info["error_info"])
                            with st.status(get_text("generating_sql_again", lang)) as status_text:
                                st.code(sql, language="sql")
                                st.session_state.messages[selected_profile].append(
                                    {"role": "assistant", "content": sql, "type": "sql"})
                                feedback = st.columns(2)
                                feedback[0].button(get_text("upvote", lang), type='secondary',
                                                   key="upvote_again",
                                                   use_container_width=True,
                                                   on_click=upvote_clicked,
                                                   args=[state_machine.get_answer().query_rewrite,
                                                         sql])
                                feedback[1].button(get_text("downvote", lang), type='secondary', use_container_width=True,
                                                   key="downcote_again",
                                                   on_click=downvote_clicked,
                                                   args=[state_machine.get_answer().query_rewrite, sql])
                                status_text.update(
                                    label=get_text("generating_sql_done", lang),
                                    state="complete", expanded=True)
                        else:
                            st.session_state.messages[selected_profile].append(
                                {"role": "assistant", "content": sql, "type": "sql"})
                        if state_machine.get_answer().sql_search_result.sql_data is not None:
                            st.session_state.messages[selected_profile].append(
                                {"role": "assistant", "content": state_machine.get_answer().sql_search_result.sql_data, "type": "pandas"})

                    elif state_machine.get_state() == QueryState.ANALYZE_DATA:
                        with st.spinner(get_text("generating_data_summarize", lang)):
                            state_machine.handle_analyze_data()
                            st.write(state_machine.get_answer().sql_search_result.data_analyse)
                            st.session_state.messages[selected_profile].append(
                                {"role": "assistant",
                                 "content": state_machine.get_answer().sql_search_result.data_analyse,
                                 "type": "text"})
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
                        with st.status(get_text("agent_cot_retrieval", lang)) as status_text:
                            state_machine.handle_agent_task()
                            agent_examples = []
                            for example in state_machine.agent_cot_retrieve:
                                agent_examples.append({'Score': example['_score'],
                                                       'Question': example['_source']['query'],
                                                       'Answer': example['_source']['comment'].strip()})
                            st.write(agent_examples)
                        status_text.update(label=get_text("agent_cot_retrieval_completed", lang),
                                           state="complete", expanded=False)
                        with st.status(get_text("agent_task_split", lang)) as status_text:
                            st.write(state_machine.agent_task_split)
                        status_text.update(label=get_text("agent_task_split_completed", lang),
                                           state="complete", expanded=False)
                    elif state_machine.get_state() == QueryState.AGENT_SEARCH:
                        with st.status(get_text("multiple_sql_generated", lang)) as status_text:
                            state_machine.handle_agent_sql_generation()
                            st.write(state_machine.agent_search_result)
                        status_text.update(label=get_text("multiple_sql_generated_completed", lang),
                                           state="complete", expanded=False)
                    elif state_machine.get_state() == QueryState.AGENT_DATA_SUMMARY:
                        with st.spinner(get_text("generating_data_summarize", lang)):
                            state_machine.handle_agent_analyze_data()
                            for i in range(len(state_machine.agent_valid_data)):
                                st.write(state_machine.agent_valid_data[i]["query"])
                                st.dataframe(pd.read_json(state_machine.agent_valid_data[i]["data_result"],
                                                          orient='records'), hide_index=True)
                            st.session_state.messages[selected_profile].append(
                                {"role": "assistant", "content": state_machine.agent_valid_data, "type": "pandas"})

                            st.markdown(state_machine.get_answer().agent_search_result.agent_summary)
                            st.session_state.messages[selected_profile].append(
                                {"role": "assistant", "content": state_machine.get_answer().agent_search_result.agent_summary, "type": "text"})
                    else:
                        state_machine.state = QueryState.ERROR

                logger.info(f'{state_machine.get_state()}')
                logger.info("state_machine is done")
                if show_token_cost:
                    with st.status("Show Token Cost") as status_text:
                        st.write(state_machine.token_info)
                    status_text.update(label=f"Show Token Cost",
                                       state="complete", expanded=False)
                if state_machine.get_state() == QueryState.COMPLETE:
                    if state_machine.get_answer().query_intent == "normal_search":
                        if state_machine.intent_search_result["sql_execute_result"]["status_code"] == 200:
                            st.session_state.current_sql_result = state_machine.intent_search_result["sql_execute_result"]["data"]
                            if visualize_results_flag:
                                do_visualize_results()
                elif state_machine.get_state() == QueryState.ERROR:
                    with st.status(get_text("error_info", lang)) as status_text:
                        st.write(state_machine.get_answer().error_log)
                    status_text.update(label=get_text("error_info", lang),
                                       state="error", expanded=False)

                if processing_context.gen_suggested_question_flag:
                    if state_machine.search_intent_flag or state_machine.agent_intent_flag:
                        st.markdown(get_text("further_ask", lang))
                        with st.spinner(get_text("generating_suggested_questions", lang)):
                            state_machine.handle_suggest_question()
                            gen_sq_list = state_machine.get_answer().suggested_question
                            sq_result = st.columns(3)
                            sq_result[0].button(gen_sq_list[0], type='secondary',
                                                use_container_width=True,
                                                on_click=sample_question_clicked,
                                                args=[gen_sq_list[0]])
                            sq_result[1].button(gen_sq_list[1], type='secondary',
                                                use_container_width=True,
                                                on_click=sample_question_clicked,
                                                args=[gen_sq_list[1]])
                            sq_result[2].button(gen_sq_list[2], type='secondary',
                                                use_container_width=True,
                                                on_click=sample_question_clicked,
                                                args=[gen_sq_list[2]])
        else:
            if visualize_results_flag:
                do_visualize_results()


if __name__ == '__main__':
    main()
