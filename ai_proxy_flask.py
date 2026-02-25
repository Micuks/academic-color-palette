#!/usr/bin/env python3
"""
AI配色咨询API代理 - Flask稳定版
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import sys

app = Flask(__name__)
CORS(app)  # 启用CORS支持

# 华为云API配置
API_URL = "https://api.modelarts-maas.com/v2/chat/completions"
API_KEY = "4DHCx6APentIbDFVmeOzk5DwHL--rxJjPvSAh8ekM3HQ5TeOwT0ug6tf2bZ_m2rmls-OiFSMsw-eN5htcIz5vA"

@app.route('/api/ai-consult', methods=['POST', 'OPTIONS'])
def ai_consult():
    """AI配色咨询接口"""
    try:
        # 获取请求数据
        data = request.get_json()
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400

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

            return jsonify({
                'success': True,
                'message': ai_message
            })
        else:
            print(f"API错误: {response.status_code}")
            sys.stdout.flush()
            return jsonify({'success': False, 'error': f'AI API Error: {response.status_code}'}), 500

    except requests.Timeout:
        print("API超时")
        sys.stdout.flush()
        return jsonify({'success': False, 'error': 'AI API Timeout'}), 504

    except Exception as e:
        print(f"服务器错误: {e}")
        sys.stdout.flush()
        return jsonify({'success': False, 'error': f'Server Error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health():
    """健康检查端点"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("🎨 AI配色咨询API代理运行在端口 8890")
    print("📍 API端点: http://localhost:8890/api/ai-consult")
    sys.stdout.flush()
    app.run(host='0.0.0.0', port=8890, debug=False)