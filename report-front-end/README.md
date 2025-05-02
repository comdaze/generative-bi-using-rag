# Generative BI Using RAG - Frontend Application

[中文版本](#基于rag的生成式商业智能-前端应用)

## Project Overview
This is a sophisticated web application that provides a conversational interface for business intelligence (BI) analysis using generative AI and Retrieval-Augmented Generation (RAG) technology. The application allows users to query business data using natural language and receive insights, visualizations, and SQL explanations.

## Core Features

1. **Natural Language to SQL Conversion**
   - Users can ask business questions in natural language
   - The system converts these questions to SQL queries
   - SQL queries are executed against databases to retrieve relevant data
   - Users can see the generated SQL for transparency

2. **Interactive Data Visualization**
   - Multiple chart types supported (bar, line, pie)
   - Dynamic visualization of query results
   - Ability to customize chart axes and parameters
   - Table view for raw data examination

3. **Conversational AI Interface**
   - Chat-based interface for natural interaction
   - Session management for maintaining conversation context
   - Suggested follow-up questions based on previous queries
   - Support for complex, multi-step analytical queries

4. **Advanced Analytics Features**
   - Data insights generation from query results
   - Support for different query intents (normal search, knowledge search, agent search)
   - Entity selection for disambiguation
   - Feedback mechanism for result improvement

5. **Multi-language Support**
   - Complete bilingual interface (English and Chinese)
   - Language detection based on browser settings
   - Persistent language preference storage
   - Extensible framework for adding more languages

## Technical Architecture

1. **Frontend Framework**
   - React with TypeScript for type safety
   - Vite as the build tool for fast development
   - Redux for state management
   - React Router for navigation

2. **UI Components**
   - AWS Cloudscape Design System for consistent AWS-style UI
   - Responsive design for different screen sizes
   - Markdown rendering for formatted text responses
   - Syntax highlighting for SQL code

3. **Authentication & Security**
   - Multiple authentication methods supported:
     - AWS Cognito
     - OIDC (OpenID Connect)
     - Azure AD
     - SSO (Single Sign-On)
   - Token-based authentication with refresh capability
   - Secure API communication

4. **Communication**
   - WebSocket for real-time chat communication
   - RESTful API for data retrieval and management
   - Error handling and reconnection logic

5. **Containerization**
   - Docker support for consistent deployment
   - Environment variable configuration for different deployments

## Integration Points

1. **Backend Services**
   - Connects to a backend service for natural language processing
   - WebSocket API for real-time query processing
   - REST API for session management and history

2. **Authentication Services**
   - Integration with various identity providers
   - Token management and refresh logic

## Development Features

1. **Internationalization (i18n)**
   - Context-based translation system
   - Support for English and Chinese
   - Extensible translation framework

2. **Error Handling**
   - Comprehensive error boundary implementation
   - User-friendly error messages
   - Logging for debugging

3. **Configuration Management**
   - Environment-based configuration
   - Feature flags (e.g., SQL display toggle)

---

# 基于RAG的生成式商业智能-前端应用

## 项目概述
这是一个复杂的Web应用程序，它利用生成式AI和检索增强生成（RAG）技术为商业智能（BI）分析提供对话式界面。该应用程序允许用户使用自然语言查询业务数据，并获取洞察、可视化和SQL解释。

## 核心功能

1. **自然语言转SQL转换**
   - 用户可以用自然语言提出业务问题
   - 系统将这些问题转换为SQL查询
   - SQL查询在数据库上执行以检索相关数据
   - 用户可以看到生成的SQL以保证透明度

2. **交互式数据可视化**
   - 支持多种图表类型（柱状图、折线图、饼图）
   - 查询结果的动态可视化
   - 能够自定义图表轴和参数
   - 提供原始数据表格视图

3. **对话式AI界面**
   - 基于聊天的界面实现自然交互
   - 会话管理以维持对话上下文
   - 基于先前查询的建议后续问题
   - 支持复杂的多步分析查询

4. **高级分析功能**
   - 从查询结果生成数据洞察
   - 支持不同的查询意图（普通搜索、知识搜索、代理搜索）
   - 实体选择以消除歧义
   - 结果改进的反馈机制

5. **多语言支持**
   - 完整的双语界面（英文和中文）
   - 基于浏览器设置的语言检测
   - 持久的语言偏好存储
   - 可扩展的框架以添加更多语言

## 技术架构

1. **前端框架**
   - 使用TypeScript的React以确保类型安全
   - Vite作为快速开发的构建工具
   - Redux用于状态管理
   - React Router用于导航

2. **UI组件**
   - AWS Cloudscape设计系统，提供一致的AWS风格UI
   - 适应不同屏幕尺寸的响应式设计
   - Markdown渲染用于格式化文本响应
   - SQL代码的语法高亮

3. **认证与安全**
   - 支持多种认证方法：
     - AWS Cognito
     - OIDC（OpenID Connect）
     - Azure AD
     - SSO（单点登录）
   - 具有刷新能力的基于令牌的认证
   - 安全的API通信

4. **通信**
   - WebSocket用于实时聊天通信
   - RESTful API用于数据检索和管理
   - 错误处理和重连逻辑

5. **容器化**
   - Docker支持一致部署
   - 不同部署的环境变量配置

## 集成点

1. **后端服务**
   - 连接到自然语言处理的后端服务
   - 用于实时查询处理的WebSocket API
   - 用于会话管理和历史的REST API

2. **认证服务**
   - 与各种身份提供商集成
   - 令牌管理和刷新逻辑

## 开发特性

1. **国际化(i18n)**
   - 基于上下文的翻译系统
   - 支持英文和中文
   - 可扩展的翻译框架

2. **错误处理**
   - 全面的错误边界实现
   - 用户友好的错误消息
   - 用于调试的日志记录

3. **配置管理**
   - 基于环境的配置
   - 功能标志（例如，SQL显示切换）
