import { Button } from "@aws-amplify/ui-react";
import { Link, SpaceBetween } from "@cloudscape-design/components";
import { useEffect, useState } from "react";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";
import { getRecommendQuestions } from "../../utils/api/API";
import { useQueryWithTokens } from "../../utils/api/WebSocket";
import { useI18n } from "../../utils/i18n";
import styles from "./chat.module.scss";

export interface RecommendQuestionsProps {
  sendJsonMessage: SendJsonMessage;
}

export default function CustomQuestions({
  sendJsonMessage,
}: RecommendQuestionsProps) {
  const [showMoreQuestions, setShowMoreQuestions] = useState(false);
  const [questions, setQuestions] = useState<string[]>([]);
  const { queryWithWS, queryConfig } = useQueryWithTokens();
  const { t } = useI18n();

  useEffect(() => {
    const data_profile = queryConfig?.selectedDataPro;
    if (data_profile) {
      getRecommendQuestions(data_profile).then((data) => {
        setQuestions(data);
      });
    }
  }, [queryConfig?.selectedDataPro]);

  const queries = showMoreQuestions
    ? questions
    : questions?.slice(0, Math.min(3, questions.length));
  return (
    <div>
      {!queries?.length ? null : (
        <SpaceBetween size={"xxs"}>
          <div className={styles.questions_grid}>
            {queries?.map((query, idx) => (
              <Button
                key={idx}
                size="small"
                className={styles.button}
                onClick={() => {
                  queryWithWS({ query, sendJsonMessage });
                }}
              >
                {query}
              </Button>
            ))}
          </div>
          <div style={{ float: "right" }}>
            <Link onFollow={() => setShowMoreQuestions((prev) => !prev)}>
              <p className={styles.text}>
                {showMoreQuestions ? t('chat.lessSuggestions') : t('chat.moreSuggestions')}
              </p>
            </Link>
          </div>
        </SpaceBetween>
      )}
    </div>
  );
}
