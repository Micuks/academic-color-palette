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
import requests
import json
import re
import colorsys

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# JWT错误处理器 - 让token无效时返回错误响应
@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    return jsonify({'success': False, 'message': 'Token无效'}), 422

@jwt.unauthorized_loader
def unauthorized_callback(error_string):
    return jsonify({'success': False, 'message': '缺少认证信息'}), 401

# 配置
app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-in-production'  # 生产环境需要修改
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

# 邮箱配置（Gmail SMTP）
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', 'zemdalk3@gmail.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'alkhrxzikhahumgr')

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
        msg['From'] = 'Academic-Color-Palette <palette-noreply@micuks.click>'
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html', 'utf-8'))

        # Gmail SMTP + STARTTLS
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"邮件发送成功: {to_email}")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False

        return True
    except Exception as e:
        print(f"❌ 发送邮件失败: {e}")
        return False

def send_verification_email(email, code, is_reset=False):
    """发送验证码邮件"""
    if is_reset:
        subject = '重置密码验证码 - 学术配色推荐器'
        body = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #FFB6C1 0%, #DDA0DD 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0;">🎨 学术配色推荐器</h1>
            </div>
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333;">重置密码验证码</h2>
                <p style="color: #666; font-size: 16px;">您正在重置密码，验证码为：</p>
                <div style="background: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                    <span style="font-size: 32px; font-weight: bold; color: #FFB6C1; letter-spacing: 5px;">{code}</span>
                </div>
                <p style="color: #999; font-size: 14px;">验证码有效期为5分钟，请尽快使用。</p>
                <p style="color: #999; font-size: 14px;">如果您没有请求重置密码，请忽略此邮件。</p>
            </div>
        </div>
        '''
    else:
        subject = '邮箱验证码 - 学术配色推荐器'
        body = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #FFB6C1 0%, #DDA0DD 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0;">🎨 学术配色推荐器</h1>
            </div>
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333;">邮箱验证码</h2>
                <p style="color: #666; font-size: 16px;">您的验证码为：</p>
                <div style="background: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                    <span style="font-size: 32px; font-weight: bold; color: #FFB6C1; letter-spacing: 5px;">{code}</span>
                </div>
                <p style="color: #999; font-size: 14px;">验证码有效期为10分钟，请尽快使用。</p>
            </div>
        </div>
        '''
    
    return send_email(email, subject, body)

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

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """忘记密码 - 发送验证码到用户邮箱"""
    data = request.get_json()
    username_or_email = data.get('username_or_email', '').strip()
    
    if not username_or_email:
        return jsonify({'success': False, 'message': '请输入用户名或邮箱'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 查找用户
    cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', 
                   (username_or_email, username_or_email))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    if not user['email']:
        conn.close()
        return jsonify({'success': False, 'message': '该用户未设置邮箱，无法重置密码'}), 400
    
    # 生成6位验证码
    code = ''.join(random.choices(string.digits, k=6))
    
    # 存储验证码（5分钟有效）
    expires_at = datetime.now() + timedelta(minutes=5)
    cursor.execute('''
        INSERT OR REPLACE INTO email_verifications (email, code, created_at, expires_at)
        VALUES (?, ?, ?, ?)
    ''', (user['email'], code, datetime.now(), expires_at))
    
    conn.commit()
    conn.close()
    
    # 发送验证码邮件
    try:
        send_verification_email(user['email'], code, is_reset=True)
        return jsonify({'success': True, 'message': '验证码已发送到邮箱'}), 200
    except Exception as e:
        print(f"发送邮件失败: {e}")
        return jsonify({'success': False, 'message': '发送邮件失败，请稍后重试'}), 500

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """重置密码"""
    data = request.get_json()
    username_or_email = data.get('username_or_email', '').strip()
    code = data.get('code', '').strip()
    new_password = data.get('new_password', '')
    
    if not username_or_email or not code or not new_password:
        return jsonify({'success': False, 'message': '请填写所有字段'}), 400
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'message': '密码至少6个字符'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 查找用户
    cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', 
                   (username_or_email, username_or_email))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    if not user['email']:
        conn.close()
        return jsonify({'success': False, 'message': '该用户未设置邮箱'}), 400
    
    # 验证验证码
    cursor.execute('SELECT * FROM email_verifications WHERE email = ? AND code = ?', 
                   (user['email'], code))
    verification = cursor.fetchone()
    
    if not verification:
        conn.close()
        return jsonify({'success': False, 'message': '验证码错误'}), 400
    
    # 检查验证码是否过期（5分钟）
    created_at = datetime.fromisoformat(verification['created_at'])
    if (datetime.now() - created_at).total_seconds() > 300:
        cursor.execute('DELETE FROM email_verifications WHERE email = ?', (user['email'],))
        conn.commit()
        conn.close()
        return jsonify({'success': False, 'message': '验证码已过期，请重新获取'}), 400
    
    # 更新密码
    password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user['id']))
    
    # 删除验证码
    cursor.execute('DELETE FROM email_verifications WHERE email = ?', (user['email'],))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '密码重置成功'}), 200

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

