#!/usr/bin/env python3
"""
AI配色咨询API代理
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import requests
import urllib.parse

# 华为云API配置
API_URL = "https://api.modelarts-maas.com/v2/chat/completions"
API_KEY = os.environ.get("HUAWEI_MAAS_API_KEY", "")

class AIProxyHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """处理POST请求"""
        if self.path == '/api/ai-consult':
            try:
                # 读取请求体
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                user_message = data.get('message', '')
                
                if not user_message:
                    self.send_error(400, 'Message is required')
                    return
                
                # 调用华为云API
                payload = {
                    "model": "deepseek-v3.2",
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个专业的配色顾问，擅长为学术图表、数据可视化、品牌设计等提供配色建议。请根据用户的需求，提供具体的配色方案，包括HEX颜色码和配色理由。回答要简洁专业，每次建议3-5个颜色的配色方案。"
                        },
                        {
                            "role": "user",
                            "content": user_message
                        }
                    ],
                    "max_tokens": 300,
                    "temperature": 0.7
                }

                headers = {
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                }

                response = requests.post(API_URL, json=payload, headers=headers, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    ai_message = result['choices'][0]['message']['content']
                    
                    # 返回AI响应
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    response_data = {
                        "success": True,
                        "message": ai_message
                    }
                    self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                else:
                    self.send_error(500, f'AI API Error: {response.status_code}')
                    
            except Exception as e:
                self.send_error(500, f'Server Error: {str(e)}')
        else:
            self.send_error(404, 'Not Found')
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[AI Proxy] {args[0]}")

def run_server(port=8890):
    server_address = ('', port)
    httpd = HTTPServer(server_address, AIProxyHandler)
    print(f"🎨 AI配色咨询API代理运行在端口 {port}")
    print(f"📍 API端点: http://localhost:{port}/api/ai-consult")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()