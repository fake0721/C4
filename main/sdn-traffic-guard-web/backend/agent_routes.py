"""
Agent API路由
提供RAG + Agent功能的HTTP接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Callable, Dict, Any, Optional, List
from datetime import datetime
import traceback

_get_agent_instance: Optional[Callable[[], Any]] = None

# 导入Agent
try:
    from .security_agent import get_agent_instance as imported_get_agent_instance
    _get_agent_instance = imported_get_agent_instance
    AGENT_AVAILABLE = True
except ImportError:
    try:
        from security_agent import get_agent_instance as imported_get_agent_instance
        _get_agent_instance = imported_get_agent_instance
        AGENT_AVAILABLE = True
    except Exception as e:
        print(f"⚠️ Agent模块加载失败: {e}")
        AGENT_AVAILABLE = False

router = APIRouter(prefix="/api/agent", tags=["AI Agent"])


def get_agent_instance() -> Any:
    if _get_agent_instance is None:
        raise HTTPException(status_code=503, detail="Agent service unavailable")
    return _get_agent_instance()


# ========== 请求/响应模型 ==========

class AnomalyAnalyzeRequest(BaseModel):
    """异常分析请求"""
    type: str  # 异常类型
    src_ip: str  # 源IP
    features: Optional[str] = ""  # 特征描述
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "DDoS",
                "src_ip": "192.168.1.100",
                "features": "流量突增，包大小512字节"
            }
        }


class QuickQueryRequest(BaseModel):
    """快速查询请求"""
    query: str  # 查询内容
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "什么是DDoS攻击？如何防御？"
            }
        }


# ========== API端点 ==========

@router.post("/analyze")
async def analyze_anomaly(request: AnomalyAnalyzeRequest):
    """
    分析网络异常
    
    使用Agent系统分析异常，包括：
    1. RAG知识库检索
    2. MCP工具调用（IP历史、网络状态）
    3. LLM智能分析
    4. 生成完整报告
    """
    if not AGENT_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Agent服务不可用，请检查依赖是否安装（langchain, chromadb等）"
        )
    
    try:
        # 获取Agent实例
        agent = get_agent_instance()
        
        # 分析异常
        result = agent.analyze_anomaly({
            "type": request.type,
            "src_ip": request.src_ip,
            "features": request.features
        })
        
        return {
            "success": True,
            "data": result,
            "message": "分析完成"
        }
        
    except Exception as e:
        print(f"❌ Agent分析失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/query")
async def quick_query(request: QuickQueryRequest):
    """
    快速查询
    
    使用RAG系统回答网络安全相关问题
    """
    if not AGENT_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Agent服务不可用，请检查依赖是否安装"
        )
    
    try:
        # 获取Agent实例
        agent = get_agent_instance()
        
        # 快速查询
        result = agent.quick_query(request.query)
        
        return {
            "success": True,
            "data": result,
            "message": "查询完成"
        }
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/status")
async def get_agent_status():
    """
    获取Agent系统状态
    
    返回Agent是否可用、RAG知识库状态等信息
    """
    if not AGENT_AVAILABLE:
        return {
            "success": False,
            "available": False,
            "message": "Agent service unavailable",
            "details": "Please install dependencies: pip install langchain chromadb"
        }
    
    try:
        agent = get_agent_instance()
        
        # 检查RAG知识库是否加载
        knowledge = await agent.rag.search_similar_documents("SDN", k=1)
        knowledge_available = len(knowledge) > 0
        
        # 获取模型配置信息
        import os
        dashscope_model = os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v4")
        chat_model = os.getenv("DASHSCOPE_CHAT_MODEL", "qwen-plus-v3")
        kimi_model = os.getenv("KIMI_API_MODEL", "kimi-2.5")
        
        return {
            "success": True,
            "available": True,
            "rag_enabled": True,
            "knowledge_base_ready": knowledge_available,
            "model": agent.model,
            "embedding_model": dashscope_model,
            "chat_model": chat_model,
            "kimi_model": kimi_model,
            "tools_count": len(agent.tools),
            "message": "Agent system running normally"
        }
        
    except Exception as e:
        print(f"Agent status check error: {e}")
        traceback.print_exc()
        return {
            "success": False,
            "available": False,
            "message": f"Status check failed: {str(e)}"
        }


@router.post("/knowledge/search")
async def search_knowledge(request: QuickQueryRequest):
    """
    搜索知识库
    
    直接检索知识库中的相关文档（不使用LLM生成）
    """
    if not AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Agent服务不可用")
    
    try:
        agent = get_agent_instance()
        search_result = agent._tool_search_knowledge(request.query)
        knowledge = search_result.get("data", [])
        
        return {
            "success": True,
            "data": {
                "query": request.query,
                "results": knowledge,
                "count": len(knowledge)
            },
            "message": "搜索完成"
        }
        
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


# ========== MCP工具测试端点 ==========

class MCPToolRequest(BaseModel):
    """MCP工具请求"""
    tool_name: str  # 工具名称
    ip: Optional[str] = None  # IP地址（可选）
    attack_type: Optional[str] = None  # 攻击类型（可选）
    level: Optional[str] = None  # 限速档位（可选）
    duration_seconds: Optional[int] = 300  # 限速时长（可选）
    reason: Optional[str] = None  # 原因（可选）


@router.post("/tools/call")
async def call_mcp_tool(request: MCPToolRequest):
    """
    调用MCP工具
    
    支持的工具：
    - query_acl_status: 查询黑白名单状态
    - query_rate_limit_history: 查询限速历史
    - query_attack_history: 查询攻击历史
    - query_flow_stats: 查询流量统计
    - get_defense_rules: 获取防御规则
    - query_network_topology: 查询网络拓扑
    - get_current_status: 获取系统状态
    - apply_rate_limit: 应用限速规则
    - add_to_blacklist: 加入黑名单
    - add_to_whitelist: 加入白名单
    """
    if not AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Agent服务不可用")
    
    try:
        agent = get_agent_instance()
        tool_name = request.tool_name
        
        # 检查工具是否存在
        if tool_name not in agent.tools:
            raise HTTPException(
                status_code=400,
                detail=f"工具不存在: {tool_name}，可用工具: {list(agent.tools.keys())}"
            )
        
        # 调用相应的工具
        if tool_name == "query_acl_status":
            if not request.ip:
                raise HTTPException(status_code=400, detail="缺少参数: ip")
            result = agent._tool_query_acl_status(request.ip)
            
        elif tool_name == "query_rate_limit_history":
            if not request.ip:
                raise HTTPException(status_code=400, detail="缺少参数: ip")
            result = agent._tool_query_rate_limit_history(request.ip)
            
        elif tool_name == "query_attack_history":
            if not request.ip:
                raise HTTPException(status_code=400, detail="缺少参数: ip")
            result = agent._tool_query_attack_history(request.ip)
            
        elif tool_name == "query_flow_stats":
            if not request.ip:
                raise HTTPException(status_code=400, detail="缺少参数: ip")
            result = agent._tool_query_flow_stats(request.ip)
            
        elif tool_name == "get_defense_rules":
            result = agent._tool_get_defense_rules(request.attack_type)
            
        elif tool_name == "query_network_topology":
            result = agent._tool_query_network_topology()
            
        elif tool_name == "get_current_status":
            result = agent._tool_get_current_status()
            
        elif tool_name == "apply_rate_limit":
            if not request.ip or not request.level or not request.reason:
                raise HTTPException(status_code=400, detail="缺少参数: ip, level, reason")
            result = agent._tool_apply_rate_limit(
                request.ip,
                request.level,
                request.duration_seconds if request.duration_seconds is not None else 300,
                request.reason,
            )
            
        elif tool_name == "add_to_blacklist":
            if not request.ip or not request.reason:
                raise HTTPException(status_code=400, detail="缺少参数: ip, reason")
            result = agent._tool_add_to_blacklist(request.ip, request.reason)
            
        elif tool_name == "add_to_whitelist":
            if not request.ip or not request.reason:
                raise HTTPException(status_code=400, detail="缺少参数: ip, reason")
            result = agent._tool_add_to_whitelist(request.ip, request.reason)
            
        else:
            raise HTTPException(status_code=400, detail=f"未知工具: {tool_name}")
        
        return {
            "success": result.get("success", True),
            "tool": tool_name,
            "data": result.get("data", {}),
            "error": result.get("error", None)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ MCP工具调用失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"工具调用失败: {str(e)}")


@router.get("/tools/list")
async def list_mcp_tools():
    """
    获取所有可用的MCP工具列表
    """
    if not AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Agent服务不可用")
    
    try:
        agent = get_agent_instance()
        
        tools_info = {
            "query_acl_status": {
                "name": "查询黑白名单状态",
                "description": "查询IP是否在黑名单或白名单中",
                "parameters": ["ip"],
                "type": "query"
            },
            "query_rate_limit_history": {
                "name": "查询限速历史",
                "description": "查询IP的限速历史和当前限速状态",
                "parameters": ["ip"],
                "type": "query"
            },
            "query_attack_history": {
                "name": "查询攻击历史",
                "description": "查询IP的历史攻击记录",
                "parameters": ["ip"],
                "type": "query"
            },
            "query_flow_stats": {
                "name": "查询流量统计",
                "description": "查询IP的流量统计信息",
                "parameters": ["ip"],
                "type": "query"
            },
            "get_defense_rules": {
                "name": "获取防御规则",
                "description": "获取攻击类型的防御规则",
                "parameters": ["attack_type(可选)"],
                "type": "query"
            },
            "query_network_topology": {
                "name": "查询网络拓扑",
                "description": "获取网络拓扑信息",
                "parameters": [],
                "type": "query"
            },
            "get_current_status": {
                "name": "获取系统状态",
                "description": "获取系统当前的防御状态",
                "parameters": [],
                "type": "query"
            },
            "apply_rate_limit": {
                "name": "应用限速规则",
                "description": "对IP应用限速规则",
                "parameters": ["ip", "level(low/medium/high)", "duration_seconds", "reason"],
                "type": "execute"
            },
            "add_to_blacklist": {
                "name": "加入黑名单",
                "description": "将IP加入黑名单",
                "parameters": ["ip", "reason"],
                "type": "execute"
            },
            "add_to_whitelist": {
                "name": "加入白名单",
                "description": "将IP加入白名单",
                "parameters": ["ip", "reason"],
                "type": "execute"
            }
        }
        
        return {
            "success": True,
            "tools": tools_info,
            "total": len(tools_info),
            "query_tools": [k for k, v in tools_info.items() if v["type"] == "query"],
            "execute_tools": [k for k, v in tools_info.items() if v["type"] == "execute"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工具列表失败: {str(e)}")


# ========== 测试端点 ==========

@router.get("/test/demo")
async def test_demo():
    """
    测试端点：返回示例数据
    
    用于前端开发时的数据模拟
    """
    return {
        "success": True,
        "data": {
            "anomaly_type": "DDoS",
            "src_ip": "192.168.1.100",
            "timestamp": datetime.now().isoformat(),
            "knowledge_sources": [
                "DDoS攻击是指利用多个受控的计算机同时向目标发送大量请求...",
                "防御策略包括：限速处理、黑名单、流量清洗等...",
                "历史案例显示，及时的限速处理可以有效缓解攻击..."
            ],
            "knowledge_count": 3,
            "tools_used": ["search_knowledge", "query_acl_status", "query_rate_limit_history", "query_attack_history", "query_flow_stats", "get_defense_rules", "query_network_topology", "get_current_status"],
            "mcp_results": {
                "acl_status": {"ip": "192.168.1.100", "status": "normal"},
                "rate_limit_history": {"ip": "192.168.1.100", "is_currently_limited": False},
                "attack_history": {"ip": "192.168.1.100", "total_attacks": 0},
                "flow_stats": {"ip": "192.168.1.100", "total_packets": 0},
                "defense_rules": {"attack_type": "DDoS", "count": 3},
                "network_topology": {"topology_type": "star", "total_hosts": 8},
                "system_status": {"total_hosts": 8, "limited_ips_count": 0}
            },
            "analysis": {
                "risk_level": "高",
                "confidence": 85,
                "recommended_action": "rate_limit",
                "kbps": 256,
                "reason": "检测到典型的DDoS攻击特征，包括流量突增、包大小相似。建议立即限速以缓解攻击影响。",
                "evidence": [
                    "流量突增超过正常流量10倍",
                    "包大小固定为512字节",
                    "目标端口集中在80端口"
                ]
            },
            "agent_version": "2.0",
            "model_used": "mistral",
            "rag_enabled": True,
            "mcp_enabled": True
        },
        "message": "测试数据"
    }
