#!/usr/bin/env python3
"""
Academic Color Palette - Backend API Server
完整的用户认证和配色管理系统
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import sqlite3
import os
from datetime import datetime, timedelta
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# JWT错误处理器 - 让token无效时返回None而不是报错
@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    return None

@jwt.unauthorized_loader
def unauthorized_callback(error_string):
    return None

# 配置
app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-in-production'  # 生产环境需要修改
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

# 邮箱配置（需要配置SMTP服务器）
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.qq.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 465))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')  # 发件邮箱
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')  # 邮箱授权码

# 数据库路径
DB_PATH = '/var/www/palette/database.db'

# 初始化数据库
def init_db():
    """初始化数据库表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 配色表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS palettes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            type TEXT NOT NULL,
            colors TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            likes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 点赞记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            palette_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (palette_id) REFERENCES palettes (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(palette_id, user_id)
        )
    ''')

    # 邮箱验证码表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            code TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER DEFAULT 0
        )
    ''')
    
    # 创建默认管理员账号
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        password_hash = bcrypt.generate_password_hash('admin123').decode('utf-8')
        cursor.execute(
            'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
            ('admin', password_hash, 'admin')
        )
        print("✅ 创建默认管理员账号: admin / admin123")
    
    conn.commit()
    conn.close()

# 获取数据库连接
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ==================== 邮箱验证 API ====================

def send_email(to_email, subject, body):
    """发送邮件"""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        # SMTP未配置，返回True让调用者知道"发送成功"（实际是开发模式）
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = 'palette-noreply@micuks.click'  # 使用别名作为发件人
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html', 'utf-8'))

        # Gmail使用SMTP + STARTTLS（端口587）
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # 开启TLS加密
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()

        return True
    except Exception as e:
        print(f"❌ 发送邮件失败: {e}")
        return False

def generate_verification_code():
    """生成6位数字验证码"""
    return ''.join(random.choices(string.digits, k=6))

@app.route('/api/auth/send-verification', methods=['POST'])
def send_verification_code():
    """发送邮箱验证码"""
    data = request.get_json()
    email = data.get('email', '').strip()

    if not email:
        return jsonify({'success': False, 'message': '邮箱不能为空'}), 400

    # 验证邮箱格式
    import re
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({'success': False, 'message': '邮箱格式不正确'}), 400

    # 检查邮箱是否已注册
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '邮箱已被注册'}), 400

    # 生成验证码
    code = generate_verification_code()
    expires_at = datetime.now() + timedelta(minutes=10)  # 10分钟后过期

    # 保存验证码到数据库
    cursor.execute(
        'INSERT INTO email_verifications (email, code, expires_at) VALUES (?, ?, ?)',
        (email, code, expires_at)
    )
    conn.commit()
    conn.close()

    # 发送邮件
    subject = '学术配色推荐器 - 邮箱验证码'
    body = f'''
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #FFB6C1;">🎨 学术配色推荐器</h2>
        <p>您好！</p>
        <p>您正在注册学术配色推荐器账号，验证码为：</p>
        <div style="background: linear-gradient(135deg, #FFE5EC 0%, #FFF0F5 100%);
                    padding: 20px;
                    text-align: center;
                    border-radius: 10px;
                    margin: 20px 0;">
            <span style="font-size: 32px; font-weight: bold; color: #FF6B9D; letter-spacing: 5px;">{code}</span>
        </div>
        <p style="color: #888;">验证码有效期为10分钟，请尽快使用。</p>
        <p style="color: #888;">如果这不是您的操作，请忽略此邮件。</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #aaa; font-size: 12px;">学术配色推荐器 - 让论文配色更专业</p>
    </div>
    '''

    if send_email(email, subject, body):
        # 开发环境：打印验证码到服务器日志
        if not SMTP_USERNAME:
            print(f"\n{'='*60}")
            print(f"📧 邮箱验证码（开发模式）")
            print(f"{'='*60}")
            print(f"邮箱: {email}")
            print(f"验证码: {code}")
            print(f"有效期: 10分钟")
            print(f"{'='*60}\n")

        return jsonify({
            'success': True,
            'message': '验证码已发送到邮箱'
        }), 200
    else:
        return jsonify({'success': False, 'message': '发送验证码失败，请稍后重试'}), 500

