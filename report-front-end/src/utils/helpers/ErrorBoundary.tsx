import React, { Component, ErrorInfo, ReactNode } from 'react';
import { useI18n } from '../i18n';
import toast from 'react-hot-toast';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

// 创建一个包装组件来使用 hooks
const ErrorFallback = () => {
  const { t } = useI18n();
  return (
    <div style={{ 
      padding: '20px', 
      margin: '20px', 
      backgroundColor: '#f8d7da', 
      color: '#721c24',
      borderRadius: '5px',
      textAlign: 'center' 
    }}>
      <h3>{t('chat.error')}</h3>
      <p>{t('chat.resultError')}</p>
      <button 
        onClick={() => window.location.reload()}
        style={{
          padding: '8px 16px',
          backgroundColor: '#dc3545',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        刷新页面
      </button>
    </div>
  );
};

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(_: Error): State {
    // 更新 state 使下一次渲染能够显示降级后的 UI
    return { hasError: true };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
    toast.error('应用发生错误，请刷新页面重试');
  }

  public render() {
    if (this.state.hasError) {
      return <ErrorFallback />;
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
