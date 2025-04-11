import json
import time

import io
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from nlq.business.profile import ProfileManagement
from nlq.business.connection import ConnectionManagement
from nlq.business.vector_store import VectorStore
from utils.logging import getLogger
from utils.navigation import make_sidebar
from utils.env_var import opensearch_info
from utils.apis import get_sql_result_tool

logger = getLogger()

DIMENSION_VALUE = "dimension"


def entity_data_check(entity_list):
    """
    check entity data format
    :param entity_list:
    :return:
    """
    try:
        if isinstance(entity_list, list):
            for item in entity_list:
                if "column_name" not in item:
                    return False
                if "table_name" not in item:
                    return False
                if "value" not in item:
                    return False
            return True
        else:
            return False
    except Exception as e:
        return False


@st.dialog("Modify the entity value")
def edit_value(profile, entity_item, entity_id):
    entity = entity_item["entity"]
    comment = entity_item["comment"]
    entity_type = entity_item.get("entity_type", "")
    entity_table_info = entity_item.get("entity_table_info", "")
    if entity_type == DIMENSION_VALUE:
        new_entity = st.text_input("Entity", value=entity, disabled=True)
        new_comment = st.text_area("Comment", value=comment, disabled=True)
        entity_table_info = st.text_area("Entity table info", value=entity_table_info)
        left_button, right_button = st.columns([1, 2])
        with right_button:
            if st.button("Submit"):
                entity_table_info = entity_table_info.replace("'", "\"")
                entity_table_info_list = json.loads(entity_table_info)
                entity_valid = entity_data_check(entity_table_info_list)
                if entity_valid:
                    VectorStore.delete_entity_sample(profile, entity_id)
                    time.sleep(2)
                    VectorStore.add_entity_dimension_batch_sample(profile, entity, "", DIMENSION_VALUE,
                                                                  entity_table_info_list)
                    st.success("Sample updated successfully!")
                    with st.spinner('Update Index ...'):
                        time.sleep(2)
                    st.session_state["entity_sample_search"][profile] = VectorStore.get_all_entity_samples(profile)
                    st.rerun()
                else:
                    st.success("Please Check Entity Info Format!")

        with left_button:
            if st.button("Cancel"):
                st.rerun()
    else:
        new_entity = st.text_input("Entity", value=entity, disabled=True)
        new_comment = st.text_area("Comment", value=comment)
        left_button, right_button = st.columns([1, 2])  # 第一个列占1份，第二个列占2份

        with right_button:
            if st.button("Submit"):
                VectorStore.add_entity_sample(profile, new_entity, new_comment)
                st.success("Sample updated successfully!")
                with st.spinner('Update Index ...'):
                    time.sleep(2)
                st.session_state["entity_sample_search"][profile] = VectorStore.get_all_entity_samples(profile)
                st.rerun()
        with left_button:
            if st.button("Cancel"):
                st.rerun()


def batch_insert_dimension_entity(profile, table, column, entity_data):
    if len(entity_data) > 0:
        entity_value = entity_data[column].tolist()
        progress_text = "Batch Insert in progress. Please wait."
        batch_bar = st.progress(0, text=progress_text)

        total_num = len(entity_value)
        for i, each_entity in enumerate(entity_value):
            if len(each_entity) > 0 and len(table) > 0 and len(column) > 0 and len(each_entity) > 0:
                entity_item_table_info = {}
                entity_item_table_info["table_name"] = table
                entity_item_table_info["column_name"] = column
                entity_item_table_info["value"] = each_entity
                VectorStore.add_entity_dimension_batch_sample(profile, each_entity, "", DIMENSION_VALUE,
                                                              [entity_item_table_info])
            batch_bar.progress((i + 1) / total_num, text=progress_text)
        batch_bar.empty()
    with st.spinner('Update Index ...'):
        time.sleep(2)
        st.session_state["entity_sample_search"][profile] = VectorStore.get_all_entity_samples(
            profile)


def delete_entity_sample(profile_name, id):
    VectorStore.delete_entity_sample(profile_name, id)
    new_value = []
    for item in st.session_state["entity_sample_search"][profile_name]:
        if item["id"] != id:
            new_value.append(item)
    st.session_state["entity_sample_search"][profile_name] = new_value
    st.success(f'Sample {id} deleted.')


