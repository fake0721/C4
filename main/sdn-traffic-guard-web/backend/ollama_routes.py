from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import json
import os
from dotenv import load_dotenv

# load .env
load_dotenv()
from typing import List, Optional

router = APIRouter(prefix="/api/ollama", tags=["ollama"])

# Ollama服务配置（优先从环境变量读取）
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11435")

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    model: str = "qwen2.5:1.5b"
    messages: List[ChatMessage]
    stream: bool = False

class ChatResponse(BaseModel):
    message: ChatMessage
    done: bool
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None

class SDNControlRequest(BaseModel):
    command: str
    context: Optional[str] = None

@router.get("/models")
async def get_models():
    """获取可用的Ollama模型列表"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"无法连接到Ollama服务: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")

@router.post("/chat")
async def chat_with_ollama(request: ChatRequest):
    """与Ollama模型进行对话"""
    try:
        # 构建请求数据
        chat_data = {
            "model": request.model,
            "messages": [msg.dict() for msg in request.messages],
            "stream": request.stream
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=chat_data
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"无法连接到Ollama服务: {str(e)}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="请求超时")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")

@router.post("/sdn-control")
async def sdn_intelligent_control(request: SDNControlRequest):
    """SDN智能控制功能"""
    try:
        # 构建SDN控制的系统提示
        system_prompt = """
你是一个SDN（软件定义网络）智能控制器助手。你可以帮助用户：
1. 理解和分析网络拓扑
2. 配置流表规则
3. 监控网络状态
4. 优化网络性能
5. 处理网络故障
6. 管理黑白名单

请根据用户的命令提供专业的SDN网络管理建议和操作指导。
如果用户询问具体的网络配置或控制命令，请提供详细的步骤和解释。
        """
        
        # 构建消息
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.command}
        ]
        
        if request.context:
            messages.insert(-1, {"role": "user", "content": f"当前网络状态: {request.context}"})
        
        # 调用Ollama
        chat_data = {
            "model": "qwen2.5:1.5b",
            "messages": messages,
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=chat_data
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "response": result["message"]["content"],
                "model": "qwen2.5:1.5b",
                "timestamp": result.get("created_at"),
                "usage": {
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0),
                    "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                }
            }
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"无法连接到Ollama服务: {str(e)}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="请求超时")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SDN智能控制失败: {str(e)}")

@router.get("/health")
async def check_ollama_health():
    """检查Ollama服务健康状态"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            models = response.json()
            
            return {
                "status": "healthy",
                "url": OLLAMA_BASE_URL,
                "models_count": len(models.get("models", [])),
                "available_models": [model["name"] for model in models.get("models", [])]
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "url": OLLAMA_BASE_URL,
            "error": str(e)
        }