import { UseAuthenticator } from "@aws-amplify/ui-react-core";
import { useEffect, useState } from "react";
import { Toaster } from "react-hot-toast";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { v4 as uuid } from "uuid";
import "./app.scss";
import BaseAppLayout from "./components/BaseAppLayout";
import PanelConfigs from "./components/PanelConfigs";
import { PanelSideNav } from "./components/PanelSideNav";
import { Session } from "./components/PanelSideNav/types";
import SectionChat from "./components/SectionChat";
import TopNav from "./components/TopNav";
import { GlobalContext } from "./hooks/useGlobalContext";
import useUnauthorized from "./hooks/useUnauthorized";
import { useI18n } from "./utils/i18n";
import ErrorBoundary from "./utils/helpers/ErrorBoundary";

export type SignOut = UseAuthenticator["signOut"];

const App: React.FC = () => {
  useUnauthorized();
  return (
    <ErrorBoundary>
      <div style={{ height: "100%" }}>
        <BrowserRouter>
          <Toaster />
          <TopNav />
          <div style={{ height: "56px", backgroundColor: "#000716" }}>&nbsp;</div>
          <div>
            <Routes>
              <Route index path="/" element={<Playground />} />
            </Routes>
          </div>
        </BrowserRouter>
      </div>
    </ErrorBoundary>
  );
};

export default App;

function Playground() {
  const { t } = useI18n();
  const [toolsHide, setToolsHide] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState("");
  
  // 使用 useEffect 初始化会话，确保 t 函数已经准备好
  useEffect(() => {
    const initialSession = {
      session_id: uuid(),
      title: t('common.newChat'),
      messages: [],
    };
    setSessions([initialSession]);
    setCurrentSessionId(initialSession.session_id);
  }, [t]);

  // 监听语言变化，更新会话标题
  useEffect(() => {
    const handleLanguageChange = () => {
      setSessions(prev => {
        return prev.map(session => {
          // 只更新默认标题的会话
          if (session.title === "New Chat" || session.title === "新建对话") {
            return {
              ...session,
              title: t('common.newChat')
            };
          }
          return session;
        });
      });
    };
    
    window.addEventListener('languageChanged', handleLanguageChange);
    return () => {
      window.removeEventListener('languageChanged', handleLanguageChange);
    };
  }, [t]);

  if (sessions.length === 0 || !currentSessionId) {
    return null; // 等待初始化完成
  }

  return (
    <GlobalContext.Provider
      value={{
        sessions,
        setSessions,
        currentSessionId,
        setCurrentSessionId,
        isSearching,
        setIsSearching,
      }}
    >
      <BaseAppLayout
        navigation={<PanelSideNav />}
        content={<SectionChat {...{ toolsHide, setToolsHide }} />}
        tools={<PanelConfigs setToolsHide={setToolsHide} />}
        toolsHide={toolsHide}
        setToolsHide={setToolsHide}
      />
    </GlobalContext.Provider>
  );
}