def read_file(uploaded_file):
    """
    read upload csv file
    :param uploaded_file:
    :return:
    """
    file_type = uploaded_file.name.split('.')[-1].lower()
    if file_type == 'csv':
        uploaded_data = pd.read_csv(uploaded_file)
    elif file_type in ['xls', 'xlsx']:
        uploaded_data = pd.read_excel(uploaded_file)
    else:
        st.error(f"Unsupported file type: {file_type}")
        return None
    columns = list(uploaded_data.columns)
    if "entity" in columns and "comment" in columns:
        return uploaded_data[["entity", "comment"]]
    elif "entity" in columns and "table" in columns and "column" in columns and "value" in columns:
        return uploaded_data[["entity", "table", "column", "value"]]
    else:
        st.error(f"The columns need contains entity and comment")
        return None


def main():
    load_dotenv()
    logger.info('start entity management')
    st.set_page_config(page_title="Entity Management", )
    make_sidebar()

    if 'profile_page_mode' not in st.session_state:
        st.session_state['index_mgt_mode'] = 'default'

    if 'current_profile' not in st.session_state:
        st.session_state['current_profile'] = ''

    if 'ner_refresh_view' not in st.session_state:
        st.session_state['ner_refresh_view'] = False

    if "update_profile" not in st.session_state:
        st.session_state.update_profile = False

    if "profiles_list" not in st.session_state:
        st.session_state["profiles_list"] = []

    if "entity_sample_search" not in st.session_state:
        st.session_state["entity_sample_search"] = {}

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
        st.title("Entity Management")
        all_profiles_list = st.session_state["profiles_list"]
        if st.session_state.current_profile != "" and st.session_state.current_profile in all_profiles_list:
            profile_index = all_profiles_list.index(st.session_state.current_profile)
            current_profile = st.selectbox("My Data Profiles", all_profiles_list, index=profile_index)
        else:
            current_profile = st.selectbox("My Data Profiles", all_profiles_list,
                                           index=None,
                                           placeholder="Please select data profile...", key='current_profile_name')

        if current_profile not in st.session_state["entity_sample_search"]:
            st.session_state["entity_sample_search"][current_profile] = None

    if current_profile is not None:
        if st.session_state.ner_refresh_view or st.session_state["entity_sample_search"][current_profile] is None:
            st.session_state["entity_sample_search"][current_profile] = VectorStore.get_all_entity_samples(
                current_profile)
            st.session_state.ner_refresh_view = False

    tab_view, tab_add, tab_dimension, tab_search, batch_insert, batch_dimension_entity = st.tabs(
        ['View Entity Info', 'Add Metrics Entity', 'Add Dimension Entity', 'Entity Search', 'Batch Metrics Entity',
         'Batch Dimension Entity'])
    if current_profile is not None:
        st.session_state['current_profile'] = current_profile
        with tab_view:
            if current_profile is not None:
                st.write("The display page can show a maximum of 5000 pieces of data")
                for sample in st.session_state["entity_sample_search"][current_profile]:
                    with st.expander(sample['entity']):
                        st.code(sample['comment'])
                        st.button('Edit ' + sample['id'], on_click=edit_value,
                                  args=[current_profile, sample, sample['id']])
                        st.button('Delete ' + sample['id'], on_click=delete_entity_sample,
                                  args=[current_profile, sample['id']])

        with tab_add:
            if current_profile is not None:
                with st.form(key='entity_add_form'):
                    entity = st.text_input('Entity', key='index_question')
                    comment = st.text_area('Comment', key='index_answer', height=300)

                    if st.form_submit_button('Add Metrics Entity', type='primary'):
                        if len(entity) > 0 and len(comment) > 0:
                            VectorStore.add_entity_sample(current_profile, entity, comment)
                            st.success('Sample added')
                            st.success('Update Index')
                            with st.spinner('Update Index ...'):
                                time.sleep(2)
                            st.session_state["entity_sample_search"][
                                current_profile] = VectorStore.get_all_entity_samples(
                                current_profile)
                            st.rerun()
                        else:
                            st.error('please input valid question and answer')
        with tab_dimension:
            if current_profile is not None:
                with st.form(key='entity_add_form_dimension'):
                    entity = st.text_input('Entity', key='index_entity')
                    table = st.text_input('Table', key='index_table')
                    column = st.text_input('Column', key='index_column')
                    value = st.text_input('Dimension value', key='index_value')
                    if st.form_submit_button('Add Dimension Entity', type='primary'):
                        if len(entity) > 0 and len(table) > 0 and len(column) > 0 and len(value) > 0:
                            entity_item_table_info = {}
                            entity_item_table_info["table_name"] = table
                            entity_item_table_info["column_name"] = column
                            entity_item_table_info["value"] = value
                            VectorStore.add_entity_dimension_batch_sample(current_profile, entity, "", DIMENSION_VALUE,
                                                                          [entity_item_table_info])
                            st.success('Sample added')
                            st.success('Update Index')
                            with st.spinner('Update Index ...'):
                                time.sleep(2)
                            st.session_state["entity_sample_search"][
                                current_profile] = VectorStore.get_all_entity_samples(
                                current_profile)
                            st.rerun()
                        else:
                            st.error('please input valid question and answer')

        with tab_search:
            if current_profile is not None:
                entity_search = st.text_input('Entity Search', key='index_entity_search')
                retrieve_number = st.slider("Entity Retrieve Number", 0, 100, 10)
                if st.button('Search', type='primary'):
                    if len(entity_search) > 0:
                        search_sample_result = VectorStore.search_sample(current_profile, retrieve_number,
                                                                         opensearch_info['ner_index'],
                                                                         entity_search)
                        for sample in search_sample_result:
                            sample_res = {'Score': sample['_score'],
                                          'Entity': sample['_source']['entity'],
                                          'Answer': sample['_source']['comment'].strip()}
                            st.code(sample_res)
                            st.button('Delete ' + sample['_id'], key=sample['_id'], on_click=delete_entity_sample,
                                      args=[current_profile, sample['_id']])

        with batch_insert:
            if current_profile is not None:
                st.write("This page support CSV or Excel files batch insert entity samples.")
                st.write("**The Column Name need contain 'entity' and 'comment'**")

                with st.form(key='upload_metrics_form'):
                    uploaded_files = st.file_uploader("Choose CSV or Excel files", accept_multiple_files=True,
                                                      type=['csv', 'xls', 'xlsx'], key="add metrics value")
                    metrics_submit_button = st.form_submit_button(label='Upload Metrics Files')
                if metrics_submit_button and uploaded_files:
                    for i, uploaded_file in enumerate(uploaded_files):
                        status_text = st.empty()
                        status_text.text(f"Processing file {i + 1} of {len(uploaded_files)}: {uploaded_file.name}")
                        each_upload_data = read_file(uploaded_file)
                        if each_upload_data is not None:
                            total_rows = len(each_upload_data)
                            unique_batch_data = {}
                            for j, item in enumerate(each_upload_data.itertuples(), 1):
                                entity = str(item.entity)
                                comment = str(item.comment)
                                if entity not in unique_batch_data:
                                    unique_batch_data[entity] = ""
                                unique_batch_data[entity] = comment

                            progress_bar = st.progress(0)
                            unique_total_row = len(unique_batch_data)
                            for k, (key, value) in enumerate(unique_batch_data.items(), 1):
                                VectorStore.add_entity_sample(current_profile, key, value)
                                progress = (k * 1.0) / unique_total_row
                                upload_text = "Batch insert in progress. {} entities have been uploaded. Please wait.".format(
                                    str(k))
                                progress_bar.progress(progress, text=upload_text)
                            progress_bar.empty()
                        st.session_state.ner_refresh_view = True
                        st.success("{uploaded_file} uploaded successfully!".format(uploaded_file=uploaded_file.name))
                    with st.spinner('Update Index ...'):
                        time.sleep(2)
                    st.session_state["entity_sample_search"][current_profile] = VectorStore.get_all_entity_samples(
                        current_profile)
                    st.rerun()

        with batch_dimension_entity:
            if current_profile is not None:
                dimension_load_type = ["Table Select", "Upload File"]

                dimension_load = st.selectbox("Dimension Load Type", dimension_load_type, index=0)
                if dimension_load == "Table Select":
                    profile_detail = st.session_state['profiles'][current_profile]
                    if profile_detail['db_url'] == '':
                        conn_name = profile_detail['conn_name']
                        db_url = ConnectionManagement.get_db_url_by_name(conn_name)
                        profile_detail['db_url'] = db_url
                        profile_detail['db_type'] = ConnectionManagement.get_db_type_by_name(conn_name)

                    tables = profile_detail["tables"]
                    table_select = st.selectbox("Tables", tables, index=None)
                    if table_select is not None:
                        conn_config = profile_detail["conn_name"]
                        conn_config = ConnectionManagement.get_conn_config_by_name(conn_config)

                        tables_info = ConnectionManagement.get_table_column_definition_by_config(conn_config,
                                                                                                [table_select])
                        st.write(tables_info)

                        column_info = tables_info[table_select]

                        column_select = st.selectbox("Column", column_info.keys(), index=None)

                        if column_select is not None:
                            download_sql = """select DISTINCT({column}) from {table}""".format(column=column_select, table=table_select)

                            download_data = get_sql_result_tool(profile_detail, download_sql)
                            download_data = download_data["data"]
                            if isinstance(download_data, list):
                                download_data = pd.DataFrame()
                            download_data_csv = download_data.to_csv(index=0, encoding='utf_8_sig')

                            download_data_bytes = io.BytesIO(download_data_csv.encode('utf-8-sig'))

                            st.download_button(
                                label="Download Insert data as CSV",
                                data=download_data_bytes,
                                file_name="batch_insert_dimension_entity.csv",
                                mime="text/csv",
                            )
                            st.button('Batch Insert Dimension Entity', on_click=batch_insert_dimension_entity,
                                         args=[current_profile, table_select, column_select, download_data])


                else:
                    st.write("This page support CSV or Excel files batch insert dimension entity samples.")
                    st.write("**The Column Name need contain 'entity' 'table' 'column' 'value'**")

                    with st.form(key='upload_dimension_form'):
                        uploaded_files = st.file_uploader("Choose CSV or Excel files", accept_multiple_files=True,
                                                      type=['csv', 'xls', 'xlsx'], key="add dimension value")
                        dimension_submit_button = st.form_submit_button(label='Upload Dimension Files')

                    if dimension_submit_button and uploaded_files:
                        for i, uploaded_file in enumerate(uploaded_files):
                            status_text = st.empty()
                            status_text.text(f"Processing file {i + 1} of {len(uploaded_files)}: {uploaded_file.name}")
                            each_upload_data = read_file(uploaded_file)
                            if each_upload_data is not None:
                                total_rows = len(each_upload_data)
                                unique_batch_data = {}
                                for j, item in enumerate(each_upload_data.itertuples(), 1):
                                    entity = str(item.entity)
                                    table = str(item.table)
                                    column = str(item.column)
                                    value = str(item.value)
                                    entity_item_table_info = {}
                                    entity_item_table_info["table_name"] = table
                                    entity_item_table_info["column_name"] = column
                                    entity_item_table_info["value"] = value
                                    value_id = table + "#" + column + "#" + value
                                    if entity in unique_batch_data:
                                        if value_id not in unique_batch_data[entity]["value_id"]:
                                            unique_batch_data[entity]["value_id"].append(value_id)
                                            unique_batch_data[entity]["value_list"].append(entity_item_table_info)
                                    else:
                                        unique_batch_data[entity] = {}
                                        unique_batch_data[entity]["value_id"] = []
                                        unique_batch_data[entity]["value_id"].append(value_id)
                                        unique_batch_data[entity]["value_list"] = []
                                        unique_batch_data[entity]["value_list"].append(entity_item_table_info)

                                progress_bar = st.progress(0)
                                unique_total_row = len(unique_batch_data)
                                for k, (key, value) in enumerate(unique_batch_data.items(), 1):
                                    VectorStore.add_entity_dimension_batch_sample(current_profile, key, "",
                                                                                  DIMENSION_VALUE,
                                                                                  value["value_list"])
                                    progress = (k * 1.0) / unique_total_row
                                    upload_text = "Batch insert in progress. {} entities have been uploaded. Please wait.".format(
                                        str(k))
                                    progress_bar.progress(progress, text=upload_text)

                                progress_bar.empty()
                            st.session_state.ner_refresh_view = True
                            st.success(
                                "{uploaded_file} uploaded successfully!".format(uploaded_file=uploaded_file.name))
                        with st.spinner('Update Index ...'):
                            time.sleep(2)
                        st.session_state["entity_sample_search"][current_profile] = VectorStore.get_all_entity_samples(
                            current_profile)
                        st.rerun()

    else:
        st.info('Please select data profile in the left sidebar.')


if __name__ == '__main__':
    main()