@app.route('/api/palettes/<int:palette_id>', methods=['PUT'])
@jwt_required()
def update_palette(palette_id):
    """编辑配色（仅管理员或作者）"""
    user_id = get_jwt_identity()
    
    data = request.get_json()
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    if not name:
        return jsonify({'success': False, 'message': '配色名称不能为空'}), 400
    
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
        return jsonify({'success': False, 'message': '没有权限编辑'}), 403
    
    # 更新配色
    cursor.execute(
        'UPDATE palettes SET name = ?, description = ? WHERE id = ?',
        (name, description, palette_id)
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '配色已更新'}), 200

@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
def admin_get_users():
    """管理员获取所有用户"""
    user_id = get_jwt_identity()
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查权限
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if user['role'] != 'admin':
        conn.close()
        return jsonify({'success': False, 'message': '没有权限'}), 403
    
    # 获取所有用户
    cursor.execute('SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC')
    users = cursor.fetchall()
    conn.close()
    
    # 格式化返回数据
    result = []
    for u in users:
        result.append({
            'id': u['id'],
            'username': u['username'],
            'email': u['email'],
            'role': u['role'],
            'created_at': u['created_at']
        })
    
    return jsonify({'success': True, 'users': result}), 200

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_user(user_id):
    """管理员删除用户"""
    admin_id = get_jwt_identity()
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查权限
    cursor.execute('SELECT * FROM users WHERE id = ?', (admin_id,))
    admin = cursor.fetchone()
    
    if admin['role'] != 'admin':
        conn.close()
        return jsonify({'success': False, 'message': '没有权限'}), 403
    
    # 不能删除自己
    if admin_id == user_id:
        conn.close()
        return jsonify({'success': False, 'message': '不能删除自己的账号'}), 400
    
    # 检查用户是否存在
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    # 删除用户的点赞记录
    cursor.execute('DELETE FROM likes WHERE user_id = ?', (user_id,))
    
    # 删除用户的配色
    cursor.execute('DELETE FROM palettes WHERE user_id = ?', (user_id,))
    
    # 删除用户
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '用户已删除'}), 200

