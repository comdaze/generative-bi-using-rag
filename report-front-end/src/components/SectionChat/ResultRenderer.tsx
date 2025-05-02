import { useCollection } from "@cloudscape-design/collection-hooks";
import {
  Box,
  Button,
  ColumnLayout,
  CopyToClipboard,
  ExpandableSection,
  Form,
  FormField,
  Header,
  Modal,
  Pagination,
  Select,
  SpaceBetween,
  Table,
  Textarea,
  TextContent,
  TextFilter,
} from "@cloudscape-design/components";
import { ReactNode, useState } from "react";
import toast from "react-hot-toast";
import { useSelector } from "react-redux";
import SyntaxHighlighter from "react-syntax-highlighter";
import useGlobalContext from "../../hooks/useGlobalContext";
import { postUserFeedback } from "../../utils/api/API";
import { SQL_DISPLAY } from "../../utils/constants";
import { UserState } from "../../utils/helpers/types";
import ExpandableSectionWithDivider from "./ExpandableSectionWithDivider";
import ChartRenderer from "./ChartRenderer";
import { FeedBackType, SQLSearchResult } from "./types";
import { Divider } from "@aws-amplify/ui-react";
import { useI18n } from "../../utils/i18n";

const Expandable = {
  Default: ExpandableSection,
  WithDivider: ExpandableSectionWithDivider,
};
interface SQLResultProps {
  query: string;
  query_rewrite?: string;
  query_intent: string;
  result?: SQLSearchResult;
  showOnlyTable?: boolean;
  showOnlyChart?: boolean;
  showOnlySql?: boolean;
}

interface AgentTask {
  description: string;
  steps: string[];
}

const OPTIONS_ERROR_CAT = (
  [
    "SQL语法错误",
    "表名错误",
    "列名错误",
    "查询值错误",
    "计算逻辑错误",
    "其他错误",
  ] as const
).map((v) => ({ value: v, label: v }));

/**
 * 渲染Agent任务组件
 * 解析并显示Agent任务的详细信息
 */
