import streamlit as st

from nlq.business.vector_store import VectorStore
from utils.navigation import make_sidebar
from utils.opensearch import opensearch_index_init
from utils.prompts.check_prompt import check_model_id_prompt
from config_files.language_config import get_text
from utils.env_var import load_default_embedding_model
from utils.logging import getLogger

# 加载默认嵌入模型
load_default_embedding_model()


st.set_page_config(
    page_title="Generative BI",
    page_icon="👋",
)

# Get current language from session state
if 'language' not in st.session_state:
    st.session_state['language'] = 'en'
lang = st.session_state['language']

make_sidebar()

st.write(f"## {get_text('welcome_title', lang)}")

st.sidebar.success(get_text('select_demo', lang))

if lang == 'en':
    st.markdown(
        """
    In the data analysis scenario, analysts often need to write multi-round, complex query statements to obtain business insights.

    Amazon Web Services has built an intelligent data analysis assistant solution to address this scenario. Leveraging the powerful natural language understanding capabilities of large language models, non-technical users can query and analyze data through natural language, without needing to master SQL or other professional skills, helping business users obtain data insights and improve decision-making efficiency. 

    This guide is based on services such as Amazon Bedrock, Amazon OpenSearch, and Amazon DynamoDB.
    """
    )
else:
    st.markdown(
        """
    在数据分析场景中，分析师通常需要编写多轮复杂的查询语句来获取业务洞察。

    亚马逊云科技构建了一个智能数据分析助手解决方案来应对这一场景。利用大型语言模型强大的自然语言理解能力，非技术用户可以通过自然语言查询和分析数据，无需掌握SQL或其他专业技能，帮助业务用户获取数据洞察并提高决策效率。

    本指南基于Amazon Bedrock、Amazon OpenSearch和Amazon DynamoDB等服务。
    """
    )

# Check OpenSearch Index Init and Test Embedding Insert
opensearch_index_init = opensearch_index_init()
if not opensearch_index_init:
    st.info("The OpenSearch Index is Error, Please Create OpenSearch Index First!!!")
else:
    try:
        current_profile = "entity_insert_test"
        entity = "Month on month ratio"
        comment = "The month on month growth rate refers to the growth rate compared to the previous period, and the calculation formula is: month on month growth rate=(current period number - previous period number)/previous period number x 100%"
        VectorStore.add_entity_sample(current_profile, entity, comment)
    except Exception as e:
        st.warning(f"初始化示例实体时出错，但不影响系统使用: {str(e)}")
        import traceback
        logger = getLogger()
        logger.error(f"初始化示例实体错误详情: {traceback.format_exc()}")
        print(traceback.format_exc())

check_model_id_prompt()