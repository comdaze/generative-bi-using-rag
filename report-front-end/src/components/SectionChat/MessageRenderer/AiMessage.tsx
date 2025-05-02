import { Button as AmplifyBtn, Divider } from "@aws-amplify/ui-react";
import {
  Container,
  ExpandableSection,
  Flashbar,
  Icon,
  SpaceBetween,
  TextContent,
} from "@cloudscape-design/components";
import { SendJsonMessage } from "react-use-websocket/dist/lib/types";
import { MessageRendererProps } from ".";
import { useQueryWithTokens } from "../../../utils/api/WebSocket";
import styles from "../chat.module.scss";
import ExpandableSectionWithDivider from "../ExpandableSectionWithDivider";
import ResultRenderer from "../ResultRenderer";
import { ChatBotAnswerItem, ChatBotMessageType, QUERY_INTENT } from "../types";
import EntitySelect from "./EntitySelect";
import { useI18n } from "../../../utils/i18n";

const AiMessage: React.FC<
  MessageRendererProps<{
    type: ChatBotMessageType.AI;
    content: ChatBotAnswerItem;
  }>
> = ({ message, sendJsonMessage }) => {
  const { queryWithWS } = useQueryWithTokens();
  const { t } = useI18n();
  
  if (!message?.content) return <>{t('chat.noMessage')}</>;
  const { content } = message;

  return (
    <Container className={styles.answer_area_container}>
      <SpaceBetween size="s">
        {!Object.entries(content.error_log).length ? null : (
          <ExpandableSectionWithDivider
            variant="footer"
            defaultExpanded
            headerText={t('chat.resultTypes.errorLog')}
          >
            <SpaceBetween size="s">
              {Object.entries(content.error_log).map(([k, v], idx) => (
                <Flashbar
                  key={idx}
                  items={[
                    {
                      type: "warning",
                      dismissible: false,
                      content: `[ ${k} ] ${v}`,
                      id: k,
                    },
                  ]}
                />
              ))}
            </SpaceBetween>
          </ExpandableSectionWithDivider>
        )}

        <AiMessageRenderer
          content={content}
          sendJsonMessage={sendJsonMessage}
        />

        {content.suggested_question?.length > 0 ? (
          <ExpandableSection
            variant="footer"
            defaultExpanded
            headerText={t('chat.suggestedQuestions')}
          >
            <div className={styles.questions_grid}>
              {content.suggested_question.map((query, kid) => (
                <AmplifyBtn
                  key={kid}
                  size="small"
                  className={styles.button}
                  onClick={() => {
                    queryWithWS({ query, sendJsonMessage });
                  }}
                >
                  {query}
                </AmplifyBtn>
              ))}
            </div>
          </ExpandableSection>
        ) : null}
      </SpaceBetween>
    </Container>
  );
};

export type IPropsAiMessageRenderer = {
  content: ChatBotAnswerItem;
  sendJsonMessage: SendJsonMessage;
};

function AiMessageRenderer({
  content,
  sendJsonMessage,
}: IPropsAiMessageRenderer) {
  const { t } = useI18n();
  
  try {
    switch (content.query_intent) {
      case QUERY_INTENT.entity_select:
        return <EntitySelect {...{ content, sendJsonMessage }} />;

      case QUERY_INTENT.normal_search:
        return (
          <ResultRenderer
            query={content.query}
            query_intent={content.query_intent}
            result={content.sql_search_result}
            query_rewrite={content.query_rewrite}
          />
        );

      case QUERY_INTENT.reject_search:
        return <div style={{ whiteSpace: "pre-line" }}>{t('chat.rejectSearch')}</div>;

      case QUERY_INTENT.agent_search:
        // 检查是否有任务结果
        if (!content.agent_search_result?.agent_sql_search_result?.length) {
          return <div>{t('chat.resultTypes.noResult')}</div>;
        }
        
        return (
          <SpaceBetween size="l">
            {/* 遍历每个子任务 */}
            {content.agent_search_result.agent_sql_search_result.map(
              (cnt, idx) => {
                // 如果没有SQL结果数据，跳过这个任务
                if (!cnt.sql_search_result?.sql_data?.length) {
                  return null;
                }
                
                return (
                  <SpaceBetween key={idx} size={"s"}>
                    {/* 隐藏子任务查询描述 */}
                    {/* 只显示表格和图表，不显示SQL和反馈 */}
                    <div>
                      <SpaceBetween size="xxl">
                        {/* 表格数据 - 只显示一次 */}
                        <ExpandableSectionWithDivider
                          variant="footer"
                          defaultExpanded
                          headerText={t('chat.resultTypes.tableTitle')}
                        >
                          <ResultRenderer
                            query={cnt.sub_task_query}
                            query_intent={content.query_intent}
                            result={cnt.sql_search_result}
                            query_rewrite={content.query_rewrite}
                            showOnlyTable={true}
                          />
                        </ExpandableSectionWithDivider>

                        {/* 图表数据 - 只在有图表时显示 */}
                        {(cnt.sql_search_result.data_show_type !== "table" || 
                          (cnt.sql_search_result.data_show_type === "table" && 
                           cnt.sql_search_result.sql_data_chart?.length > 0)) && (
                          <ExpandableSectionWithDivider
                            variant="footer"
                            defaultExpanded
                            headerText={t('chat.resultTypes.chartTitle')}
                          >
                            <ResultRenderer
                              query={cnt.sub_task_query}
                              query_intent={content.query_intent}
                              result={cnt.sql_search_result}
                              query_rewrite={content.query_rewrite}
                              showOnlyChart={true}
                            />
                          </ExpandableSectionWithDivider>
                        )}
                      </SpaceBetween>
                    </div>
                    <Divider />
                  </SpaceBetween>
                );
              }
            ).filter(Boolean)} {/* 过滤掉null项 */}

            {/* 隐藏SQL显示 */}

            {content.agent_search_result.agent_summary ? (
              <ExpandableSection
                variant="footer"
                defaultExpanded
                headerText={t('chat.resultTypes.insightsTitle')}
              >
                <div style={{ whiteSpace: "pre-line", padding: "8px 18px" }}>
                  {content.agent_search_result.agent_summary}
                </div>
              </ExpandableSection>
            ) : null}
          </SpaceBetween>
        );

      case QUERY_INTENT.knowledge_search:
        return (
          <div style={{ whiteSpace: "pre-line" }}>
            {content.knowledge_search_result.knowledge_response}
          </div>
        );

      case QUERY_INTENT.ask_in_reply:
        return (
          <div style={{ whiteSpace: "pre-line" }}>
            {content.ask_rewrite_result.query_rewrite}
          </div>
        );

      default:
        return (
          <div style={{ whiteSpace: "pre-line" }}>
            {t('chat.resultError')}
          </div>
        );
    }
  } catch (error) {
    console.error("Error rendering AI message:", error);
    return (
      <div style={{ whiteSpace: "pre-line" }}>
        {t('chat.error')}
      </div>
    );
  }
}

export default AiMessage;
