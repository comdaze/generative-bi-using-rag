import { Dispatch, SetStateAction, useCallback } from "react";
import { useSelector } from "react-redux";
import useWebSocket from "react-use-websocket";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";
import { Session } from "../../components/PanelSideNav/types";
import {
  ChatBotMessageType,
  WSResponseQueryResult,
  WSResponseStatusMessageItem,
} from "../../components/SectionChat/types";
import useGlobalContext from "../../hooks/useGlobalContext";
import { AUTH_WITH_NOTHING, DEFAULT_QUERY_CONFIG } from "../constants";
import { dispatchUnauthorizedEvent } from "../helpers/tools";
import { UserState } from "../helpers/types";
import { getBearerTokenObj } from "./API";
import toast from "react-hot-toast";
import { useI18n } from "../i18n";

export function useCreateWssClient(
  setStatusMessage: Dispatch<SetStateAction<WSResponseStatusMessageItem[]>>
) {
  const { setIsSearching, setSessions } = useGlobalContext();
  const { t } = useI18n();
  const socketUrl = process.env.VITE_WEBSOCKET_URL as string;
  const { sendJsonMessage } = useWebSocket(socketUrl, {
    onOpen: (openMessage) =>
      console.log("websocket connection opened, ", openMessage),
    onClose: (closeMessage) => {
      console.error("websocket connection closed, ", closeMessage);
      setIsSearching(false); // 确保搜索状态被重置
    },
    onError: (errorMessage) => {
      console.error("websocket connection error, ", errorMessage);
      setIsSearching(false); // 确保搜索状态被重置
      toast.error(t('chat.connectionError')); // 使用国际化的错误消息
    },
    //Will attempt to reconnect on all close events, such as server shutting down
    shouldReconnect: () => true,
    onMessage: (message) => handleWebSocketMessage(message),
    heartbeat: true,
  });

  const handleWebSocketMessage = useCallback(
    (message: MessageEvent) => {
      const data = message?.data;
      console.log("Received WebSocketMessage: ", data);
      if (data === undefined) {
        console.warn('Received WS message.data === "undefined"');
        setIsSearching(false);
        return;
      }
      if (data === "pong") return;
      
      try {
        const messageJson: WSResponseStatusMessageItem | WSResponseQueryResult =
          JSON.parse(data);

        if (!AUTH_WITH_NOTHING) {
          if (messageJson.content?.["X-Status-Code"] === 401) {
            setIsSearching(false);
            return dispatchUnauthorizedEvent();
          } else if (messageJson.content?.["X-Status-Code"] === 200) {
            setIsSearching(false);
            // Do something extra here
          }
        }

        if (messageJson.content_type === "state") {
          // update status messages
          setStatusMessage((prevMsgs) => [
            ...prevMsgs,
            messageJson as WSResponseStatusMessageItem,
          ]);
        } else {
          // NOW: messageJson.content_type (MUST BE) === "end"
          setIsSearching(false);
          setStatusMessage([]);
          // update sessions
          setSessions((prevList: Session[]) => {
            return prevList.map((item) => {
              if (
                (messageJson as WSResponseQueryResult).session_id !==
                item.session_id
              ) {
                return item;
              } else {
                return {
                  session_id: item.session_id,
                  title: item.title,
                  messages: [
                    ...item.messages,
                    {
                      type: ChatBotMessageType.AI,
                      content: (messageJson as WSResponseQueryResult).content,
                    },
                  ],
                };
              }
            });
          });
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
        setIsSearching(false);
        toast.error(t('chat.jsonParseError'));
        setStatusMessage([]);
      }
    },
    [setIsSearching, setSessions, setStatusMessage, t]
  );

  return sendJsonMessage;
}

export type IWSQueryParams = {
  query: string;
  sendJsonMessage: SendJsonMessage;
  extraParams?: {
    query_rewrite?: string;
    previous_intent?: string;
    entity_user_select?: Record<string, Record<string, string>>;
    entity_retrieval?: unknown[];
  };
};
export const useQueryWithTokens = () => {
  const userInfo = useSelector((state: UserState) => state.userInfo);
  const queryConfig = useSelector((state: UserState) => state.queryConfig);
  const globalContext = useGlobalContext();
  const { currentSessionId, setSessions, setIsSearching } = globalContext;
  const { t } = useI18n();

  const queryWithWS = useCallback(
    ({ query, sendJsonMessage, extraParams = {} }: IWSQueryParams) => {
      try {
        setIsSearching(true);
        setSessions((prevList) => {
          return prevList.map((item) => {
            if (currentSessionId !== item.session_id) return item;
            return {
              ...item,
              title: item.title === "New Chat" || item.title === "新建对话" ? query : item.title,
              messages: item.messages.concat({
                type: ChatBotMessageType.Human,
                content: query,
              }),
            };
          });
        });
        const extraToken = !AUTH_WITH_NOTHING ? getBearerTokenObj() : {};
        const params = {
          query: query,
          bedrock_model_id:
            queryConfig.selectedLLM || DEFAULT_QUERY_CONFIG.selectedLLM,
          use_rag_flag: true,
          visualize_results_flag: true,
          intent_ner_recognition_flag: queryConfig.intentChecked,
          agent_cot_flag: queryConfig.complexChecked,
          profile_name:
            queryConfig.selectedDataPro || DEFAULT_QUERY_CONFIG.selectedDataPro,
          explain_gen_process_flag: true,
          gen_suggested_question_flag: queryConfig.modelSuggestChecked,
          answer_with_insights:
            queryConfig.answerInsightChecked ||
            DEFAULT_QUERY_CONFIG.answerInsightChecked,
          top_k: queryConfig.topK,
          top_p: queryConfig.topP,
          max_tokens: queryConfig.maxLength,
          temperature: queryConfig.temperature,
          context_window: queryConfig.contextWindow,
          session_id: currentSessionId,
          user_id: userInfo.userId,
          username: userInfo.username,
          ...extraParams,
          ...extraToken,
        };
        console.log("Send WebSocketMessage: ", params);
        sendJsonMessage(params);
      } catch (error) {
        console.error("Error sending WebSocket message:", error);
        setIsSearching(false);
        toast.error(t('chat.error'));
      }
    },
    [
      currentSessionId,
      queryConfig.answerInsightChecked,
      queryConfig.complexChecked,
      queryConfig.contextWindow,
      queryConfig.intentChecked,
      queryConfig.maxLength,
      queryConfig.modelSuggestChecked,
      queryConfig.selectedDataPro,
      queryConfig.selectedLLM,
      queryConfig.temperature,
      queryConfig.topK,
      queryConfig.topP,
      setIsSearching,
      setSessions,
      userInfo.userId,
      userInfo.username,
      t
    ]
  );
  return { queryWithWS, userInfo, queryConfig, ...globalContext };
};
