# Internationalization (i18n) Implementation Guide

[中文版本](#国际化i18n实现指南)

## Overview

This document provides a detailed explanation of the internationalization (i18n) implementation in the Generative BI Using RAG frontend application. The application supports both English and Chinese languages with a seamless switching mechanism.

## Implementation Framework

The i18n system is built using React Context API, which provides a clean and efficient way to manage translations throughout the application without prop drilling. The implementation follows these key principles:

1. **Centralized Translation Management**: All translations are stored in separate language files
2. **Context-based Access**: Components access translations through a custom hook
3. **Persistent Language Preference**: User language choice is saved in localStorage
4. **Automatic Language Detection**: Default language is determined by browser settings
5. **Dynamic UI Updates**: UI components respond to language changes in real-time

## Key Components

### 1. Translation Files

**Location**: `/src/utils/i18n/en.ts` and `/src/utils/i18n/zh.ts`

These files contain all text strings used in the application, organized in a nested object structure:

**English Example (`en.ts`):**
```typescript
export default {
  common: {
    newChat: "New Chat",
    compact: "Compact Mode",
    comfortable: "Comfortable Mode",
    // ...other translations
  },
  chat: {
    noMessage: "No message",
    placeholder: "Type your question...",
    // ...other translations
  },
  // ...other categories
};
```

**Chinese Example (`zh.ts`):**
```typescript
export default {
  common: {
    newChat: "新建对话",
    compact: "紧凑模式",
    comfortable: "舒适模式",
    // ...other translations
  },
  chat: {
    noMessage: "没有消息",
    placeholder: "输入您的问题...",
    // ...other translations
  },
  // ...other categories
};
```

### 2. Context and Hook Definition

**Location**: `/src/utils/i18n/index.ts`

This file defines the React Context and a custom hook for accessing translations:

```typescript
import { createContext, useContext } from 'react';
import en from './en';
import zh from './zh';

export type Language = 'en' | 'zh';
export type TranslationKeys = typeof en;

export const translations = {
  en,
  zh,
};

export const getTranslation = (lang: Language) => {
  return translations[lang];
};

export interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string, fallback?: string) => string;
}

export const I18nContext = createContext<I18nContextType>({
  language: 'en',
  setLanguage: () => {},
  t: (key: string, fallback?: string) => fallback || key,
});

export const useI18n = () => useContext(I18nContext);

// Helper function to get nested translation by dot notation
export const getNestedTranslation = (obj: any, path: string, fallback?: string): string => {
  const keys = path.split('.');
  let result = obj;
  
  for (const key of keys) {
    if (result && typeof result === 'object' && key in result) {
      result = result[key];
    } else {
      return fallback || path; // Return fallback or key path if translation not found
    }
  }
  
  return result as string;
};
```

### 3. Context Provider

**Location**: `/src/utils/i18n/I18nProvider.tsx`

This component manages the language state and provides translation functions to the application:

```typescript
import React, { useState, useEffect, ReactNode, useCallback } from 'react';
import { I18nContext, Language, getTranslation, getNestedTranslation } from './index';

interface I18nProviderProps {
  children: ReactNode;
}

const LANGUAGE_KEY = 'app_language';

export const I18nProvider: React.FC<I18nProviderProps> = ({ children }) => {
  // Get saved language from localStorage or use browser language or default to English
  const getSavedLanguage = (): Language => {
    const savedLang = localStorage.getItem(LANGUAGE_KEY);
    if (savedLang === 'en' || savedLang === 'zh') {
      return savedLang;
    }
    
    // Try to use browser language
    const browserLang = navigator.language.toLowerCase();
    if (browserLang.startsWith('zh')) {
      return 'zh';
    }
    
    // Default to English
    return 'en';
  };

  const [language, setLanguageState] = useState<Language>(getSavedLanguage());
  
  const setLanguage = useCallback((lang: Language) => {
    localStorage.setItem(LANGUAGE_KEY, lang);
    setLanguageState(lang);
    document.documentElement.lang = lang;
    // Force re-render of components
    window.dispatchEvent(new Event('languageChanged'));
  }, []);
  
  // Function to get translation by key using dot notation (e.g., 'common.newChat')
  const t = useCallback((key: string, fallback?: string): string => {
    const currentTranslations = getTranslation(language);
    return getNestedTranslation(currentTranslations, key, fallback);
  }, [language]);
  
  // Set document language on initial load
  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);
  
  return (
    <I18nContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </I18nContext.Provider>
  );
};
```

## Implementation Steps

### Step 1: Provider Setup

The I18nProvider is added at the application root in `/src/main.tsx`:

```typescript
root.render(
  <React.StrictMode>
    <Provider store={userReduxStore}>
      <I18nProvider>
        {rootComponent}
      </I18nProvider>
    </Provider>
  </React.StrictMode>
);
```

### Step 2: Language Switching UI

A language toggle button is implemented in the top navigation bar in `/src/components/TopNav/index.tsx`:

```typescript
const toggleLanguage = () => {
  const newLang = language === 'en' ? 'zh' : 'en';
  setLanguage(newLang);
  console.log("Language changed to:", newLang);
};

// In the TopNavigation utilities array:
{
  type: "button",
  iconName: "globe",
  text: language === 'en' ? t('topNav.switchToChinese') : t('topNav.switchToEnglish'),
  ariaLabel: "LanguageSwitch",
  onClick: toggleLanguage,
}
```

### Step 3: Using Translations in Components

Components access translations using the `useI18n` hook:

```typescript
import { useI18n } from "../../utils/i18n";

function MyComponent() {
  const { t } = useI18n();
  
  return (
    <div>
      <h1>{t('common.newChat')}</h1>
      <p>{t('chat.placeholder')}</p>
    </div>
  );
}
```

### Step 4: Handling Language Changes

The application listens for language changes and updates components accordingly:

```typescript
// In app.tsx
useEffect(() => {
  const handleLanguageChange = () => {
    setSessions(prev => {
      return prev.map(session => {
        // Only update sessions with default titles
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
```

## Adding a New Language

To add support for a new language:

1. Create a new translation file (e.g., `/src/utils/i18n/fr.ts`) with the same structure as existing language files
2. Update the Language type in `/src/utils/i18n/index.ts`:
   ```typescript
   export type Language = 'en' | 'zh' | 'fr';
   ```
3. Add the new language to the translations object:
   ```typescript
   export const translations = {
     en,
     zh,
     fr,
   };
   ```
4. Update the language detection logic in `I18nProvider.tsx` to support the new language

## Conclusion

The i18n implementation in this application provides a robust and flexible way to support multiple languages. The use of React Context API ensures efficient state management, while the dot notation for translation keys allows for a clean and organized translation structure.

---

# 国际化(i18n)实现指南

## 概述

本文档详细介绍了基于RAG的生成式商业智能前端应用中的国际化(i18n)实现。该应用支持英文和中文两种语言，并提供无缝的语言切换机制。

## 实现框架

i18n系统使用React Context API构建，这提供了一种干净高效的方式来管理整个应用程序中的翻译，而无需进行属性传递。实现遵循以下关键原则：

1. **集中式翻译管理**：所有翻译存储在单独的语言文件中
2. **基于上下文的访问**：组件通过自定义钩子访问翻译
3. **持久化语言偏好**：用户语言选择保存在localStorage中
4. **自动语言检测**：默认语言由浏览器设置决定
5. **动态UI更新**：UI组件实时响应语言变化

## 关键组件

### 1. 翻译文件

**位置**：`/src/utils/i18n/en.ts` 和 `/src/utils/i18n/zh.ts`

这些文件包含应用程序中使用的所有文本字符串，组织在嵌套对象结构中：

**英文示例 (`en.ts`):**
```typescript
export default {
  common: {
    newChat: "New Chat",
    compact: "Compact Mode",
    comfortable: "Comfortable Mode",
    // ...其他翻译
  },
  chat: {
    noMessage: "No message",
    placeholder: "Type your question...",
    // ...其他翻译
  },
  // ...其他类别
};
```

**中文示例 (`zh.ts`):**
```typescript
export default {
  common: {
    newChat: "新建对话",
    compact: "紧凑模式",
    comfortable: "舒适模式",
    // ...其他翻译
  },
  chat: {
    noMessage: "没有消息",
    placeholder: "输入您的问题...",
    // ...其他翻译
  },
  // ...其他类别
};
```

### 2. 上下文和钩子定义

**位置**：`/src/utils/i18n/index.ts`

此文件定义了React上下文和用于访问翻译的自定义钩子：

```typescript
import { createContext, useContext } from 'react';
import en from './en';
import zh from './zh';

export type Language = 'en' | 'zh';
export type TranslationKeys = typeof en;

export const translations = {
  en,
  zh,
};

export const getTranslation = (lang: Language) => {
  return translations[lang];
};

export interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string, fallback?: string) => string;
}

export const I18nContext = createContext<I18nContextType>({
  language: 'en',
  setLanguage: () => {},
  t: (key: string, fallback?: string) => fallback || key,
});

export const useI18n = () => useContext(I18nContext);

// 使用点表示法获取嵌套翻译的辅助函数
export const getNestedTranslation = (obj: any, path: string, fallback?: string): string => {
  const keys = path.split('.');
  let result = obj;
  
  for (const key of keys) {
    if (result && typeof result === 'object' && key in result) {
      result = result[key];
    } else {
      return fallback || path; // 如果未找到翻译，则返回fallback或键路径
    }
  }
  
  return result as string;
};
```

### 3. 上下文提供器

**位置**：`/src/utils/i18n/I18nProvider.tsx`

此组件管理语言状态并向应用程序提供翻译功能：

```typescript
import React, { useState, useEffect, ReactNode, useCallback } from 'react';
import { I18nContext, Language, getTranslation, getNestedTranslation } from './index';

interface I18nProviderProps {
  children: ReactNode;
}

const LANGUAGE_KEY = 'app_language';

export const I18nProvider: React.FC<I18nProviderProps> = ({ children }) => {
  // 从localStorage获取保存的语言，或使用浏览器语言，或默认为英语
  const getSavedLanguage = (): Language => {
    const savedLang = localStorage.getItem(LANGUAGE_KEY);
    if (savedLang === 'en' || savedLang === 'zh') {
      return savedLang;
    }
    
    // 尝试使用浏览器语言
    const browserLang = navigator.language.toLowerCase();
    if (browserLang.startsWith('zh')) {
      return 'zh';
    }
    
    // 默认为英语
    return 'en';
  };

  const [language, setLanguageState] = useState<Language>(getSavedLanguage());
  
  const setLanguage = useCallback((lang: Language) => {
    localStorage.setItem(LANGUAGE_KEY, lang);
    setLanguageState(lang);
    document.documentElement.lang = lang;
    // 强制重新渲染组件
    window.dispatchEvent(new Event('languageChanged'));
  }, []);
  
  // 使用点表示法通过键获取翻译的函数（例如，'common.newChat'）
  const t = useCallback((key: string, fallback?: string): string => {
    const currentTranslations = getTranslation(language);
    return getNestedTranslation(currentTranslations, key, fallback);
  }, [language]);
  
  // 在初始加载时设置文档语言
  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);
  
  return (
    <I18nContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </I18nContext.Provider>
  );
};
```

## 实现步骤

### 步骤1：提供器设置

I18nProvider在应用程序根目录中的`/src/main.tsx`中添加：

```typescript
root.render(
  <React.StrictMode>
    <Provider store={userReduxStore}>
      <I18nProvider>
        {rootComponent}
      </I18nProvider>
    </Provider>
  </React.StrictMode>
);
```

### 步骤2：语言切换UI

在顶部导航栏`/src/components/TopNav/index.tsx`中实现了语言切换按钮：

```typescript
const toggleLanguage = () => {
  const newLang = language === 'en' ? 'zh' : 'en';
  setLanguage(newLang);
  console.log("Language changed to:", newLang);
};

// 在TopNavigation utilities数组中：
{
  type: "button",
  iconName: "globe",
  text: language === 'en' ? t('topNav.switchToChinese') : t('topNav.switchToEnglish'),
  ariaLabel: "LanguageSwitch",
  onClick: toggleLanguage,
}
```

### 步骤3：在组件中使用翻译

组件使用`useI18n`钩子访问翻译：

```typescript
import { useI18n } from "../../utils/i18n";

function MyComponent() {
  const { t } = useI18n();
  
  return (
    <div>
      <h1>{t('common.newChat')}</h1>
      <p>{t('chat.placeholder')}</p>
    </div>
  );
}
```

### 步骤4：处理语言变化

应用程序监听语言变化并相应地更新组件：

```typescript
// 在app.tsx中
useEffect(() => {
  const handleLanguageChange = () => {
    setSessions(prev => {
      return prev.map(session => {
        // 只更新具有默认标题的会话
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
```

## 添加新语言

要添加对新语言的支持：

1. 创建一个新的翻译文件（例如，`/src/utils/i18n/fr.ts`），结构与现有语言文件相同
2. 更新`/src/utils/i18n/index.ts`中的Language类型：
   ```typescript
   export type Language = 'en' | 'zh' | 'fr';
   ```
3. 将新语言添加到translations对象：
   ```typescript
   export const translations = {
     en,
     zh,
     fr,
   };
   ```
4. 更新`I18nProvider.tsx`中的语言检测逻辑以支持新语言

## 结论

该应用程序中的i18n实现提供了一种强大而灵活的方式来支持多种语言。使用React Context API确保了高效的状态管理，而翻译键的点表示法允许清晰和有组织的翻译结构。
