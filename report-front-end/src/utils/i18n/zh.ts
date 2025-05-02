export default {
  common: {
    newChat: "新建对话",
    compact: "紧凑模式",
    comfortable: "舒适模式",
    userInfo: "用户信息",
    username: "用户名",
    userId: "用户ID",
    loginExpiration: "登录过期时间",
    signOut: "退出登录"
  },
  chat: {
    noMessage: "没有消息",
    placeholder: "输入您的问题...",
    send: "发送",
    confirmClear: "确定要清除当前会话的所有消息吗？",
    moreSuggestions: "更多建议",
    lessSuggestions: "收起建议",
    resultTypes: {
      noResult: "没有结果",
      noChartData: "没有可用的图表数据",
      tableTitle: "表格数据",
      chartTitle: "图表",
      insightsTitle: "数据洞察",
      sqlTitle: "SQL 查询",
      upvote: "👍 有帮助",
      downvote: "👎 需改进",
      errorLog: "错误日志",
      agentTasks: "任务拆解",
      task: "任务",
      taskSteps: "步骤",
      parsingError: "解析任务数据时出错，显示原始内容："
    },
    feedback: {
      downvoteTitle: "反馈问题",
      answer: "SQL 查询",
      feedbackForm: "反馈表单",
      errorCategory: "错误类别 *",
      errorDescription: "错误描述 *",
      correctSql: "正确的 SQL 参考",
      submit: "提交",
      emptyError: "请填写错误描述",
      descPlaceholder: "请简要描述遇到的错误",
      sqlPlaceholder: "如果您知道正确的 SQL 查询，请在此提供"
    },
    table: {
      noMatches: "没有匹配项",
      noResults: "没有找到符合条件的结果",
      matches: "个匹配项",
      search: "搜索",
      clearFilter: "清除筛选条件",
      nextPage: "下一页",
      previousPage: "上一页",
      pageLabel: "页码"
    },
    loadingHistory: "加载历史记录中...",
    historyLoadError: "加载历史记录失败",
    error: "发生错误，请重试",
    rejectSearch: "抱歉，我无法回答这个问题。请尝试询问与数据相关的问题。",
    resultError: "处理结果时出错",
    connectionError: "连接错误，请检查网络并重试",
    jsonParseError: "解析消息失败",
    suggestedQuestions: "推荐问题",
    statusMessages: {
      agentsqltask_1generating: "正在生成任务1的SQL查询...",
      agentsqltask_2generating: "正在生成任务2的SQL查询...",
      agentsqltask_3generating: "正在生成任务3的SQL查询...",
      agentTaskGenerating: "正在生成任务SQL查询...",
      generatingSql: "正在生成SQL查询...",
      executingSql: "正在执行SQL查询...",
      analyzingData: "正在分析数据...",
      generatingResponse: "正在生成回复...",
      // Knowledge search 状态消息
      queryRewrite: "查询重写",
      queryIntentAnalyse: "查询意图分析",
      entityInfoRetrieval: "实体信息检索",
      qaInfoRetrieval: "问答信息检索",
      databaseSqlExecution: "数据库SQL执行",
      generatingDataInsights: "正在生成数据洞察",
      generatingSuggestedQuestions: "正在生成推荐问题",
      dataVisualization: "数据可视化",
      agentTaskSplit: "任务拆分",
      knowledgeSearchIntent: "知识搜索意图"
    },
    queryProcess: {
      queryRewrite: "查询重写",
      queryIntent: "查询意图分析",
      agentTaskSplit: "任务拆分"
    }
  },
  sideNav: {
    newChat: "新建对话",
    renameChat: "重命名对话",
    deleteChat: "删除对话",
    yes: "是",
    no: "否"
  },
  topNav: {
    switchToChinese: "切换到中文",
    switchToEnglish: "切换到英文"
  },
  configs: {
    configurations: "配置",
    llmModel: "LLM 模型",
    dataProfile: "数据配置文件",
    loadingModels: "加载模型中...",
    loadingProfiles: "加载配置文件中...",
    nowViewingProfile: "当前查看的数据配置文件：",
    queryConfig: "查询配置",
    intentRecognition: "意图识别",
    complexQuery: "复杂查询",
    modelSuggestion: "模型建议",
    answerWithInsights: "回答包含洞察",
    contextWindow: "上下文窗口",
    modelConfig: "模型配置",
    temperature: "温度",
    topP: "Top P",
    maxLength: "最大长度",
    topK: "Top K",
    save: "保存",
    configSaved: "配置已保存"
  }
};
