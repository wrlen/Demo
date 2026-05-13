# 文档机器人 - 前卫设计前端

本项目包含两个前端界面选项：

## 1. Streamlit 前端 (传统方式)
- 文件路径: `doc-robot/frontend/app.py`
- 基于 Streamlit 的传统界面
- 适用于快速原型和开发调试

## 2. 前卫设计 HTML 前端 (现代化方式)
- 文件路径: `doc-robot/frontend/avant-garde-ui.html`
- 完全重新设计的现代化界面
- 具备前卫美学和交互体验

## 前卫设计特性

### 视觉设计
- 使用深色背景和霓虹色渐变 (青色到洋红色)
- 几何形状和模糊效果创造层次感
- 现代化字体搭配 (Space Grotesk 和 Inter)
- 响应式设计，适配不同屏幕尺寸

### 交互体验
- 鼠标移动时的视差效果
- 平滑的悬停动画和过渡效果
- 卡片式界面设计
- 动态加载状态和反馈

### 功能特性
- 三种核心模式切换：智能问答、文档更新、用户反馈
- 实时数据交互和反馈
- 直观的用户界面设计

## 使用方式

### 方式一：Streamlit 前端
```bash
streamlit run doc-robot/frontend/app.py
```

### 方式二：HTML 前端
直接在浏览器中打开 `doc-robot/frontend/avant-garde-ui.html` 文件即可使用。

## 开发说明

前端代码遵循以下原则：
1. 使用纯 HTML/CSS/JavaScript 实现，无需额外依赖
2. 与后端 API 保持兼容，使用相同的接口格式
3. 采用现代化的 CSS 技术 (CSS Variables, Flexbox, Grid)
4. 支持响应式设计和无障碍访问