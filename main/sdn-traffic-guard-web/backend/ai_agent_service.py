"""
AI Agent服务 - 简化的HTTP AI调用服务
提供基础的AI对话功能
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class AIAgentService:
    """简化的AI服务类 - 直接使用HTTP API调用"""
    
    def __init__(self):
        self.dashscope_api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.kimi_api_key = os.getenv("KIMI_API_KEY", "")
        
    async def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理用户消息 - 使用Kimi API"""
        try:
            if not self.kimi_api_key:
                return {
                    "response": "AI服务未正确配置，请联系管理员设置KIMI_API_KEY环境变量",
                    "tools_used": [],
                    "timestamp": datetime.now().isoformat()
                }
            
            # Kimi API配置
            url = os.getenv("KIMI_API_URL", "https://api.moonshot.cn/v1/chat/completions")
            
            headers = {
                "Authorization": f"Bearer {self.kimi_api_key}",
                "Content-Type": "application/json"
            }
            
            # 构建提示词
            system_prompt = "你是一个专业的网络管理AI助手，请用中文回答用户的问题。"
            user_prompt = message
            if context:
                user_prompt += f"\n\n相关上下文：{json.dumps(context, ensure_ascii=False)}"
            
            data = {
                "model": os.getenv("KIMI_API_MODEL", "kimi-2.5"),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            # 发送请求
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            ai_response = result.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "抱歉，我无法处理您的请求")
            
            return {
                "response": ai_response,
                "tools_used": ["通义千问API"],
                "timestamp": datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "response": f"网络连接失败，请检查网络设置：{str(e)}",
                "tools_used": [],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "response": f"AI服务暂时不可用：{str(e)}",
                "tools_used": [],
                "timestamp": datetime.now().isoformat()
            }

    async def process_file(self, file_content: str, filename: str, query: str) -> Dict[str, Any]:
        """处理文件分析请求"""
        try:
            # 构建分析提示
            file_type = filename.split('.')[-1].lower()
            prompt = f"请分析以下文件内容：\n\n文件名：{filename}\n文件类型：{file_type}\n\n文件内容：\n{file_content[:2000]}...\n\n用户问题：{query}"

            return await self.process_message(prompt)
            
        except Exception as e:
            return {
                "response": f"文件分析失败：{str(e)}",
                "tools_used": [],
                "timestamp": datetime.now().isoformat()
            }

# 创建全局实例
ai_agent_service = AIAgentService()