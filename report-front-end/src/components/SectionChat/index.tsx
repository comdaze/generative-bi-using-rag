import { LoadingBar } from "@cloudscape-design/chat-components";
import {
  Box,
  SpaceBetween,
  Spinner,
  StatusIndicator,
} from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import useGlobalContext from "../../hooks/useGlobalContext";
import { getHistoryBySession, getSelectData } from "../../utils/api/API";
import { useCreateWssClient } from "../../utils/api/WebSocket";
import {
  ActionType,
  LLMConfigState,
  UserState,
} from "../../utils/helpers/types";
import ChatInput from "./ChatInput";
import MessageRenderer from "./MessageRenderer";
import styles from "./chat.module.scss";
import { ChatBotHistoryItem, WSResponseStatusMessageItem } from "./types";
import toast from "react-hot-toast";
import { Heading } from "@aws-amplify/ui-react";
import { useI18n } from "../../utils/i18n";
import ErrorBoundary from "../../utils/helpers/ErrorBoundary";

export default function SectionChat({
  setToolsHide,
  toolsHide,
}: {
  setToolsHide: Dispatch<SetStateAction<boolean>>;
  toolsHide: boolean;
}) {
  const [messageHistory, setMessageHistory] = useState<ChatBotHistoryItem[]>(
    []
  );
  const [isLoadingSessionHistory, setIsLoadingSessionHistory] = useState(false);

  const [statusMessage, setStatusMessage] = useState<WSResponseStatusMessageItem[]>([]);
  const { sessions, setSessions, currentSessionId, isSearching } =
    useGlobalContext();

  const sendJsonMessage = useCreateWssClient(setStatusMessage);

  const dispatch = useDispatch();
  const queryConfig = useSelector((state: UserState) => state.queryConfig);
  const userInfo = useSelector((state: UserState) => state.userInfo);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const { t } = useI18n();

  useEffect(() => {
    if (!queryConfig.selectedLLM || !queryConfig.selectedDataPro) {
      setLoadingProfile(true);
      try {
        getSelectData().then((response) => {
          if (!response) return;
          const { bedrock_model_ids, data_profiles } = response;
          const configInfo: LLMConfigState = { ...queryConfig };
          if (!queryConfig.selectedLLM && bedrock_model_ids?.length) {
            const defaultLLM = bedrock_model_ids[0];
            configInfo.selectedLLM = defaultLLM;
          }
          if (!queryConfig.selectedDataPro && data_profiles?.length) {
            const defaultProfile = data_profiles[0];
            configInfo.selectedDataPro = defaultProfile;
            toast.success(
              <div>
                Default data profile selected:
                <Heading>
                  <em>{defaultProfile}</em>
                </Heading>
              </div>,
              { duration: 8000 }
            );
          }
          dispatch({ type: ActionType.UpdateConfig, state: configInfo });
        });
      } catch (error) {
        console.warn("getSelectData error in useEffect init: ", error);
        toast.error(t('chat.error'));
      } finally {
        setLoadingProfile(false);
      }
    }
  }, [dispatch, queryConfig, t]);

  useEffect(() => {
    setIsLoadingSessionHistory(true);
    getHistoryBySession({
      session_id: currentSessionId,
      user_id: userInfo.userId,
      profile_name: queryConfig.selectedDataPro,
    })
      .then((data) => {
        if (!data) {
          setIsLoadingSessionHistory(false);
          return;
        }
        const { messages, session_id } = data;
        setSessions((prevList) => {
          return prevList.map((item) => {
            if (session_id === item.session_id) {
              setMessageHistory(messages);
              return { ...item, messages };
            }
            return item;
          });
        });
      })
      .catch((error) => {
        console.error("Error loading session history:", error);
        toast.error(t('chat.historyLoadError'));
      })
      .finally(() => {
        setIsLoadingSessionHistory(false);
      });
  }, [
    currentSessionId,
    queryConfig.selectedDataPro,
    setSessions,
    userInfo.userId,
    t
  ]);

  useEffect(() => {
    sessions.forEach((session) => {
      if (session.session_id === currentSessionId) {
        setMessageHistory(session.messages);
      }
    });
  }, [currentSessionId, sessions]);

  return (
    <ErrorBoundary>
      <section className={styles.chat_container}>
        <SpaceBetween size="xxs">
          {isLoadingSessionHistory || loadingProfile ? (
            <Box variant="h3" margin="xxl" padding="xxl">
              <Spinner /> {t('chat.loadingHistory')}
            </Box>
          ) : (
            <>
              {messageHistory?.map((message, idx) => {
                return (
                  <div key={idx}>
                    <MessageRenderer
                      message={message}
                      sendJsonMessage={sendJsonMessage}
                    />
                  </div>
                );
              })}

              {!isSearching ? null : (
                <div className={styles.status_container}>
                  <div style={{ position: "absolute", top: 0, width: "100%" }}>
                    <LoadingBar variant="gen-ai-masked" />
                  </div>
                  <SpaceBetween size="xxs">
                    {statusMessage?.length ? (
                      statusMessage.map((message, idx) => {
                        const displayMessage =
                          idx % 2 === 1 ? true : idx === statusMessage.length - 1;
                        
                        // Determine status indicator type
                        let statusType = "in-progress";
                        if (message.content.status === "end") {
                          statusType = "success";
                        } else if (message.content.status === "error") {
                          statusType = "error";
                        } else if (message.content.status === "rejected") {
                          statusType = "warning";
                        }
                        
                        // Format the message text for i18n lookup
                        const originalText = message.content.text;
                        
                        // 使用更可靠的方式处理状态消息的翻译
                        let translatedText;
                        
                        // 特殊处理Agent SQL Task消息
                        if (originalText.includes('Agent SQL Task')) {
                          if (originalText.includes('Task_1')) {
                            translatedText = t('chat.statusMessages.agentsqltask_1generating');
                          } else if (originalText.includes('Task_2')) {
                            translatedText = t('chat.statusMessages.agentsqltask_2generating');
                          } else if (originalText.includes('Task_3')) {
                            translatedText = t('chat.statusMessages.agentsqltask_3generating');
                          } else {
                            // 通用的Agent任务消息
                            translatedText = t('chat.statusMessages.agentTaskGenerating');
                          }
                        } 
                        // 处理Knowledge search状态消息
                        else if (originalText === 'Query Rewrite') {
                          translatedText = t('chat.statusMessages.queryRewrite');
                        }
                        else if (originalText === 'Query Intent Analyse') {
                          translatedText = t('chat.statusMessages.queryIntentAnalyse');
                        }
                        else if (originalText === 'Entity Info Retrieval') {
                          translatedText = t('chat.statusMessages.entityInfoRetrieval');
                        }
                        else if (originalText === 'QA Info Retrieval') {
                          translatedText = t('chat.statusMessages.qaInfoRetrieval');
                        }
                        else if (originalText === 'Database SQL Execution') {
                          translatedText = t('chat.statusMessages.databaseSqlExecution');
                        }
                        else if (originalText === 'Generating Data Insights') {
                          translatedText = t('chat.statusMessages.generatingDataInsights');
                        }
                        else if (originalText === 'Generating Suggested Questions') {
                          translatedText = t('chat.statusMessages.generatingSuggestedQuestions');
                        }
                        else if (originalText === 'Data Visualization') {
                          translatedText = t('chat.statusMessages.dataVisualization');
                        }
                        else if (originalText === 'Agent Task Split') {
                          translatedText = t('chat.statusMessages.agentTaskSplit');
                        }
                        else if (originalText === 'Knowledge Search Intent') {
                          translatedText = t('chat.statusMessages.knowledgeSearchIntent');
                        }
                        else if (originalText.includes('Generating SQL')) {
                          translatedText = t('chat.statusMessages.generatingSql');
                        } 
                        else if (originalText.includes('Executing SQL')) {
                          translatedText = t('chat.statusMessages.executingSql');
                        }
                        else if (originalText.includes('Analyzing data')) {
                          translatedText = t('chat.statusMessages.analyzingData');
                        }
                        else if (originalText.includes('Generating response')) {
                          translatedText = t('chat.statusMessages.generatingResponse');
                        }
                        else {
                          // 如果没有匹配的翻译，使用原始文本
                          translatedText = originalText;
                        }
                        
                        return displayMessage ? (
                          <StatusIndicator
                            key={idx}
                            type={statusType}
                          >
                            {translatedText}
                          </StatusIndicator>
                        ) : null;
                      })
                    ) : (
                      <Spinner />
                    )}
                  </SpaceBetween>
                </div>
              )}
            </>
          )}
        </SpaceBetween>

        <div className={styles.welcome_text}>
          {messageHistory?.length === 0 &&
            statusMessage?.length === 0 &&
            !isLoadingSessionHistory &&
            !loadingProfile && <center></center>}
        </div>

        <div className={styles.input_container}>
          <ChatInput
            toolsHide={toolsHide}
            setToolsHide={setToolsHide}
            messageHistory={messageHistory}
            setStatusMessage={setStatusMessage}
            sendJsonMessage={sendJsonMessage}
          />
        </div>
      </section>
    </ErrorBoundary>
  );
}
