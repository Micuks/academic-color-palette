#!/usr/bin/env python3
"""
AI配色咨询API代理 - 稳定版
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import requests
import sys

# 华为云API配置
API_URL = "https://api.modelarts-maas.com/v2/chat/completions"
API_KEY = "4DHCx6APentIbDFVmeOzk5DwHL--rxJjPvSAh8ekM3HQ5TeOwT0ug6tf2bZ_m2rmls-OiFSMsw-eN5htcIz5vA"

class AIProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """自定义日志"""
        print(f"[AI Proxy] {args[0]}")
        sys.stdout.flush()

    def do_OPTIONS(self):
        """处理CORS预检请求"""
        try:
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
        except Exception as e:
            print(f"OPTIONS Error: {e}")

    def do_POST(self):
        """处理POST请求"""
        if self.path == '/api/ai-consult':
            try:
                # 读取请求体
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length == 0:
                    self.send_error(400, 'Empty request')
                    return

                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                user_message = data.get('message', '')

                if not user_message:
                    self.send_error(400, 'Message is required')
                    return

                print(f"收到请求: {user_message[:50]}...")
                sys.stdout.flush()

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
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                }

                print("调用华为云API...")
                sys.stdout.flush()

                response = requests.post(API_URL, json=payload, headers=headers, timeout=60)

                if response.status_code == 200:
                    result = response.json()
                    ai_message = result['choices'][0]['message']['content']

                    print(f"AI回复: {ai_message[:100]}...")
                    sys.stdout.flush()

                    # 构造响应数据
                    response_data = {
                        "success": True,
                        "message": ai_message
                    }
                    response_body = json.dumps(response_data, ensure_ascii=False).encode('utf-8')

                    # 返回AI响应（添加Content-Length强制Clash释放缓冲）
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(response_body)))
                    self.send_header('Connection', 'close')
                    self.end_headers()

                    self.wfile.write(response_body)
                    self.wfile.flush()
                else:
                    print(f"API错误: {response.status_code}")
                    sys.stdout.flush()
                    self.send_error(500, f'AI API Error: {response.status_code}')

            except requests.Timeout:
                print("API超时")
                sys.stdout.flush()
                self.send_error(504, 'AI API Timeout')

            except Exception as e:
                print(f"服务器错误: {e}")
                sys.stdout.flush()
                try:
                    self.send_error(500, f'Server Error: {str(e)}')
                except:
                    pass
        else:
            self.send_error(404, 'Not Found')

def run_server(port=8890):
    server_address = ('', port)
    httpd = HTTPServer(server_address, AIProxyHandler)
    print(f"🎨 AI配色咨询API代理运行在端口 {port}")
    print(f"📍 API端点: http://localhost:{port}/api/ai-consult")
    sys.stdout.flush()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器停止")
        sys.exit(0)

if __name__ == '__main__':
    run_server()