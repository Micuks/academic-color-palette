#!/usr/bin/env python3
"""
Academic Color Palette - Simple Backend API Server
使用标准库实现的简单后端（无需额外依赖）
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sqlite3
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import re

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
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            token TEXT,
            token_expires TIMESTAMP,
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
            user_id INTEGER,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (palette_id) REFERENCES palettes (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 创建默认管理员账号
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute(
            'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
            ('admin', password_hash, 'admin')
        )
        print("✅ 创建默认管理员账号: admin / admin123")
    
    conn.commit()
    conn.close()

# 密码哈希
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 生成token
def generate_token():
    return secrets.token_urlsafe(32)

# 验证token
def verify_token(token):
    if not token:
        return None
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM users WHERE token = ? AND token_expires > ?',
        (token, datetime.now().isoformat())
    )
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user['id'],
            'username': user['username'],
            'password_hash': user['password_hash'],
            'role': user['role'],
            'token': user['token'],
            'token_expires': user['token_expires'],
            'created_at': user['created_at']
        }
    return None

# API处理器
class APIHandler(BaseHTTPRequestHandler):
    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)
        
        # 健康检查
        if path == '/api/health':
            self.send_json_response({
                'success': True,
                'message': 'API服务正常运行',
                'timestamp': datetime.now().isoformat()
            })
            return
        
        # 获取配色列表
        if path == '/api/palettes':
            sort_by = query.get('sort', ['time'])[0]
            palette_type = query.get('type', [None])[0]
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            query_sql = 'SELECT * FROM palettes'
            params = []
            
            if palette_type and palette_type != '自定义':
                query_sql += ' WHERE type = ?'
                params.append(palette_type)
            
            if sort_by == 'likes':
                query_sql += ' ORDER BY likes DESC, created_at DESC'
            else:
                query_sql += ' ORDER BY created_at DESC'
            
            cursor.execute(query_sql, params)
            palettes = cursor.fetchall()
            conn.close()
            
            result = []
            for p in palettes:
                result.append({
                    'id': p[0],
                    'name': p[1],
                    'description': p[2],
                    'type': p[3],
                    'colors': p[4].split(','),
                    'userId': p[5],
                    'username': p[6],
                    'likes': p[7],
                    'createdAt': p[8]
                })
            
            self.send_json_response({'success': True, 'palettes': result})
            return
        
        # 获取当前用户
        if path == '/api/auth/me':
            token = self.headers.get('Authorization', '').replace('Bearer ', '')
            user = verify_token(token)
            
            if not user:
                self.send_json_response({'success': False, 'message': '未登录或token已过期'}, 401)
                return
            
            self.send_json_response({
                'success': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role']
                }
            })
            return
        
        # 管理员获取所有配色
        if path == '/api/admin/palettes':
            token = self.headers.get('Authorization', '').replace('Bearer ', '')
            user = verify_token(token)
            
            if not user or user['role'] != 'admin':
                self.send_json_response({'success': False, 'message': '没有权限'}, 403)
                return
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM palettes ORDER BY created_at DESC')
            palettes = cursor.fetchall()
            conn.close()
            
            result = []
            for p in palettes:
                result.append({
                    'id': p[0],
                    'name': p[1],
                    'description': p[2],
                    'type': p[3],
                    'colors': p[4].split(','),
                    'userId': p[5],
                    'username': p[6],
                    'likes': p[7],
                    'createdAt': p[8]
                })
            
            self.send_json_response({'success': True, 'palettes': result})
            return
        
        self.send_json_response({'success': False, 'message': 'API不存在'}, 404)
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # 获取请求体
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else '{}'
        data = json.loads(body)
        
        # 用户注册
        if path == '/api/auth/register':
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            
            if not username or not password:
                self.send_json_response({'success': False, 'message': '用户名和密码不能为空'}, 400)
                return
            
            if len(username) < 3:
                self.send_json_response({'success': False, 'message': '用户名至少3个字符'}, 400)
                return
            
            if len(password) < 6:
                self.send_json_response({'success': False, 'message': '密码至少6个字符'}, 400)
                return
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                conn.close()
                self.send_json_response({'success': False, 'message': '用户名已存在'}, 400)
                return
            
            password_hash = hash_password(password)
            token = generate_token()
            token_expires = (datetime.now() + timedelta(days=7)).isoformat()
            
            cursor.execute(
                'INSERT INTO users (username, password_hash, role, token, token_expires) VALUES (?, ?, ?, ?, ?)',
                (username, password_hash, 'user', token, token_expires)
            )
            conn.commit()
            
            user_id = cursor.lastrowid
            conn.close()
            
            self.send_json_response({
                'success': True,
                'message': '注册成功',
                'user': {'id': user_id, 'username': username, 'role': 'user'},
                'access_token': token
            }, 201)
            return
        
        # 用户登录
        if path == '/api/auth/login':
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            
            if not username or not password:
                self.send_json_response({'success': False, 'message': '用户名和密码不能为空'}, 400)
                return
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            password_hash = hash_password(password)
            cursor.execute(
                'SELECT * FROM users WHERE username = ? AND password_hash = ?',
                (username, password_hash)
            )
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                self.send_json_response({'success': False, 'message': '用户名或密码错误'}, 401)
                return
            
            # 更新token
            token = generate_token()
            token_expires = (datetime.now() + timedelta(days=7)).isoformat()
            cursor.execute(
                'UPDATE users SET token = ?, token_expires = ? WHERE id = ?',
                (token, token_expires, user[0])
            )
            conn.commit()
            conn.close()
            
            self.send_json_response({
                'success': True,
                'message': '登录成功',
                'user': {'id': user[0], 'username': user[1], 'role': user[3]},
                'access_token': token
            })
            return
        
        # 上传配色
        if path == '/api/palettes/upload':
            token = self.headers.get('Authorization', '').replace('Bearer ', '')
            user = verify_token(token)
            
            if not user:
                self.send_json_response({'success': False, 'message': '未登录或token已过期'}, 401)
                return
            
            name = data.get('name', '').strip()
            description = data.get('description', '').strip()
            palette_type = data.get('type', '').strip()
            colors = data.get('colors', [])
            
            if not name or not colors:
                self.send_json_response({'success': False, 'message': '配色名称和颜色列表不能为空'}, 400)
                return
            
            # 验证颜色格式
            for color in colors:
                if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
                    self.send_json_response({'success': False, 'message': f'颜色格式错误: {color}'}, 400)
                    return
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            colors_str = ','.join(colors)
            cursor.execute(
                'INSERT INTO palettes (name, description, type, colors, user_id, username) VALUES (?, ?, ?, ?, ?, ?)',
                (name, description, palette_type, colors_str, user['id'], user['username'])
            )
            conn.commit()
            palette_id = cursor.lastrowid
            conn.close()
            
            self.send_json_response({
                'success': True,
                'message': '上传成功',
                'palette_id': palette_id
            }, 201)
            return
        
        # 点赞配色
        if path.startswith('/api/palettes/') and path.endswith('/like'):
            match = re.match(r'/api/palettes/(\d+)/like', path)
            if not match:
                self.send_json_response({'success': False, 'message': 'API路径错误'}, 400)
                return
            
            palette_id = int(match.group(1))
            token = self.headers.get('Authorization', '').replace('Bearer ', '')
            user = verify_token(token)
            
            if not user:
                self.send_json_response({'success': False, 'message': '未登录或token已过期'}, 401)
                return
            
            ip_address = self.client_address[0]
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # 检查是否已点赞
            cursor.execute(
                'SELECT * FROM likes WHERE palette_id = ? AND user_id = ?',
                (palette_id, user['id'])
            )
            if cursor.fetchone():
                conn.close()
                self.send_json_response({'success': False, 'message': '你已经点赞过了'}, 400)
                return
            
            # 添加点赞记录
            cursor.execute(
                'INSERT INTO likes (palette_id, user_id, ip_address) VALUES (?, ?, ?)',
                (palette_id, user['id'], ip_address)
            )
            
            # 更新点赞数
            cursor.execute(
                'UPDATE palettes SET likes = likes + 1 WHERE id = ?',
                (palette_id,)
            )
            
            cursor.execute('SELECT likes FROM palettes WHERE id = ?', (palette_id,))
            palette = cursor.fetchone()
            
            conn.commit()
            conn.close()
            
            self.send_json_response({
                'success': True,
                'message': '点赞成功',
                'likes': palette[0]
            })
            return
        
        self.send_json_response({'success': False, 'message': 'API不存在'}, 404)
    
    def do_DELETE(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # 删除配色
        if path.startswith('/api/palettes/'):
            match = re.match(r'/api/palettes/(\d+)', path)
            if not match:
                self.send_json_response({'success': False, 'message': 'API路径错误'}, 400)
                return
            
            palette_id = int(match.group(1))
            token = self.headers.get('Authorization', '').replace('Bearer ', '')
            user = verify_token(token)
            
            if not user:
                self.send_json_response({'success': False, 'message': '未登录或token已过期'}, 401)
                return
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # 获取配色信息
            cursor.execute('SELECT * FROM palettes WHERE id = ?', (palette_id,))
            palette = cursor.fetchone()
            
            if not palette:
                conn.close()
                self.send_json_response({'success': False, 'message': '配色不存在'}, 404)
                return
            
            # 检查权限（管理员或作者）
            if user['role'] != 'admin' and palette[5] != user['id']:
                conn.close()
                self.send_json_response({'success': False, 'message': '没有权限删除'}, 403)
                return
            
            # 删除点赞记录
            cursor.execute('DELETE FROM likes WHERE palette_id = ?', (palette_id,))
            
            # 删除配色
            cursor.execute('DELETE FROM palettes WHERE id = ?', (palette_id,))
            
            conn.commit()
            conn.close()
            
            self.send_json_response({'success': True, 'message': '删除成功'})
            return
        
        self.send_json_response({'success': False, 'message': 'API不存在'}, 404)
    
    def log_message(self, format, *args):
        # 自定义日志格式
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {args[0]}")

if __name__ == '__main__':
    # 确保数据库目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # 初始化数据库
    init_db()
    
    print("=" * 60)
    print("🎨 Academic Color Palette - Simple Backend API Server")
    print("=" * 60)
    print(f"📡 API地址: http://localhost:8890")
    print(f"💾 数据库: {DB_PATH}")
    print(f"👤 管理员账号: admin / admin123")
    print("=" * 60)
    
    # 启动服务器
    server = HTTPServer(('0.0.0.0', 8890), APIHandler)
    print("✅ 服务器启动成功！")
    server.serve_forever()