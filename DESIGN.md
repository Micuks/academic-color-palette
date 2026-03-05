# 每日配色推荐 - Dribbble 风格设计文档

## 设计原则

参考 Dribbble 的设计风格：
- 卡片式布局，干净清爽
- 白色背景为主
- 大图片展示，图片占主要空间
- 简洁的元信息
- 微妙的阴影和圆角
- 悬停显示更多信息

## 设计方案

### 布局结构

```
┌─────────────────────────────────────────────────┐
│  今日配色推荐                                    │
│  破晓桃枝                                        │
│  2026年3月5日 星期四                             │
├─────────────────────────────────────────────────┤
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐       │
│  │     │ │     │ │     │ │     │ │     │       │
│  │     │ │     │ │     │ │     │ │     │       │
│  │     │ │     │ │     │ │     │ │     │       │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘       │
│  晨雾纱  早樱颊  新萝青  潭影碧  墨枝痕          │
│  #F8F3E6 #E8B4B8 #6A994E #3C6E71 #2F3E46       │
├─────────────────────────────────────────────────┤
│  以清早桃林为意象，捕捉初春薄雾中花枝初绽、      │
│  新绿暗涌的过渡瞬间，冷暖交融间蕴涵周四的        │
│  沉静与期待。                                    │
├─────────────────────────────────────────────────┤
│  🎨 平面设计  📱 UI设计  🏠 室内设计            │
├─────────────────────────────────────────────────┤
│  [预览图表效果]  [复制所有颜色]                  │
└─────────────────────────────────────────────────┘
```

### 设计细节

#### 1. 卡片容器
- 背景：白色 (#FFFFFF)
- 圆角：16px
- 阴影：0 4px 20px rgba(0, 0, 0, 0.08)
- 内边距：32px
- 最大宽度：800px
- 居中显示

#### 2. 标题区域
- "今日配色推荐"：小标签，灰色 (#6B7280)，12px，字间距 1px
- 配色名称：大标题，黑色 (#111827)，32px，粗体
- 日期：灰色 (#9CA3AF)，14px

#### 3. 颜色展示区域
- 5 个颜色块横向排列
- 每个颜色块：
  - 宽度：120px
  - 高度：160px
  - 圆角：12px
  - 阴影：0 2px 8px rgba(0, 0, 0, 0.1)
  - 悬停：上移 4px，阴影增强
- 颜色名称和 HEX 值显示在下方
  - 名称：14px，黑色 (#111827)
  - HEX：12px，灰色 (#6B7280)，等宽字体

#### 4. 描述区域
- 字体：16px，行高 1.6
- 颜色：深灰色 (#374151)
- 背景：浅灰色 (#F9FAFB)
- 内边距：16px
- 圆角：8px

#### 5. 使用建议区域
- 标签式设计
- 背景：浅灰色 (#F3F4F6)
- 圆角：20px
- 内边距：8px 16px
- 字体：14px

#### 6. 操作按钮区域
- 主按钮：
  - 背景：黑色 (#111827)
  - 文字：白色，14px
  - 圆角：8px
  - 内边距：12px 24px
  - 悬停：背景变深
- 次按钮：
  - 背景：白色
  - 边框：1px solid #E5E7EB
  - 文字：黑色，14px
  - 圆角：8px
  - 内边距：12px 24px
  - 悬停：背景变浅灰色

### 响应式设计

#### 桌面端（> 768px）
- 颜色块：5 列，120px 宽度
- 卡片：居中，最大宽度 800px

#### 移动端（≤ 768px）
- 颜色块：3 列，自适应宽度
- 卡片：全宽，内边距 20px
- 标题：24px
- 按钮：全宽

### 动画效果

1. **颜色块悬停**
   - 上移 4px
   - 阴影增强：0 8px 16px rgba(0, 0, 0, 0.15)
   - 过渡时间：0.2s

2. **按钮悬停**
   - 背景色变化
   - 过渡时间：0.2s

3. **卡片加载**
   - 淡入效果
   - 过渡时间：0.3s

## 技术实现

### CSS 变量

```css
:root {
  --color-primary: #111827;
  --color-secondary: #6B7280;
  --color-text: #374151;
  --color-border: #E5E7EB;
  --color-bg: #F9FAFB;
  --color-white: #FFFFFF;
  
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
  
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 20px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.15);
  
  --transition: 0.2s ease;
}
```

### HTML 结构

```html
<div class="daily-palette-card">
  <div class="palette-header">
    <span class="palette-badge">今日配色推荐</span>
    <h2 class="palette-title">破晓桃枝</h2>
    <p class="palette-date">2026年3月5日 星期四</p>
  </div>
  
  <div class="palette-colors">
    <div class="color-block" style="background: #F8F3E6;">
      <div class="color-info">
        <span class="color-name">晨雾纱</span>
        <span class="color-hex">#F8F3E6</span>
      </div>
    </div>
    <!-- 其他颜色块 -->
  </div>
  
  <div class="palette-description">
    以清早桃林为意象...
  </div>
  
  <div class="palette-usage">
    <span class="usage-tag">🎨 平面设计</span>
    <span class="usage-tag">📱 UI设计</span>
    <span class="usage-tag">🏠 室内设计</span>
  </div>
  
  <div class="palette-actions">
    <button class="btn-primary">预览图表效果</button>
    <button class="btn-secondary">复制所有颜色</button>
  </div>
</div>
```

## 实现步骤

1. 创建 CSS 样式
2. 修改 HTML 结构
3. 添加响应式设计
4. 添加动画效果
5. 测试和调整