const RenderAgentTasks = ({ sqlGenProcess, isStyled = false }: { sqlGenProcess: string, isStyled?: boolean }) => {
  const { t } = useI18n();
  
  if (!sqlGenProcess || !sqlGenProcess.startsWith('[{')) {
    return <div>{sqlGenProcess.replace(/^\n+/, "")}</div>;
  }

  try {
    // 处理可能的Unicode转义问题
    let processedJson = sqlGenProcess;
    
    // 如果是Unicode转义的字符串，先尝试解码
    if (sqlGenProcess.includes('\\u')) {
      try {
        // 尝试将Unicode转义序列转换为实际字符
        processedJson = JSON.parse(`"${sqlGenProcess.replace(/"/g, '\\"')}"`);
      } catch (e) {
        // 如果解码失败，使用原始字符串
        processedJson = sqlGenProcess;
      }
    }
    
    // 解析 JSON 字符串
    const tasks: AgentTask[] = JSON.parse(processedJson);
    
    if (!tasks || !Array.isArray(tasks) || tasks.length === 0) {
      return <div>{sqlGenProcess.replace(/^\n+/, "")}</div>;
    }
    
    if (!isStyled) {
      // 简单版本
      return (
        <div>
          <h4>{t('chat.resultTypes.agentTasks')}</h4>
          {tasks.map((task, index) => (
            <div key={index} style={{ marginBottom: '20px' }}>
              <h5>{`${t('chat.resultTypes.task')} ${index + 1}: ${task.description}`}</h5>
              <ul>
                {task.steps && Array.isArray(task.steps) && task.steps.map((step, stepIndex) => (
                  <li key={stepIndex}>{step}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      );
    }
    
    // 样式化版本
    return (
      <div className="agent-tasks-container" style={{ marginTop: '12px' }}>
        <h4 style={{ 
          color: "#0972d3", 
          marginBottom: "16px", 
          fontSize: '16px',
          fontWeight: '600',
          borderBottom: '1px solid #e9ebed',
          paddingBottom: '8px'
        }}>
          {t('chat.resultTypes.agentTasks')}
        </h4>
        <div>
          {tasks.map((task, index) => (
            <div key={index} style={{ 
              marginBottom: '16px', 
              padding: '12px', 
              borderRadius: '8px',
              backgroundColor: '#f2f3f3',
              border: '1px solid #d1d5db'
            }}>
              <h5 style={{ 
                color: "#16191f", 
                marginTop: 0, 
                marginBottom: '8px',
                fontSize: '14px',
                fontWeight: '600'
              }}>
                {`${t('chat.resultTypes.task')} ${index + 1}: ${task.description}`}
              </h5>
              <div style={{ fontSize: '13px', color: '#414d5c', marginBottom: '4px' }}>
                {t('chat.resultTypes.taskSteps')}:
              </div>
              <ul style={{ 
                margin: 0, 
                paddingLeft: '20px',
                fontSize: '13px',
                color: '#414d5c'
              }}>
                {task.steps && Array.isArray(task.steps) && task.steps.map((step, stepIndex) => (
                  <li key={stepIndex} style={{ marginBottom: '4px' }}>{step}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    );
  } catch (error) {
    console.error("Error parsing agent tasks:", error);
    return (
      <div>
        <div style={{ color: '#d91515', marginBottom: '8px' }}>
          {t('chat.resultTypes.parsingError')}
        </div>
        <div style={{ whiteSpace: "pre-wrap", overflowWrap: "break-word" }}>
          {sqlGenProcess.replace(/^\n+/, "")}
        </div>
      </div>
    );
  }
};

/**
 * 渲染SQL反馈按钮组件
 * 处理用户对SQL结果的反馈（点赞/踩）
 */
const RenderFeedbackButtons = ({ 
  query, 
  query_rewrite, 
  query_intent, 
  sql, 
  selectedIcon, 
  setSelectedIcon, 
  sendingFeedback, 
  setSendingFeedback, 
  setIsDownvoteModalVisible 
}: { 
  query: string;
  query_rewrite?: string;
  query_intent: string;
  sql: string;
  selectedIcon?: FeedBackType;
  setSelectedIcon: (icon?: FeedBackType) => void;
  sendingFeedback: boolean;
  setSendingFeedback: (loading: boolean) => void;
  setIsDownvoteModalVisible: (visible: boolean) => void;
}) => {
  const { t } = useI18n();
  const { currentSessionId } = useGlobalContext();
  const queryConfig = useSelector((state: UserState) => state.queryConfig);
  const userInfo = useSelector((state: UserState) => state.userInfo);

  return (
    <ColumnLayout columns={2}>
      {[FeedBackType.UPVOTE, FeedBackType.DOWNVOTE].map(
        (feedback_type, index) => {
          const isUpvote = feedback_type === FeedBackType.UPVOTE;
          const isSelected =
            (isUpvote && selectedIcon === FeedBackType.UPVOTE) ||
            (!isUpvote && selectedIcon === FeedBackType.DOWNVOTE);
          return (
            <Button
              key={index.toString()}
              fullWidth
              loading={sendingFeedback}
              disabled={sendingFeedback}
              variant={isSelected ? "primary" : undefined}
              onClick={async () => {
                if (isUpvote) {
                  setSendingFeedback(true);
                  try {
                    const res = await postUserFeedback({
                      feedback_type,
                      data_profiles: queryConfig.selectedDataPro,
                      query: query_rewrite || query,
                      query_intent,
                      query_answer: sql,
                      session_id: currentSessionId,
                      user_id: userInfo.userId,
                    });
                    if (res === true) {
                      setSelectedIcon(
                        isUpvote
                          ? FeedBackType.UPVOTE
                          : FeedBackType.DOWNVOTE
                      );
                    } else {
                      setSelectedIcon(undefined);
                    }
                  } catch (error) {
                    console.error(error);
                  } finally {
                    setSendingFeedback(false);
                  }
                } else {
                  // is downvoting
                  setIsDownvoteModalVisible(true);
                }
              }}
            >
              {isUpvote ? t('chat.resultTypes.upvote') : t('chat.resultTypes.downvote')}
            </Button>
          );
        }
      )}
    </ColumnLayout>
  );
};

/**
 * 渲染SQL代码块组件
 * 显示SQL代码并提供复制功能
 */
const RenderSqlCode = ({ sql, showLineNumbers = false }: { sql: string, showLineNumbers?: boolean }) => {
  return (
    <div>
      <SyntaxHighlighter 
        language="sql"
        showLineNumbers={showLineNumbers}
        wrapLines={showLineNumbers}
      >
        {sql.replace(/^\n+/, "").replace(/\n+$/, "")}
      </SyntaxHighlighter>
      <CopyToClipboard>
        {sql}
      </CopyToClipboard>
    </div>
  );
};

/**
 * The display panel of Table, Chart, SQL etc.
 */
export default function ResultRenderer({
  query,
  query_rewrite,
  query_intent,
  result,
  showOnlyTable = false,
  showOnlyChart = false,
  showOnlySql = false,
}: SQLResultProps) {
  const [selectedIcon, setSelectedIcon] = useState<FeedBackType>();
  const [sendingFeedback, setSendingFeedback] = useState(false);
  const [isDownvoteModalVisible, setIsDownvoteModalVisible] = useState(false);
  // Downvote modal hooks
  const [errDesc, setErrDesc] = useState("");
  const [errCatOpt, setErrCatOpt] = useState(OPTIONS_ERROR_CAT[0]);
  const [correctSQL, setCorrectSQL] = useState("");
  const [isValidating, setIsValidating] = useState(false);
  const { t } = useI18n();
  const queryConfig = useSelector((state: UserState) => state.queryConfig);
  const userInfo = useSelector((state: UserState) => state.userInfo);
  const { currentSessionId } = useGlobalContext();

  if (!result) return <div>{t('chat.resultTypes.noResult')}</div>;

  const sql_data = result.sql_data ?? [];
  const sql_data_chart = result.sql_data_chart ?? [];
  let headers: any = [];
  let content: any = [];
  if (sql_data.length > 0) {
    // convert data from server to generate table
    headers = sql_data[0].map((header: string) => {
      return {
        header: header,
        cell: (item: { [x: string]: any }) => item[header],
      };
    });
    const items = sql_data.slice(1, sql_data.length);
    content = items.map((item) => {
      const map: any = new Map(
        item.map((value, index) => {
          return [sql_data[0][index], value];
        })
      );
      return Object.fromEntries(map);
    });
  }

  // 只显示表格
  if (showOnlyTable && sql_data.length > 0) {
    return <DataTable distributions={content} header={headers} />;
  }

  // 只显示图表
  if (showOnlyChart) {
    // 如果有非表格类型的图表数据
    if (result.data_show_type !== "table" && sql_data.length > 0) {
      return (
        <ChartRenderer
          data_show_type={result.data_show_type}
          sql_data={result.sql_data}
        />
      );
    } 
    // 如果是表格类型但有专门的图表数据
    else if (result.data_show_type === "table" && sql_data_chart.length > 0) {
      return (
        <ChartRenderer
          data_show_type={sql_data_chart[0].chart_type}
          sql_data={sql_data_chart[0].chart_data}
        />
      );
    }
    // 如果没有图表数据
    return <div>{t('chat.resultTypes.noChartData')}</div>;
  }

  // 只显示SQL和反馈
  if (showOnlySql && SQL_DISPLAY === "yes") {
    return (
      <SpaceBetween size="xl">
        <RenderSqlCode sql={result.sql} />
        {/* 隐藏Agent任务显示 */}
        <RenderFeedbackButtons
          query={query}
          query_rewrite={query_rewrite}
          query_intent={query_intent}
          sql={result.sql}
          selectedIcon={selectedIcon}
          setSelectedIcon={setSelectedIcon}
          sendingFeedback={sendingFeedback}
          setSendingFeedback={setSendingFeedback}
          setIsDownvoteModalVisible={setIsDownvoteModalVisible}
        />
      </SpaceBetween>
    );
  }

  // 默认显示全部内容
  return (
    <div>
      <SpaceBetween size="xxl">
        {sql_data.length > 0 ? (
          <Expandable.Default
            variant="footer"
            defaultExpanded
            headerText={t('chat.resultTypes.tableTitle')}
          >
            <DataTable distributions={content} header={headers} />
          </Expandable.Default>
        ) : null}

        {result.data_show_type !== "table" && sql_data.length > 0 ? (
          <Expandable.Default
            variant="footer"
            defaultExpanded
            headerText={t('chat.resultTypes.chartTitle')}
          >
            <ChartRenderer
              data_show_type={result.data_show_type}
              sql_data={result.sql_data}
            />
          </Expandable.Default>
        ) : null}

        {result.data_show_type === "table" && sql_data_chart.length > 0 ? (
          <Expandable.Default
            variant="footer"
            defaultExpanded
            headerText={t('chat.resultTypes.chartTitle')}
          >
            <ChartRenderer
              data_show_type={sql_data_chart[0].chart_type}
              sql_data={sql_data_chart[0].chart_data}
            />
          </Expandable.Default>
        ) : null}

        {result?.data_analyse ? (
          <ExpandableSectionWithDivider
            withDivider={SQL_DISPLAY === "yes"}
            variant="footer"
            defaultExpanded
            headerText={t('chat.resultTypes.insightsTitle')}
          >
            <div style={{ whiteSpace: "pre-line" }}>{result.data_analyse}</div>
          </ExpandableSectionWithDivider>
        ) : null}

        {SQL_DISPLAY === "yes" && (
          <ExpandableSectionWithDivider
            withDivider={false}
            variant="footer"
            headerText={t('chat.resultTypes.sqlTitle')}
          >
            <SpaceBetween size="xl">
              <RenderSqlCode sql={result.sql} />
              {/* 隐藏Agent任务显示 */}
              <RenderFeedbackButtons
                query={query}
                query_rewrite={query_rewrite}
                query_intent={query_intent}
                sql={result.sql}
                selectedIcon={selectedIcon}
                setSelectedIcon={setSelectedIcon}
                sendingFeedback={sendingFeedback}
                setSendingFeedback={setSendingFeedback}
                setIsDownvoteModalVisible={setIsDownvoteModalVisible}
              />

              <Modal
                onDismiss={() => {
                  setIsDownvoteModalVisible(false);
                  setIsValidating(false);
                }}
                visible={isDownvoteModalVisible}
                header={t('chat.feedback.downvoteTitle')}
                footer={
                  <Box float="right">
                    <Button
                      variant="primary"
                      onClick={async () => {
                        setIsValidating(true);
                        if (!errDesc)
                          return toast.error(
                            t('chat.feedback.emptyError')
                          );
                        setSendingFeedback(true);
                        try {
                          const res = await postUserFeedback({
                            feedback_type: FeedBackType.DOWNVOTE,
                            data_profiles: queryConfig.selectedDataPro,
                            query: query_rewrite || query,
                            query_intent,
                            query_answer: result.sql,
                            error_description: errDesc,
                            session_id: currentSessionId,
                            user_id: userInfo.userId,
                            error_categories: errCatOpt.value,
                            correct_sql_reference: correctSQL,
                          });
                          if (res === true) {
                            setSelectedIcon(FeedBackType.DOWNVOTE);
                            setIsDownvoteModalVisible(false);
                          } else {
                            setSelectedIcon(undefined);
                          }
                        } catch (error) {
                          console.error(error);
                        } finally {
                          setSendingFeedback(false);
                          setIsValidating(false);
                        }
                      }}
                    >
                      {t('chat.feedback.submit')}
                    </Button>
                  </Box>
                }
              >
                <form onSubmit={(e) => e.preventDefault()}>
                  <Form>
                    <SpaceBetween direction="vertical" size="l">
                      <FormField label={t('chat.feedback.answer')}>
                        <RenderSqlCode sql={result.sql} showLineNumbers={true} />
                      </FormField>

                      <Divider label={t('chat.feedback.feedbackForm')} />
                      <FormField label={t('chat.feedback.errorCategory')}>
                        <Select
                          options={OPTIONS_ERROR_CAT}
                          selectedOption={errCatOpt}
                          onChange={({ detail }) =>
                            // options are fixed values, no need for type checking
                            setErrCatOpt(detail.selectedOption as any)
                          }
                        />
                      </FormField>
                      <FormField
                        label={t('chat.feedback.errorDescription')}
                        warningText={
                          isValidating &&
                          !errDesc &&
                          t('chat.feedback.emptyError')
                        }
                      >
                        <Textarea
                          placeholder={t('chat.feedback.descPlaceholder')}
                          value={errDesc}
                          onChange={({ detail }) => setErrDesc(detail.value)}
                        />
                      </FormField>
                      <FormField label={t('chat.feedback.correctSql')}>
                        <Textarea
                          onChange={({ detail }) => setCorrectSQL(detail.value)}
                          value={correctSQL}
                          placeholder={t('chat.feedback.sqlPlaceholder')}
                        />
                      </FormField>
                    </SpaceBetween>
                  </Form>
                </form>
              </Modal>
            </SpaceBetween>
          </ExpandableSectionWithDivider>
        )}
      </SpaceBetween>
    </div>
  );
}

const DataTable = ({
  distributions,
  header,
}: {
  distributions: [];
  header: [];
}) => {
  const { t } = useI18n();
  const [selectedItems, setSelectedItems] = useState<any[]>([]);
  const [currentPageIndex, setCurrentPageIndex] = useState(1);
  const [filteringText, setFilteringText] = useState("");
  const PAGE_SIZE = 10;

  const { items, filteredItemsCount, collectionProps, filterProps, paginationProps } =
    useCollection(distributions, {
      filtering: {
        empty: (
          <TextContent>
            <h3>{t('chat.table.noMatches')}</h3>
            <p>{t('chat.table.noResults')}</p>
          </TextContent>
        ),
        noMatch: (
          <TextContent>
            <h3>{t('chat.table.noMatches')}</h3>
            <p>{t('chat.table.noResults')}</p>
          </TextContent>
        ),
      },
      pagination: { pageSize: PAGE_SIZE },
      sorting: {},
      selection: {},
    });

  return (
    <Table
      {...collectionProps}
      resizableColumns
      header={
        <Header
          counter={
            selectedItems.length
              ? `(${selectedItems.length}/${distributions.length})`
              : `(${distributions.length})`
          }
          actions={
            <TextFilter
              {...filterProps}
              filteringText={filteringText}
              onChange={({ detail }) => setFilteringText(detail.filteringText)}
              countText={`${filteredItemsCount} ${t('chat.table.matches')}`}
              placeholder={t('chat.table.search')}
              clear={
                filteringText
                  ? {
                      ariaLabel: t('chat.table.clearFilter'),
                    }
                  : undefined
              }
            />
          }
        />
      }
      columnDefinitions={header}
      items={items}
      selectionType="multi"
      trackBy="name"
      selectedItems={selectedItems}
      onSelectionChange={({ detail }) =>
        setSelectedItems(detail.selectedItems)
      }
      pagination={
        <Pagination
          {...paginationProps}
          ariaLabels={{
            nextPageLabel: t('chat.table.nextPage'),
            previousPageLabel: t('chat.table.previousPage'),
            pageLabel: (pageNumber) => `${t('chat.table.pageLabel')} ${pageNumber}`,
          }}
          onChange={({ detail }) => {
            setCurrentPageIndex(detail.currentPageIndex);
          }}
          currentPageIndex={currentPageIndex}
        />
      }
    />
  );
};
