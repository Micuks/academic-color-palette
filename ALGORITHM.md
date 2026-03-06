# 🎨 学术配色推荐器 - AI 配色算法详解

## 📋 目录

1. [算法概述](#算法概述)
2. [核心原理](#核心原理)
3. [实现细节](#实现细节)
4. [配色风格](#配色风格)
5. [API 接口](#api-接口)
6. [示例展示](#示例展示)

---

## 算法概述

### 设计理念

**从"机械生成"到"AI 创作"**

传统的配色算法通常基于色相环理论，通过数学公式生成颜色。这种方法虽然科学，但缺乏创意和情感，每天生成的配色风格单一、乏味。

我们的新算法将配色创作完全交给 AI，让 AI 根据日期、季节、节日等因素，设计出富有创意和情感的配色方案。

### 核心优势

| 传统算法 | AI 配色算法 |
|---------|-----------|
| ❌ 色相环均匀分布 | ✅ 多样化配色理论 |
| ❌ 风格单一 | ✅ 风格多变（自然、情感、文化、节日） |
| ❌ 缺乏情感 | ✅ 富有诗意和意境 |
| ❌ 机械命名 | ✅ AI 生成诗意名称 |
| ❌ 固定模式 | ✅ 每天不同主题 |

---

## 核心原理

### 1. 日期驱动

算法根据日期信息生成配色主题：

```python
from datetime import datetime

date_obj = datetime.strptime(date_str, '%Y-%m-%d')
month = date_obj.month
day = date_obj.day
weekday = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][date_obj.weekday()]
```

### 2. 季节判断

根据月份判断季节，为配色提供主题方向：

```python
if month in [3, 4, 5]:
    season = "春季"
    season_desc = "万物复苏，生机盎然"
elif month in [6, 7, 8]:
    season = "夏季"
    season_desc = "热情奔放，色彩斑斓"
elif month in [9, 10, 11]:
    season = "秋季"
    season_desc = "金风送爽，层林尽染"
else:
    season = "冬季"
    season_desc = "宁静致远，素雅清新"
```

### 3. AI 生成

使用 DeepSeek v3.2 模型生成配色方案：

```python
payload = {
    "model": "deepseek-v3.2",
    "messages": [
        {
            "role": "system",
            "content": "你是一位专业的配色设计师，擅长根据日期、季节、节日设计多样化的配色方案。"
        },
        {
            "role": "user",
            "content": prompt
        }
    ],
    "max_tokens": 800,
    "temperature": 0.9  # 提高温度，增加多样性
}
```

---

## 实现细节

### 主函数：generate_daily_palette()

```python
def generate_daily_palette():
    """生成每日配色（AI 完全生成）"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 调用 AI 生成完整配色方案
    try:
        ai_result = call_ai_for_full_palette(today)
        if ai_result:
            return ai_result
    except Exception as e:
        print(f"[每日配色] AI 生成失败: {e}")
    
    # 如果 AI 失败，返回默认配色
    return {
        'name': '今日配色',
        'date': today,
        'description': '精心搭配的配色方案',
        'colors': [
            {'hex': '#FF6B6B', 'name': '珊瑚红'},
            {'hex': '#4ECDC4', 'name': '青碧'},
            {'hex': '#45B7D1', 'name': '天青'},
            {'hex': '#96CEB4', 'name': '薄荷绿'},
            {'hex': '#FFEAA7', 'name': '柠檬黄'}
        ],
        'usage': ['🎨 平面设计', '📱 UI设计', '🏠 室内设计', '👗 时尚设计'],
        'festivals': []
    }
```

### AI 调用函数：call_ai_for_full_palette()

```python
def call_ai_for_full_palette(date_str):
    """调用 AI 生成完整配色方案（包括颜色值）"""
    try:
        # 解析日期信息
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        month = date_obj.month
        day = date_obj.day
        weekday = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][date_obj.weekday()]
        
        # 判断季节
        if month in [3, 4, 5]:
            season = "春季"
            season_desc = "万物复苏，生机盎然"
        elif month in [6, 7, 8]:
            season = "夏季"
            season_desc = "热情奔放，色彩斑斓"
        elif month in [9, 10, 11]:
            season = "秋季"
            season_desc = "金风送爽，层林尽染"
        else:
            season = "冬季"
            season_desc = "宁静致远，素雅清新"
        
        # 构建 Prompt
        prompt = f"""你是一位专业的配色设计师。请为今天（{date_str}，{season}，{weekday}）设计一套配色方案。

日期信息：
- 日期：{date_str}
- 季节：{season}（{season_desc}）
- 星期：{weekday}

请根据日期、季节、星期的特点，设计一套有创意的配色方案。配色风格要多样化，可以是：
- 自然风景系（森林、海洋、日落、星空等）
- 情感表达系（温暖、冷静、活力、神秘等）
- 文化艺术系（中国风、现代简约、复古怀旧等）
- 节日主题系（如果有特殊节日）

请以 JSON 格式返回，格式如下：
{{
  "palette-name": "配色名称（2-6个字，有创意，不要制式命名）",
  "colors": [
    {{"hex": "#RRGGBB", "name": "颜色名称（2-4个字，诗意）"}},
    {{"hex": "#RRGGBB", "name": "颜色名称"}},
    {{"hex": "#RRGGBB", "name": "颜色名称"}},
    {{"hex": "#RRGGBB", "name": "颜色名称"}},
    {{"hex": "#RRGGBB", "name": "颜色名称"}}
  ],
  "description": "配色介绍（1-2句话，描述配色的感觉或意境）",
  "usage": ["使用建议1", "使用建议2", "使用建议3", "使用建议4"]
}}

重要要求：
1. palette-name 要有创意，不要用"XX交响曲"、"XX印象"、"XX之韵"等制式命名
2. colors 必须是 5 个颜色，每个颜色包含 hex 和 name
3. hex 必须是有效的 HEX 颜色码（如 #FF6B6B）
4. name 要根据颜色实际色相、亮度生成诗意的名称（2-4个字）
5. 配色风格要多样化，不要每天都是类似的风格
6. 颜色之间要协调，可以是：
   - 同色系渐变
   - 互补色对比
   - 三角配色
   - 分裂互补
   - 四角配色
   - 自由搭配"""

        # 调用 AI API
        payload = {
            "model": "deepseek-v3.2",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位专业的配色设计师，擅长根据日期、季节、节日设计多样化的配色方案。你的配色风格多变，从自然风景到情感表达，从文化艺术到节日主题，都能驾驭。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 800,
            "temperature": 0.9  # 提高温度，增加多样性
        }

        response = requests.post(AI_API_URL, json=payload, headers=headers, timeout=60)

        if response.status_code == 200:
            result = response.json()
            ai_message = result['choices'][0]['message']['content']
            
            # 解析 JSON
            import json
            import re
            
            # 提取 JSON 部分
            json_match = re.search(r'\{[\s\S]*\}', ai_message)
            if json_match:
                json_str = json_match.group()
                ai_result = json.loads(json_str)
                
                # 验证返回格式
                if 'palette-name' in ai_result and 'colors' in ai_result:
                    # 验证颜色格式
                    colors = []
                    for c in ai_result['colors']:
                        if 'hex' in c and 'name' in c:
                            # 验证 HEX 格式
                            hex_color = c['hex'].upper()
                            if re.match(r'^#[0-9A-F]{6}$', hex_color):
                                colors.append({
                                    'hex': hex_color,
                                    'name': c['name']
                                })
                    
                    if len(colors) == 5:
                        return {
                            'name': ai_result.get('palette-name', '今日配色'),
                            'date': date_str,
                            'description': ai_result.get('description', '精心搭配的配色方案'),
                            'colors': colors,
                            'usage': ai_result.get('usage', ['🎨 平面设计', '📱 UI设计', '🏠 室内设计', '👗 时尚设计']),
                            'festivals': []
                        }
        
        return None

    except Exception as e:
        print(f"[每日配色] 错误: {e}")
        return None
```

---

## 配色风格

### 1. 自然风景系

以自然景观为灵感，捕捉大自然的色彩：

- **森林**：深绿、浅绿、棕色、土黄
- **海洋**：深蓝、浅蓝、青色、白色
- **日落**：橙色、红色、紫色、金色
- **星空**：深蓝、紫色、银色、黑色

### 2. 情感表达系

以情感为主题，通过色彩传达情绪：

- **温暖**：红色、橙色、黄色、粉色
- **冷静**：蓝色、青色、灰色、白色
- **活力**：亮黄、亮橙、亮绿、亮粉
- **神秘**：紫色、深蓝、黑色、金色

### 3. 文化艺术系

以文化艺术为灵感，融合传统与现代：

- **中国风**：朱红、青绿、墨黑、米白
- **现代简约**：黑白灰、低饱和度色彩
- **复古怀旧**：棕色、米色、暗红、墨绿
- **波普艺术**：高饱和度色彩、对比强烈

### 4. 节日主题系

以节日为主题，营造节日氛围：

- **春节**：红色、金色、黄色
- **中秋**：金黄、深蓝、白色
- **圣诞**：红色、绿色、白色、金色
- **情人节**：粉色、红色、白色

---

## API 接口

### 获取每日配色

**请求**：
```http
GET /api/daily-palette
```

**响应**：
```json
{
  "success": true,
  "palette": {
    "name": "破晓桃枝",
    "date": "2026-03-05",
    "description": "以清早桃林为意象，捕捉初春薄雾中花枝初绽、新绿暗涌的过渡瞬间，冷暖交融间蕴涵周四的沉静与期待。",
    "colors": [
      {"hex": "#F8F3E6", "name": "晨雾纱"},
      {"hex": "#E8B4B8", "name": "早樱颊"},
      {"hex": "#6A994E", "name": "新萝青"},
      {"hex": "#3C6E71", "name": "潭影碧"},
      {"hex": "#2F3E46", "name": "墨枝痕"}
    ],
    "usage": [
      "春季品牌视觉系统主色调",
      "文创产品渐变包装",
      "室内软装过渡季节搭配",
      "数字界面深色模式点缀方案"
    ],
    "festivals": []
  }
}
```

---

## 示例展示

### 示例 1：破晓桃枝（2026-03-05，春季，周四）

**配色名称**：破晓桃枝 🌸

**颜色**：
- **晨雾纱** (#F8F3E6) - 浅米色，清晨薄雾的颜色
- **早樱颊** (#E8B4B8) - 浅粉色，初绽樱花
- **新萝青** (#6A994E) - 嫩绿色，新生的绿意
- **潭影碧** (#3C6E71) - 青绿色，潭水的倒影
- **墨枝痕** (#2F3E46) - 深灰绿色，墨色的枝干

**描述**：以清早桃林为意象，捕捉初春薄雾中花枝初绽、新绿暗涌的过渡瞬间，冷暖交融间蕴涵周四的沉静与期待。

**使用建议**：
- 春季品牌视觉系统主色调
- 文创产品渐变包装
- 室内软装过渡季节搭配
- 数字界面深色模式点缀方案

---

## 技术栈

- **后端**：Python Flask
- **AI 模型**：DeepSeek v3.2（华为云 API）
- **配色理论**：色相环、互补色、三角配色等
- **缓存机制**：内存缓存（每日更新）

---

## 未来改进

1. **节日数据库**：集成节日 API，自动识别节日
2. **天气数据**：根据天气调整配色风格
3. **用户偏好**：学习用户喜好，个性化推荐
4. **配色历史**：保存历史配色，避免重复
5. **配色评分**：用户评分，优化算法

---

**更新时间**：2026-03-05
**版本**：v2.0（AI 驱动）