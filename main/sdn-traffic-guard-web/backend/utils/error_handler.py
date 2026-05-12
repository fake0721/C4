"""
错误处理工具 - 提供友好的错误提示和用户指导
"""

from typing import Dict, Any
from datetime import datetime


class AIErrorHandler:
    """AI错误处理器"""
    
    @staticmethod
    def handle_api_error(error_code: int, error_message: str = "") -> Dict[str, Any]:
        """处理API错误"""
        error_messages = {
            429: {
                "friendly_message": "API请求过于频繁，请稍后再试。",
                "user_guidance": "建议等待1-2分钟后再尝试，或者联系管理员检查API配额。",
                "technical_details": "HTTP 429 Too Many Requests - 已达到API调用频率限制"
            },
            401: {
                "friendly_message": "API认证失败，请检查API密钥配置。",
                "user_guidance": "请确保KIMI_API_KEY环境变量已正确设置。",
                "technical_details": "HTTP 401 Unauthorized - 无效的API密钥"
            },
            403: {
                "friendly_message": "API访问被拒绝，权限不足。",
                "user_guidance": "请联系管理员检查API访问权限。",
                "technical_details": "HTTP 403 Forbidden - 访问权限不足"
            },
            500: {
                "friendly_message": "AI服务暂时不可用，请稍后再试。",
                "user_guidance": "建议等待几分钟后重试，如果问题持续请联系技术支持。",
                "technical_details": "HTTP 500 Internal Server Error - 服务器内部错误"
            },
            503: {
                "friendly_message": "AI服务繁忙，请稍后再试。",
                "user_guidance": "建议等待几分钟后重试，服务器可能正在维护或过载。",
                "technical_details": "HTTP 503 Service Unavailable - 服务不可用"
            }
        }
        
        # 获取错误信息
        error_info = error_messages.get(error_code, {
            "friendly_message": "AI服务暂时不可用，请稍后再试。",
            "user_guidance": "如果问题持续，请联系技术支持。",
            "technical_details": f"HTTP {error_code} - {error_message}"
        })
        
        return {
            "response": f"{error_info['friendly_message']} {error_info['user_guidance']}",
            "error_code": error_code,
            "error_message": error_message,
            "technical_details": error_info['technical_details'],
            "timestamp": datetime.now().isoformat(),
            "recoverable": error_code in [429, 503]  # 这些错误通常可以自动恢复
        }
    
    @staticmethod
    def handle_network_error(error: Exception) -> Dict[str, Any]:
        """处理网络错误"""
        error_message = str(error)
        
        # 根据错误类型提供不同的指导
        if "timeout" in error_message.lower():
            guidance = "网络连接超时，请检查网络连接后重试。"
        elif "connection" in error_message.lower():
            guidance = "网络连接失败，请检查网络连接和代理设置。"
        else:
            guidance = "网络通信异常，请稍后再试。"
        
        return {
            "response": f"网络连接异常：{guidance}",
            "error_message": error_message,
            "timestamp": datetime.now().isoformat(),
            "recoverable": True
        }
    
    @staticmethod
    def handle_unexpected_error(error: Exception) -> Dict[str, Any]:
        """处理未预期的错误"""
        return {
            "response": "系统遇到未预期的错误，请稍后再试或联系技术支持。",
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "recoverable": False
        }
    
    @staticmethod
    def format_error_response(base_response: Dict[str, Any], error_info: Dict[str, Any]) -> Dict[str, Any]:
        """格式化错误响应"""
        return {
            "response": error_info["response"],
            "tools_used": base_response.get("tools_used", []),
            "model": base_response.get("model", "unknown"),
            "timestamp": error_info["timestamp"],
            "stream": base_response.get("stream", False),
            "error": error_info.get("error_message", ""),
            "error_code": error_info.get("error_code"),
            "technical_details": error_info.get("technical_details"),
            "recoverable": error_info.get("recoverable", False)
        }


# 全局错误处理器实例
error_handler = AIErrorHandler()