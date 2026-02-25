# 学术配色推荐器 (Academic Color Palette)

一个专为学术论文设计的配色方案推荐工具，帮助研究者选择美观且符合学术规范的配色方案。

## 🌟 功能特性

### 配色库
- 多种配色方案（类似色、互补色、三角配色、四角配色）
- 配色卡片展示
- 一键复制颜色代码
- 配色预览（4种学术论文图表）
- 筛选功能（按配色类型）

### 颜色分析
- 颜色选择器
- HEX颜色输入
- 亮度调节（0-100%）
- 配色方案推荐
- 每日配色推荐

### 工具箱
- AI配色咨询（集成AI模型）
- 随机配色生成
- 颜色格式转换

### 用户系统
- 用户注册（邮箱必填）
- 用户登录（支持用户名/邮箱登录）
- 个人配色管理
- 配色上传
- 点赞功能
- 管理员后台

## 🛠️ 技术栈

### 后端
- **框架：** Python Flask
- **数据库：** SQLite
- **认证：** JWT (Flask-JWT-Extended)
- **加密：** bcrypt

### 前端
- **语言：** 纯HTML/CSS/JavaScript
- **架构：** 单页应用（SPA）
- **UI：** 响应式设计

### 服务器
- **Web服务器：** Caddy
- **HTTPS：** 自动SSL证书
- **代理：** API反向代理

## 📦 安装部署

### 1. 克隆仓库
```bash
git clone https://github.com/yourusername/academic-color-palette.git
cd academic-color-palette
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境
```bash
# 设置数据库路径
export DB_PATH=/var/www/palette/database.db

# 设置JWT密钥
export JWT_SECRET_KEY=your-secret-key
```

### 4. 启动后端
```bash
python3 backend_server.py
```

### 5. 配置Caddy
```caddyfile
palette.micuks.click {
    root * /var/www/palette
    file_server
    reverse_proxy /api/* localhost:8890
    encode gzip
}
```

### 6. 启动Caddy
```bash
caddy run --config /etc/caddy/Caddyfile
```

## 🔐 默认账号

### 管理员
- 用户名：`admin`
- 密码：`admin123`

### 测试用户
- 用户名：`testuser2`
- 邮箱：`test2@example.com`
- 密码：`test123`

## 📊 数据库结构

### users表
```sql
- id: INTEGER PRIMARY KEY
- username: TEXT UNIQUE
- email: TEXT UNIQUE (必填)
- password_hash: TEXT
- role: TEXT (user/admin)
- created_at: TIMESTAMP
```

### palettes表
```sql
- id: INTEGER PRIMARY KEY
- name: TEXT
- description: TEXT
- type: TEXT
- colors: TEXT (逗号分隔)
- user_id: INTEGER
- username: TEXT
- likes: INTEGER
- created_at: TIMESTAMP
```

### likes表
```sql
- id: INTEGER PRIMARY KEY
- palette_id: INTEGER
- user_id: INTEGER
- ip_address: TEXT
- created_at: TIMESTAMP
```

## 🔌 API接口

### 用户认证
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 配色管理
- `POST /api/palettes/upload` - 上传配色
- `GET /api/palettes` - 获取所有配色
- `POST /api/palettes/:id/like` - 点赞配色
- `DELETE /api/palettes/:id` - 删除配色

### 管理员
- `GET /api/admin/users` - 获取所有用户
- `DELETE /api/admin/users/:id` - 删除用户
- `GET /api/admin/palettes` - 获取所有配色
- `DELETE /api/admin/palettes/:id` - 删除配色

## 🌐 访问地址

**生产环境：** https://palette.micuks.click

**服务器：** 腾讯云香港
**IP：** 43.140.243.48

## 📝 开发计划

### v1.1（下一版本）
- [ ] 配色收藏功能
- [ ] 配色评论功能
- [ ] 配色搜索功能
- [ ] 配色导出（PDF/PNG）

### v2.0（未来版本）
- [ ] AI配色生成
- [ ] 团队协作功能
- [ ] 配色模板库
- [ ] 移动端优化

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 👤 作者

**春竹** 🎋
- 创建时间：2026-02-25
- 项目状态：v1.0开发完成

---

**学术配色推荐器 - 让论文配色更专业！** 🎨