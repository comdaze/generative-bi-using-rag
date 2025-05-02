# 为Generative BI项目添加中英文切换功能

## 实现概述 | Implementation Overview

为了使Generative BI项目支持中英文切换功能，我们进行了以下修改：
To enable language switching between Chinese and English in the Generative BI project, we have made the following modifications:

1. 创建了语言配置文件 `language_config.py`，包含中英文翻译字典
   Created a language configuration file `language_config.py` containing translation dictionaries for Chinese and English
2. 在应用程序中实现了语言选择器和会话状态管理
   Implemented a language selector and session state management in the application
3. 使用 `get_text()` 函数替换了所有硬编码的文本
   Replaced all hardcoded text with the `get_text()` function
4. 更新了UI组件以支持多语言显示
   Updated UI components to support multilingual display

## 技术实现 | Technical Implementation

### 1. 语言配置文件 | Language Configuration File

`/application/config_files/language_config.py` 文件包含了一个名为 `translations` 的字典，其中存储了所有UI元素的中英文翻译。该文件还提供了 `get_text()` 函数，用于根据指定的键和语言代码获取相应的翻译文本。

The `/application/config_files/language_config.py` file contains a dictionary named `translations` that stores Chinese and English translations for all UI elements. The file also provides a `get_text()` function to retrieve the appropriate translation text based on a specified key and language code.

```python
# 示例代码 | Sample code
def get_text(key, language):
    """
    Get the translated text for a given key and language.
    
    Args:
        key (str): The translation key
        language (str): The language code ('en' or 'zh')
        
    Returns:
        str: The translated text
    """
    if language not in translations:
        language = 'en'  # Default to English
    
    return translations[language].get(key, translations['en'].get(key, key))
```

### 2. 会话状态管理 | Session State Management

在 `Index.py` 中，我们使用 Streamlit 的会话状态（session state）来存储和管理用户的语言选择：

In `Index.py`, we use Streamlit's session state to store and manage the user's language selection:

```python
# 如果会话状态中没有语言设置，则初始化为英文
# Initialize language preference in session state if not already set
if 'language' not in st.session_state:
    st.session_state['language'] = 'en'

# 添加语言选择器
# Add language selector
language_options = {'English': 'en', '中文': 'zh'}
selected_language = st.selectbox(
    "Language / 语言",
    options=list(language_options.keys()),
    index=0 if st.session_state['language'] == 'en' else 1
)
# 当语言选择改变时更新会话状态
# Update language in session state when changed
if language_options[selected_language] != st.session_state['language']:
    st.session_state['language'] = language_options[selected_language]
    st.rerun()

# 获取当前语言
# Get current language
lang = st.session_state['language']
```

### 3. 多语言UI实现 | Multilingual UI Implementation

在所有页面中，我们使用 `get_text()` 函数替换了硬编码的文本，以支持多语言显示：

In all pages, we replaced hardcoded text with the `get_text()` function to support multilingual display:

```python
# 示例：使用get_text()函数获取翻译文本
# Example: Using the get_text() function to get translated text
st.header(get_text('login_title', lang))
username = st.text_input(get_text('username', lang))
password = st.text_input(get_text('password', lang), type="password")
submit_button = st.form_submit_button(get_text('login_button', lang))
```

### 4. 前端实现 | Frontend Implementation

对于React前端部分，我们可以使用i18next或类似的国际化库来实现语言切换功能。前端需要：

For the React frontend part, we can use i18next or a similar internationalization library to implement language switching. The frontend needs to:

1. 存储用户的语言选择（localStorage或Redux）
   Store the user's language selection (localStorage or Redux)
2. 提供语言切换组件
   Provide a language switching component
3. 使用翻译函数替换硬编码文本
   Replace hardcoded text with translation functions

```javascript
// 示例前端代码 | Sample frontend code
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t, i18n } = useTranslation();
  
  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
  };

  return (
    <div>
      <button onClick={() => changeLanguage('en')}>English</button>
      <button onClick={() => changeLanguage('zh')}>中文</button>
      <h1>{t('welcome_title')}</h1>
      <p>{t('assistant_intro')}</p>
    </div>
  );
}
```

## 使用方法 | Usage Instructions

1. 在登录页面或主界面选择语言（English/中文）
   Select a language (English/中文) on the login page or main interface
2. 系统会记住用户的语言选择，并在所有页面应用该语言
   The system will remember the user's language selection and apply it across all pages
3. 用户可以随时切换语言，无需重新登录
   Users can switch languages at any time without needing to log in again

## 扩展建议 | Extension Suggestions

1. 添加更多语言支持
   Add support for more languages
   - 在 `language_config.py` 中的 `translations` 字典中添加新的语言键值对
     Add new language key-value pairs to the `translations` dictionary in `language_config.py`
   - 更新语言选择器以包含新语言
     Update the language selector to include the new languages

2. 实现语言偏好持久化
   Implement language preference persistence
   - 使用数据库或cookies存储用户的语言偏好
     Use a database or cookies to store the user's language preference
   - 在用户登录时自动应用其首选语言
     Automatically apply the user's preferred language when they log in

3. 添加自动语言检测
   Add automatic language detection
   - 基于用户的浏览器设置或IP地址自动检测首选语言
     Automatically detect the preferred language based on the user's browser settings or IP address

4. 优化翻译工作流程
   Optimize the translation workflow
   - 使用翻译管理工具来简化翻译过程
     Use translation management tools to streamline the translation process
   - 实现自动化翻译更新机制
     Implement automated translation update mechanisms

## 结论 | Conclusion

通过实现中英文切换功能，Generative BI项目现在可以服务于更广泛的用户群体，提高了产品的可访问性和用户体验。该实现方法具有良好的可扩展性，可以轻松添加更多语言支持。

By implementing the Chinese-English language switching feature, the Generative BI project can now serve a wider user base, improving the product's accessibility and user experience. The implementation method has good scalability and can easily accommodate additional language support.
