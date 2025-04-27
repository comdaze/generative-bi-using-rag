import {
  Button,
  ButtonDropdown,
  Header,
  SideNavigation,
  SpaceBetween,
} from "@cloudscape-design/components";
import { useCallback, useContext, useEffect, useState } from "react";
import { v4 as uuid } from "uuid";
import { GlobalContext } from "../../hooks/useGlobalContext";
import { Session } from "./types";
import { useI18n } from "../../utils/i18n";

export function PanelSideNav() {
  const {
    sessions,
    setSessions,
    currentSessionId,
    setCurrentSessionId,
    isSearching,
  } = useContext(GlobalContext);
  const { t } = useI18n();
  const [activeHref, setActiveHref] = useState("#/");
  const [deleteSessionId, setDeleteSessionId] = useState<string | null>(null);

  const onFollowHandler = useCallback(
    (event: CustomEvent) => {
      event.preventDefault();
      const href = event.detail.href;
      const sessionId = href.replace("#/", "");
      setActiveHref(href);
      setCurrentSessionId(sessionId);
    },
    [setCurrentSessionId]
  );

  const onCreateNewSession = useCallback(() => {
    const newSession: Session = {
      session_id: uuid(),
      title: t('common.newChat'),
      messages: [],
    };
    setSessions((prev) => [...prev, newSession]);
    setCurrentSessionId(newSession.session_id);
  }, [setSessions, setCurrentSessionId, t]);

  const onDeleteSession = useCallback(
    (sessionId: string) => {
      if (sessions.length === 1) {
        return;
      }
      setSessions((prev) => {
        const newSessions = prev.filter((s) => s.session_id !== sessionId);
        if (sessionId === currentSessionId) {
          setCurrentSessionId(newSessions[0].session_id);
        }
        return newSessions;
      });
      setDeleteSessionId(null);
    },
    [sessions.length, setSessions, currentSessionId, setCurrentSessionId]
  );

  const onRenameSession = useCallback(
    (sessionId: string, newTitle: string) => {
      setSessions((prev) => {
        return prev.map((s) => {
          if (s.session_id === sessionId) {
            return {
              ...s,
              title: newTitle,
            };
          }
          return s;
        });
      });
    },
    [setSessions]
  );

  useEffect(() => {
    if (currentSessionId) {
      setActiveHref(`#/${currentSessionId}`);
    }
  }, [currentSessionId]);

  // 监听语言变化，更新会话标题
  useEffect(() => {
    const handleLanguageChange = () => {
      // 强制重新渲染
      setSessions(prev => [...prev]);
    };
    
    window.addEventListener('languageChanged', handleLanguageChange);
    return () => {
      window.removeEventListener('languageChanged', handleLanguageChange);
    };
  }, [setSessions]);

  return (
    <SpaceBetween size="l">
      <div className="sidenav-header-container">
        <Button 
          className="new-chat-button"
          onClick={onCreateNewSession} 
          disabled={isSearching}
        >
          {t('sideNav.newChat')}
        </Button>
      </div>
      <SideNavigation
        activeHref={activeHref}
        onFollow={onFollowHandler}
        items={sessions.map((session) => {
          return {
            type: "link",
            text: session.title,
            href: `#/${session.session_id}`,
            info: deleteSessionId === session.session_id && (
              <SpaceBetween direction="horizontal" size="xs">
                <Button
                  variant="primary"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(session.session_id);
                  }}
                >
                  {t('sideNav.yes')}
                </Button>
                <Button
                  variant="normal"
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeleteSessionId(null);
                  }}
                >
                  {t('sideNav.no')}
                </Button>
              </SpaceBetween>
            ),
            actions: [
              <ButtonDropdown
                key="actions"
                items={[
                  {
                    id: "rename",
                    text: t('sideNav.renameChat'),
                    disabled: isSearching,
                  },
                  {
                    id: "delete",
                    text: t('sideNav.deleteChat'),
                    disabled: sessions.length === 1 || isSearching,
                  },
                ]}
                onItemClick={(e) => {
                  if (e.detail.id === "delete") {
                    setDeleteSessionId(session.session_id);
                  } else if (e.detail.id === "rename") {
                    const newTitle = prompt(
                      "Enter new title",
                      session.title
                    );
                    if (newTitle) {
                      onRenameSession(session.session_id, newTitle);
                    }
                  }
                }}
              />,
            ],
          };
        })}
      />
    </SpaceBetween>
  );
}
