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