@app.route('/api/admin/users/<int:user_id>/role', methods=['PUT'])
@jwt_required()
def admin_update_user_role(user_id):
    """管理员修改用户权限"""
    admin_id = get_jwt_identity()
    
    data = request.get_json()
    new_role = data.get('role')
    
    if new_role not in ['admin', 'user']:
        return jsonify({'success': False, 'message': '无效的角色'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查权限
    cursor.execute('SELECT * FROM users WHERE id = ?', (admin_id,))
    admin = cursor.fetchone()
    
    if admin['role'] != 'admin':
        conn.close()
        return jsonify({'success': False, 'message': '没有权限'}), 403
    
    # 不能修改自己的权限
    if admin_id == user_id:
        conn.close()
        return jsonify({'success': False, 'message': '不能修改自己的权限'}), 400
    
    # 检查用户是否存在
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    # 更新用户权限
    cursor.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': f'用户权限已更新为 {new_role}'}), 200

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

@app.route('/api/admin/palettes/<int:palette_id>', methods=['PUT'])
@jwt_required()
def admin_update_palette(palette_id):
    """管理员编辑配色"""
    user_id = get_jwt_identity()
    
    data = request.get_json()
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    if not name:
        return jsonify({'success': False, 'message': '配色名称不能为空'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查权限
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if user['role'] != 'admin':
        conn.close()
        return jsonify({'success': False, 'message': '没有权限'}), 403
    
    # 检查配色是否存在
    cursor.execute('SELECT * FROM palettes WHERE id = ?', (palette_id,))
    palette = cursor.fetchone()
    
    if not palette:
        conn.close()
        return jsonify({'success': False, 'message': '配色不存在'}), 404
    
    # 更新配色
    cursor.execute(
        'UPDATE palettes SET name = ?, description = ? WHERE id = ?',
        (name, description, palette_id)
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '配色已更新'}), 200

# ==================== AI配色咨询 ====================

import requests

# 华为云API配置
AI_API_URL = "https://api.modelarts-maas.com/v2/chat/completions"
AI_API_KEY = "***REMOVED***"

@app.route('/api/ai-consult', methods=['POST'])
def ai_consult():
    """AI配色咨询"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({'success': False, 'message': '消息不能为空'}), 400

        print(f"[AI咨询] 收到请求: {user_message[:50]}...")

        # 调用华为云API
        payload = {
            "model": "deepseek-v3.2",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的配色顾问。请简洁回答，每次建议3-5个颜色的配色方案，包括HEX码和理由。"
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "max_tokens": 200,
            "temperature": 0.7
        }

        headers = {
            "Authorization": f"Bearer {AI_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(AI_API_URL, json=payload, headers=headers, timeout=60)

        if response.status_code == 200:
            result = response.json()
            ai_message = result['choices'][0]['message']['content']

            print(f"[AI咨询] 回复: {ai_message[:100]}...")

            return jsonify({
                'success': True,
                'message': ai_message
            }), 200
        else:
            print(f"[AI咨询] API错误: {response.status_code}")
            return jsonify({'success': False, 'message': f'AI API错误: {response.status_code}'}), 500

    except requests.Timeout:
        print("[AI咨询] API超时")
        return jsonify({'success': False, 'message': 'AI API超时'}), 504

    except Exception as e:
        print(f"[AI咨询] 错误: {e}")
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500

# ==================== 健康检查 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'success': True,
        'message': 'API服务正常运行',
        'timestamp': datetime.now().isoformat()
    }), 200

# 每日配色缓存
DAILY_PALETTE_CACHE = None
DAILY_PALETTE_DATE = None

@app.route('/api/daily-palette', methods=['GET'])
def get_daily_palette():
    """获取每日配色（缓存）"""
    global DAILY_PALETTE_CACHE, DAILY_PALETTE_DATE
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 如果缓存存在且是今天的，直接返回
    if DAILY_PALETTE_CACHE and DAILY_PALETTE_DATE == today:
        print(f"[每日配色] 返回缓存数据: {today}")
        return jsonify({
            'success': True,
            'palette': DAILY_PALETTE_CACHE
        }), 200
    
    # 否则生成新的配色
    print(f"[每日配色] 生成新配色: {today}")
    palette = generate_daily_palette()
    
    # 缓存配色
    DAILY_PALETTE_CACHE = palette
    DAILY_PALETTE_DATE = today
    
    return jsonify({
        'success': True,
        'palette': palette
    }), 200

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

def call_ai_for_full_palette(date_str):
    """调用 AI 生成完整配色方案（包括颜色值）"""
    try:
        # 解析日期信息
        from datetime import datetime
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

        headers = {
            "Authorization": f"Bearer {AI_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(AI_API_URL, json=payload, headers=headers, timeout=60)

        if response.status_code == 200:
            result = response.json()
            ai_message = result['choices'][0]['message']['content']
            
            print(f"[每日配色] AI 返回: {ai_message[:200]}...")
            
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
        
        print(f"[每日配色] AI 返回格式错误")
        return None

    except json.JSONDecodeError as e:
        print(f"[每日配色] JSON 解析错误: {e}")
        return None
    except requests.Timeout:
        print("[每日配色] API 超时")
        return None
    except Exception as e:
        print(f"[每日配色] 错误: {e}")
        return None


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