@app.route('/api/auth/verify-code', methods=['POST'])
def verify_code():
    """验证邮箱验证码"""
    data = request.get_json()
    email = data.get('email', '').strip()
    code = data.get('code', '').strip()

    if not email or not code:
        return jsonify({'success': False, 'message': '邮箱和验证码不能为空'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # 查找最新的未使用的验证码
    cursor.execute('''
        SELECT * FROM email_verifications
        WHERE email = ? AND code = ? AND used = 0 AND expires_at > ?
        ORDER BY created_at DESC LIMIT 1
    ''', (email, code, datetime.now()))

    verification = cursor.fetchone()

    if not verification:
        conn.close()
        return jsonify({'success': False, 'message': '验证码错误或已过期'}), 400

    # 标记验证码为已使用
    cursor.execute('UPDATE email_verifications SET used = 1 WHERE id = ?', (verification['id'],))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': '验证成功'}), 200

# ==================== 用户认证 API ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册（需要验证码）"""
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    verification_code = data.get('verificationCode', '').strip()

    if not username or not email or not password or not verification_code:
        return jsonify({'success': False, 'message': '用户名、邮箱、密码和验证码不能为空'}), 400

    if len(username) < 3:
        return jsonify({'success': False, 'message': '用户名至少3个字符'}), 400

    if len(password) < 6:
        return jsonify({'success': False, 'message': '密码至少6个字符'}), 400

    # 验证邮箱格式
    import re
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({'success': False, 'message': '邮箱格式不正确'}), 400

    # 验证验证码
    conn = get_db()
    cursor = conn.cursor()

    # 查询未使用的验证码
    cursor.execute('''
        SELECT * FROM email_verifications
        WHERE email = ? AND code = ? AND used = 0 AND expires_at > ?
        ORDER BY created_at DESC LIMIT 1
    ''', (email, verification_code, datetime.now()))

    verification = cursor.fetchone()
    if not verification:
        conn.close()
        return jsonify({'success': False, 'message': '验证码错误或已过期'}), 400

    # 标记验证码为已使用
    cursor.execute('''
        UPDATE email_verifications
        SET used = 1
        WHERE id = ?
    ''', (verification[0],))

    # 检查用户名是否已存在
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '用户名已存在'}), 400

    # 检查邮箱是否已存在
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '邮箱已被注册'}), 400

    # 创建新用户
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    cursor.execute(
        'INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)',
        (username, email, password_hash, 'user')
    )
    conn.commit()

    # 获取新用户信息
    user_id = cursor.lastrowid
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    # 生成JWT token
    access_token = create_access_token(identity=str(user_id))

    return jsonify({
        'success': True,
        'message': '注册成功',
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role']
        },
        'access_token': access_token
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录（支持用户名或邮箱登录）"""
    data = request.get_json()
    login_input = data.get('username', '').strip()  # 可以是用户名或邮箱
    password = data.get('password', '').strip()
    
    if not login_input or not password:
        return jsonify({'success': False, 'message': '用户名/邮箱和密码不能为空'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 判断是邮箱还是用户名
    if '@' in login_input:
        # 邮箱登录
        cursor.execute('SELECT * FROM users WHERE email = ?', (login_input,))
    else:
        # 用户名登录
        cursor.execute('SELECT * FROM users WHERE username = ?', (login_input,))
    
    user = cursor.fetchone()
    conn.close()
    
    if not user or not bcrypt.check_password_hash(user['password_hash'], password):
        return jsonify({'success': False, 'message': '用户名/邮箱或密码错误'}), 401
    
    # 生成JWT token
    access_token = create_access_token(identity=str(user['id']))
    
    return jsonify({
        'success': True,
        'message': '登录成功',
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'] if user['email'] else '',
            'role': user['role']
        },
        'access_token': access_token
    }), 200

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """获取当前登录用户信息"""
    user_id = get_jwt_identity()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'] if user['email'] else '',
            'role': user['role']
        }
    }), 200

# ==================== 配色管理 API ====================

@app.route('/api/palettes/upload', methods=['POST'])
@jwt_required()
def upload_palette():
    """上传配色"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    palette_type = data.get('type', '').strip()
    colors = data.get('colors', [])
    
    if not name or not colors:
        return jsonify({'success': False, 'message': '配色名称和颜色列表不能为空'}), 400
    
    if not isinstance(colors, list) or len(colors) == 0:
        return jsonify({'success': False, 'message': '颜色列表格式错误'}), 400
    
    # 验证颜色格式
    import re
    for color in colors:
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            return jsonify({'success': False, 'message': f'颜色格式错误: {color}'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取用户信息
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    # 保存配色
    colors_str = ','.join(colors)
    cursor.execute(
        'INSERT INTO palettes (name, description, type, colors, user_id, username) VALUES (?, ?, ?, ?, ?, ?)',
        (name, description, palette_type, colors_str, user_id, user['username'])
    )
    conn.commit()
    
    palette_id = cursor.lastrowid
    conn.close()
    
    return jsonify({
        'success': True,
        'message': '上传成功',
        'palette_id': palette_id
    }), 201

@app.route('/api/palettes', methods=['GET'])
def get_palettes():
    """获取配色列表"""
    sort_by = request.args.get('sort', 'time')  # time 或 likes
    palette_type = request.args.get('type', None)  # 筛选类型

    conn = get_db()
    cursor = conn.cursor()

    # 构建查询
    query = 'SELECT * FROM palettes'
    params = []

    # 根据类型筛选
    if palette_type:
        query += ' WHERE type = ?'
        params.append(palette_type)

    # 排序
    if sort_by == 'likes':
        query += ' ORDER BY likes DESC, created_at DESC'
    else:
        query += ' ORDER BY created_at DESC'

    cursor.execute(query, params)
    palettes = cursor.fetchall()
    conn.close()

    # 格式化返回数据
    result = []
    for p in palettes:
        result.append({
            'id': p['id'],
            'name': p['name'],
            'description': p['description'],
            'type': p['type'],
            'colors': p['colors'].split(','),
            'userId': p['user_id'],
            'username': p['username'],
            'likes': p['likes'],
            'createdAt': p['created_at']
        })

    return jsonify({
        'success': True,
        'palettes': result
    }), 200

def get_real_ip():
    """获取真实IP地址"""
    # 优先从X-Forwarded-For获取
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # X-Forwarded-For可能包含多个IP，取第一个
        return forwarded_for.split(',')[0].strip()
    
    # 其次从X-Real-IP获取
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    # 最后使用remote_addr
    return request.remote_addr

@app.route('/api/palettes/<int:palette_id>/like-status', methods=['GET'])
def get_like_status(palette_id):
    """检查点赞状态"""
    # 获取用户ID（如果已登录）
    user_id = None
    try:
        # 尝试从header中获取token
        auth_header = request.headers.get('Authorization', None)
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            # 尝试解码token
            from flask_jwt_extended import decode_token
            decoded = decode_token(token)
            user_id = decoded.get('sub')
            print(f"[后端-点赞状态] palette_id={palette_id}, user_id={user_id}, token有效")
    except Exception as e:
        print(f"[后端-点赞状态] palette_id={palette_id}, token无效或无token: {e}")
        pass

    # 获取真实IP地址
    ip_address = get_real_ip()
    print(f"[后端-点赞状态] palette_id={palette_id}, user_id={user_id}, ip_address={ip_address}")

    conn = get_db()
    cursor = conn.cursor()

    # 检查是否已点赞
    if user_id:
        cursor.execute('''
            SELECT * FROM likes WHERE palette_id = ? AND user_id = ?
        ''', (palette_id, user_id))
    else:
        cursor.execute('''
            SELECT * FROM likes WHERE palette_id = ? AND ip_address = ?
        ''', (palette_id, ip_address))

    liked = cursor.fetchone() is not None
    conn.close()
    
    print(f"[后端-点赞状态] palette_id={palette_id}, liked={liked}")
    return jsonify({'success': True, 'liked': liked}), 200

@app.route('/api/palettes/<int:palette_id>/like', methods=['POST'])
def like_palette(palette_id):
    """点赞/取消点赞配色"""
    # 获取用户ID（如果已登录）
    user_id = None
    try:
        # 尝试从header中获取token
        auth_header = request.headers.get('Authorization', None)
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            # 尝试解码token
            from flask_jwt_extended import decode_token
            decoded = decode_token(token)
            user_id = decoded.get('sub')
            print(f"[后端-点赞操作] palette_id={palette_id}, user_id={user_id}, token有效")
    except Exception as e:
        print(f"[后端-点赞操作] palette_id={palette_id}, token无效或无token: {e}")
        pass

    # 获取真实IP地址
    ip_address = get_real_ip()
    print(f"[后端-点赞操作] palette_id={palette_id}, user_id={user_id}, ip_address={ip_address}")

    conn = get_db()
    cursor = conn.cursor()

    # 检查是否已点赞
    if user_id:
        cursor.execute('''
            SELECT * FROM likes WHERE palette_id = ? AND user_id = ?
        ''', (palette_id, user_id))
    else:
        cursor.execute('''
            SELECT * FROM likes WHERE palette_id = ? AND ip_address = ?
        ''', (palette_id, ip_address))

    existing_like = cursor.fetchone()

    if existing_like:
        # 取消点赞
        cursor.execute('DELETE FROM likes WHERE id = ?', (existing_like[0],))
        cursor.execute('''
            UPDATE palettes SET likes = likes - 1 WHERE id = ? AND likes > 0
        ''', (palette_id,))
        conn.commit()

        # 获取更新后的点赞数
        cursor.execute('SELECT likes FROM palettes WHERE id = ?', (palette_id,))
        likes = cursor.fetchone()[0]
        conn.close()

        print(f"[后端-点赞操作] palette_id={palette_id}, 取消点赞, likes={likes}")
        return jsonify({'success': True, 'liked': False, 'likes': likes}), 200
    else:
        # 添加点赞
        cursor.execute('''
            INSERT INTO likes (palette_id, user_id, ip_address, created_at)
            VALUES (?, ?, ?, ?)
        ''', (palette_id, user_id, ip_address, datetime.now()))

        cursor.execute('''
            UPDATE palettes SET likes = likes + 1 WHERE id = ?
        ''', (palette_id,))
        conn.commit()

        # 获取更新后的点赞数
        cursor.execute('SELECT likes FROM palettes WHERE id = ?', (palette_id,))
        likes = cursor.fetchone()[0]
        conn.close()

        print(f"[后端-点赞操作] palette_id={palette_id}, 添加点赞, likes={likes}")
        return jsonify({'success': True, 'liked': True, 'likes': likes}), 200

@app.route('/api/palettes/<int:palette_id>', methods=['DELETE'])
@jwt_required()
def delete_palette(palette_id):
    """删除配色（仅管理员或作者）"""
    user_id = get_jwt_identity()
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取用户信息
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    # 获取配色信息
    cursor.execute('SELECT * FROM palettes WHERE id = ?', (palette_id,))
    palette = cursor.fetchone()
    
    if not palette:
        conn.close()
        return jsonify({'success': False, 'message': '配色不存在'}), 404
    
    # 检查权限（管理员或作者）
    if user['role'] != 'admin' and palette['user_id'] != user_id:
        conn.close()
        return jsonify({'success': False, 'message': '没有权限删除'}), 403
    
    # 删除点赞记录
    cursor.execute('DELETE FROM likes WHERE palette_id = ?', (palette_id,))
    
    # 删除配色
    cursor.execute('DELETE FROM palettes WHERE id = ?', (palette_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': '删除成功'
    }), 200

@app.route('/api/admin/palettes', methods=['GET'])
@jwt_required()
def admin_get_palettes():
    """管理员获取所有配色"""
    user_id = get_jwt_identity()
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查权限
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if user['role'] != 'admin':
        conn.close()
        return jsonify({'success': False, 'message': '没有权限'}), 403
    
    # 获取所有配色
    cursor.execute('SELECT * FROM palettes ORDER BY created_at DESC')
    palettes = cursor.fetchall()
    conn.close()
    
    # 格式化返回数据
    result = []
    for p in palettes:
        result.append({
            'id': p['id'],
            'name': p['name'],
            'description': p['description'],
            'type': p['type'],
            'colors': p['colors'].split(','),
            'userId': p['user_id'],
            'username': p['username'],
            'likes': p['likes'],
            'createdAt': p['created_at']
        })
    
    return jsonify({
        'success': True,
        'palettes': result
    }), 200

# ==================== 健康检查 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'success': True,
        'message': 'API服务正常运行',
        'timestamp': datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    # 确保数据库目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # 初始化数据库
    init_db()
    
    print("=" * 60)
    print("🎨 Academic Color Palette - Backend API Server")
    print("=" * 60)
    print(f"📡 API地址: http://localhost:8890")
    print(f"💾 数据库: {DB_PATH}")
    print(f"👤 管理员账号: admin / admin123")
    print("=" * 60)
    
    # 启动服务器
    app.run(host='0.0.0.0', port=8890, debug=True)