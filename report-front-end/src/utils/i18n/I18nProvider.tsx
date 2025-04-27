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
