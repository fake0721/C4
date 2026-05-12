#!/usr/bin/env python
"""
v1_routes 提速版（缓存 + 索引 + 条数裁剪）
1. 缓存热点查询 60 秒
2. 流量/异常只返回最近 48 点（4 小时）
3. 不改 Ryu，只改中间层
"""
import random
import time
import requests
import uuid
import json
import os
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from functools import wraps
from dotenv import load_dotenv

from fastapi import APIRouter, Form, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import pymysql
import redis
from pathlib import Path

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

# 自定义JSON编码器，支持Decimal类型
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

router = APIRouter(prefix="/v1", tags=["v1"])

# ---------- 配置 ----------
RYU_BASE = "http://192.168.126.128:8080/v1"
TIMEOUT = 10
DB_CONFIG = {
    'host': '192.168.126.1',
    'user': 'root',
    'password': 'wcp13636938197HM',
    'db': 'network_management',
    'charset': 'utf8mb4'
}
# 强制使用真实数据（即使RYU控制器不可用也不返回模拟数据）
FORCED_REAL_DATA = True
REDIS_HOST = os.getenv("REDIS_HOST") or "127.0.0.1"
REDIS_PORT = int(os.getenv("REDIS_PORT") or "6379")
REDIS_DB = int(os.getenv("REDIS_DB") or "0")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None
CACHE_TTL  = 60            # 秒

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True,
)

# ---------- 模型 ----------
class ChatRequest(BaseModel):
    username: Optional[str] = None  # ✅ 新增：使用username字段
    user_id: Optional[str] = None   # ✅ 保留：向后兼容
    user: str  # 用户输入的消息内容
    has_uploaded_file: Optional[bool] = False  # 是否有上传的文件
    uploaded_filename: Optional[str] = None  # 上传的文件名
    conversation_history: Optional[List[Dict[str, str]]] = None  # 【新增】对话历史，用于上下文理解

class ThresholdBody(BaseModel):
    syn_threshold: Optional[int] = None
    udp_threshold: Optional[int] = None
    icmp_threshold: Optional[int] = None

# ---------- 工具 ----------

def proxy_get(path: str) -> Dict[str, Any]:
    """代理GET请求到RYU控制器，失败时返回错误"""
    try:
        print(f"[DEBUG] 尝试连接RYU控制器: {RYU_BASE}/{path}")
        r = requests.get(f"{RYU_BASE}/{path}", timeout=TIMEOUT)
        r.raise_for_status()
        print(f"[DEBUG] RYU控制器响应成功")
        return {"success": True, "data": r.json(), "message": "ok"}
    except Exception as e:
        print(f"[ERROR] RYU控制器请求失败: {e}")
        error_msg = f"无法获取真实数据: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "data": [], "message": error_msg}

def cache_key(func_name: str, *args) -> str:
    return f"v1:{func_name}:" + ":".join(map(str, args))


def _generate_default_response(user_message: str, tool_results: dict) -> str:
    """
    基于工具结果生成默认回答（降级方案）
    """
    response_parts = []
    
    # 分析工具结果并生成回答
    for tool_name, result in tool_results.items():
        if isinstance(result, dict):
            if tool_name == "query_acl_status":
                status = result.get("status", "unknown")
                if status == "black":
                    response_parts.append(f"该IP在黑名单中")
                elif status == "white":
                    response_parts.append(f"该IP在白名单中")
                else:
                    response_parts.append(f"该IP状态正常")
            
            elif tool_name == "query_attack_history":
                attacks = result.get("attacks", [])
                if attacks:
                    response_parts.append(f"该IP有{len(attacks)}条历史攻击记录")
                else:
                    response_parts.append(f"该IP没有历史攻击记录")
            
            elif tool_name == "query_flow_stats":
                packet_count = result.get("total_packets", 0)
                if packet_count > 0:
                    response_parts.append(f"该IP的流量统计：总包数{packet_count}")
            
            elif tool_name == "get_defense_rules":
                rules = result.get("rules", [])
                if rules:
                    response_parts.append(f"防御规则已获取，共{len(rules)}条")
            
            elif tool_name == "get_current_status":
                response_parts.append(f"系统状态已获取")
    
    if response_parts:
        return "根据实时数据分析：" + "；".join(response_parts)
    else:
        return "已调用MCP工具获取实时数据，但暂无具体分析结果"


def _get_default_tool_decision(user_message: str) -> str:
    """
    根据用户消息自动判断需要调用哪些MCP工具（降级方案）
    """
    import json
    import re
    
    message_lower = user_message.lower()
    tools = []
    
    # 提取IP地址
    ip_match = re.search(r'\d+\.\d+\.\d+\.\d+', user_message)
    ip = ip_match.group(0) if ip_match else None
    
    # 根据关键词判断需要调用的工具
    if any(keyword in message_lower for keyword in ['黑名单', '白名单', '名单', 'acl']):
        if ip:
            tools.append({"tool": "query_acl_status", "params": {"ip": ip}})
    
    if any(keyword in message_lower for keyword in ['限速', '速率', '限制', 'rate']):
        if ip:
            tools.append({"tool": "query_rate_limit_history", "params": {"ip": ip}})
    
    if any(keyword in message_lower for keyword in ['攻击', '异常', '历史', 'attack']):
        if ip:
            tools.append({"tool": "query_attack_history", "params": {"ip": ip}})
        tools.append({"tool": "get_defense_rules", "params": {}})
    
    if any(keyword in message_lower for keyword in ['流量', '统计', 'flow', 'stats']):
        if ip:
            tools.append({"tool": "query_flow_stats", "params": {"ip": ip}})
    
    if any(keyword in message_lower for keyword in ['拓扑', '网络', 'topology']):
        tools.append({"tool": "query_network_topology", "params": {}})
    
    if any(keyword in message_lower for keyword in ['状态', '系统', 'status']):
        tools.append({"tool": "get_current_status", "params": {}})
    
    # 如果没有匹配到任何工具，默认查询IP的所有信息
    if not tools and ip:
        tools = [
            {"tool": "query_acl_status", "params": {"ip": ip}},
            {"tool": "query_attack_history", "params": {"ip": ip}},
            {"tool": "query_flow_stats", "params": {"ip": ip}}
        ]
    
    # 如果还是没有工具，返回系统状态
    if not tools:
        tools = [{"tool": "get_current_status", "params": {}}]
    
    decision = {
        "tools": tools,
        "analysis": "使用默认工具决策"
    }
    
    return json.dumps(decision, ensure_ascii=False)

def cached_query(key: str, sql: str, params: tuple, ttl: int = 60) -> List[Dict]:
    """纯 MySQL 版，不使用 Redis"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            # datetime → 时间戳
            for row in rows:
                for k, v in row.items():
                    if isinstance(v, datetime):
                        row[k] = int(v.timestamp())
        return rows
    except Exception as e:
        logger.error(f"cached_query 失败: {e}")
        return []
    finally:
        if conn:
            conn.close()


# ---------- 1. 原有接口（提速版） ----------
@router.get("/summary")
async def get_summary():
    day = datetime.now().strftime('%Y-%m-%d')
    key = cache_key("summary", day)
    rows = cached_query(key,
                   "SELECT COUNT(*) FROM anomaly_log WHERE DATE(detect_time) = %s",
                   (day,))

    ano = rows[0]['COUNT(*)'] if rows else 0

    key2 = cache_key("summary_counts")
    rows2 = cached_query(key2,
                         "SELECT 'limit' as k,COUNT(*) FROM rate_limit_active UNION ALL "
                         "SELECT 'black',COUNT(*) FROM acl_entries WHERE list_type='black' UNION ALL "
                         "SELECT 'white',COUNT(*) FROM acl_entries WHERE list_type='white'",
                         (), ttl=30)
    counts = {r['k']: r['COUNT(*)'] for r in rows2}
    
    # 计算活跃主机数量 - 从异常日志中统计不同的源IP
    # ✅ 修复：先尝试查询dst_ip，如果失败则只查询src_ip
    key3 = cache_key("host_count", day)
    try:
        rows3 = cached_query(key3,
                            "SELECT COUNT(DISTINCT ip) as host_count FROM ("
                            "SELECT src_ip as ip FROM anomaly_log WHERE DATE(detect_time) = %s "
                            "UNION "
                            "SELECT dst_ip as ip FROM anomaly_log WHERE DATE(detect_time) = %s"
                            ") as combined_ips",
                            (day, day), ttl=300)  # 5分钟缓存
        host_count = rows3[0]['host_count'] if rows3 and len(rows3) > 0 else 0
    except Exception as e:
        # dst_ip字段不存在，只统计src_ip
        print(f"[WARNING] dst_ip字段不存在，只统计src_ip: {e}")
        rows3 = cached_query(key3,
                            "SELECT COUNT(DISTINCT src_ip) as host_count "
                            "FROM anomaly_log WHERE DATE(detect_time) = %s",
                            (day,), ttl=300)
        host_count = rows3[0]['host_count'] if rows3 and len(rows3) > 0 else 0
    
    return {"success": True,
            "data": {
                "today_anomalies": ano,
                "limit_count": counts.get('limit', 0),
                "black_count": counts.get('black', 0),
                "white_count": counts.get('white', 0),
                "switch_count": 1,  # 实时内存，不改
                "host_count": host_count  # 真实的活跃主机数量
            },
            "message": "ok"}

@router.get("/attack_sessions")
async def get_attack_sessions(
    hours: int = Query(12, description="获取最近N小时的攻击会话数据"),
    limit: int = Query(10, description="最大返回数据条数")
):
    """获取攻击会话数据（从attack_sessions表，已去重的攻击记录）"""
    try:
        print(f"[DEBUG] 转发攻击会话请求: hours={hours}, limit={limit}")
        r = requests.get(f"{RYU_BASE}/attack_sessions", params={"hours": hours, "limit": limit}, timeout=TIMEOUT)
        r.raise_for_status()
        print(f"[DEBUG] RYU控制器响应成功，返回 {len(r.json())} 条记录")
        return r.json()
    except Exception as e:
        print(f"[ERROR] 获取攻击会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/handled-sessions/count")
async def get_handled_sessions_count():
    """统计不同时间段的已处理攻击会话数量"""
    try:
        print(f"[DEBUG] 查询已处理攻击会话统计")
        r = requests.get(f"{RYU_BASE}/handled-sessions/count", timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] 已处理攻击会话统计: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] 获取已处理攻击会话统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 设备异常监控 --------------------------------------------------------------

@router.get("/device-anomalies")
async def proxy_device_anomalies(hours: int = Query(24, ge=1, le=168)):
    """转发设备异常查询到 RYU 控制器"""
    try:
        params = {"hours": hours}
        print(f"[DEBUG] 转发设备异常查询: params={params}")
        r = requests.get(f"{RYU_BASE}/device-anomalies", params=params, timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] 设备异常查询成功: count={result.get('count') if isinstance(result, dict) else 'unknown'}")
        return result
    except Exception as e:
        print(f"[ERROR] 获取设备异常失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/device-anomalies/{anomaly_id}")
async def proxy_update_device_anomaly(anomaly_id: int, payload: dict):
    """转发设备异常状态更新到 RYU 控制器"""
    try:
        print(f"[DEBUG] 更新设备异常状态: id={anomaly_id}, payload={payload}")
        r = requests.put(f"{RYU_BASE}/device-anomalies/{anomaly_id}", json=payload, timeout=TIMEOUT)
        
        # 404 意味着记录已被处理或不存在，对前端来说这是成功的
        if r.status_code == 404:
            print(f"[DEBUG] 异常 {anomaly_id} 不存在（已处理），返回成功响应")
            return {"success": True, "message": f"异常已处理", "affected_rows": 0}
        
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] 设备异常状态更新成功: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] 更新设备异常失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attack-sessions/count")
async def get_attack_sessions_count():
    """统计不同时间段的攻击会话数量"""
    try:
        print(f"[DEBUG] 转发攻击会话统计请求")
        r = requests.get(f"{RYU_BASE}/attack-sessions/count", timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] RYU控制器统计响应成功: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] 获取攻击会话统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/handled-ips")
async def get_handled_ips(days: int = Query(1, description="查询最近N天", ge=1, le=7)):
    """获取已处理的IP列表（从limit_sessions表）"""
    try:
        print(f"[DEBUG] 转发handled_ips请求: 最近{days}天")
        r = requests.get(f"{RYU_BASE}/handled-ips", params={"days": days}, timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] RYU控制器响应成功: 最近{days}天有{result.get('count', 0)}个IP被处理")
        return result
    except Exception as e:
        print(f"[ERROR] 获取handled_ips失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/attack-sessions/update-status")
async def update_attack_status(data: dict):
    """更新攻击会话的处理状态"""
    try:
        print(f"[DEBUG] 更新攻击状态: IP={data.get('ip')}, action={data.get('action')}")
        r = requests.post(f"{RYU_BASE}/attack-sessions/update-status", json=data, timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] 更新成功: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] 更新攻击状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/attack-sessions/trend")
async def get_attack_sessions_trend(hours: int = Query(24, description="查询最近N小时", ge=1, le=168)):
    """获取攻击会话的时间趋势数据（用于异常时间趋势图）"""
    try:
        print(f"[DEBUG] 转发attack_sessions_trend请求: 最近{hours}小时")
        r = requests.get(f"{RYU_BASE}/attack-sessions/trend", params={"hours": hours}, timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] RYU控制器响应成功: 获取到{len(result.get('data', []))}个时间点的趋势数据")
        return result
    except Exception as e:
        print(f"[ERROR] 获取attack_sessions_trend失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/anomalies")
async def get_anomalies(
    hours: int = Query(12, description="获取最近N小时的异常数据", ge=1, le=168),
    limit: int = Query(None, description="最大返回数据条数，不传则返回所有数据"),
    raw: bool = Query(False, description="是否返回原始数据（不去重）")
):
    """获取异常检测数据，使用RYU控制器的时间过滤路由，支持自定义时间范围"""
    try:
        # 使用RYU控制器的时间过滤参数（最近N小时）
        ryu_endpoint = f"{RYU_BASE}/anomalies"
        params = {'hours': hours}
        if limit is not None:
            params['limit'] = limit
        
        print(f"[DEBUG] 尝试连接RYU控制器获取异常数据: {ryu_endpoint}, 参数: {params}")
        r = requests.get(ryu_endpoint, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        raw_data = r.json()
        print(f"[DEBUG] RYU控制器异常数据响应成功，数据量: {len(raw_data)}")
        
        # 处理RYU返回的数据，转换为前端需要的格式
        processed_anomalies = []
        seen_attacks = set()  # 用于去重，但使用更细粒度的标识符
        
        for item in raw_data:
            src_ip = item.get('src_ip', '')
            anomaly_type = item.get('anomaly_type', '')
            detect_time = item.get('detect_time', '')
            details = item.get('details', '')
            
            # 解析时间
            try:
                dt = datetime.strptime(detect_time, '%Y-%m-%d %H:%M:%S')
            except:
                # 如果时间解析失败，使用当前时间
                print(f"[WARNING] 时间解析失败: {detect_time}")
                dt = datetime.now()
            
            # 解析details中的速率信息
            rate_kbps = 0
            if 'rate=' in details:
                try:
                    rate_str = details.split('rate=')[1].split()[0]
                    rate_kbps = float(rate_str)
                except Exception as e:
                    print(f"[DEBUG] 速率解析失败: {details}, 错误: {e}")
                    rate_kbps = 0
            
            # 创建更细粒度的唯一标识符，包含速率信息以减少过度去重
            try:
                # 使用秒级时间戳和速率信息，让更多不同的攻击事件能够显示
                second_key = dt.strftime('%Y-%m-%d %H:%M:%S')
                rate_range = int(rate_kbps / 10) * 10  # 按10kbps分组
                attack_key = f"{src_ip}_{anomaly_type}_{second_key}_{rate_range}"
            except:
                attack_key = f"{src_ip}_{anomaly_type}_{detect_time}_{rate_kbps}"
            
            if attack_key not in seen_attacks:
                seen_attacks.add(attack_key)
                
                # 转换时间格式为时间戳
                try:
                    timestamp = int(dt.timestamp() * 1000)  # 毫秒时间戳
                    time_str = dt.strftime('%H:%M:%S')  # 时间字符串
                except:
                    timestamp = int(datetime.now().timestamp() * 1000)
                    time_str = detect_time
                
                processed_item = {
                    'id': f"anomaly_{src_ip}_{timestamp}_{rate_kbps}",
                    'time': time_str,
                    'src_ip': src_ip,
                    'dst_ip': item.get('dst_ip', ''),
                    'type': anomaly_type,
                    'anomaly_type': anomaly_type,  # 兼容前端
                    'details': f"速率: {rate_kbps:.1f} kbps" if rate_kbps > 0 else details,
                    'timestamp': timestamp,
                    'detect_time': detect_time,
                    'rate_kbps': round(rate_kbps, 1),
                    'severity': 'high' if rate_kbps > 1000 else 'medium' if rate_kbps > 100 else 'low',
                    'status': 'detected'
                }
                processed_anomalies.append(processed_item)
        
        # 按时间排序，最新的在前
        processed_anomalies.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # 使用传入的limit参数限制返回的数据量，如果limit为None则返回所有数据
        if limit is not None and len(processed_anomalies) > limit:
            processed_anomalies = processed_anomalies[:limit]
            limit_msg = f"，限制返回{limit}条"
        else:
            limit_msg = "，返回所有数据"
        
        print(f"[DEBUG] RYU控制器返回 {len(raw_data)} 条最近{hours}小时的异常数据")
        print(f"[DEBUG] 去重后保留 {len(processed_anomalies)} 条异常事件{limit_msg}")
        
        # ✅ 返回实际的数据库记录数（未去重）和去重后的显示数据
        result = {
            "success": True, 
            "data": processed_anomalies, 
            "total_count": len(raw_data),  # 数据库中的实际记录数（未去重）
            "display_count": len(processed_anomalies),  # 去重后的显示数量
            "message": "ok"
        }
        
        # ✅ 如果请求原始数据，添加raw_data字段
        if raw:
            # 处理原始数据，但不去重
            raw_processed = []
            for item in raw_data:
                src_ip = item.get('src_ip', '')
                anomaly_type = item.get('anomaly_type', '')
                detect_time = item.get('detect_time', '')
                details = item.get('details', '')
                
                try:
                    dt = datetime.strptime(detect_time, '%Y-%m-%d %H:%M:%S')
                    timestamp = int(dt.timestamp() * 1000)
                    time_str = dt.strftime('%H:%M:%S')
                except:
                    timestamp = int(datetime.now().timestamp() * 1000)
                    time_str = detect_time
                
                # 解析速率
                rate_kbps = 0
                if 'rate=' in details:
                    try:
                        rate_str = details.split('rate=')[1].split()[0]
                        rate_kbps = float(rate_str)
                    except:
                        rate_kbps = 0
                
                raw_processed.append({
                    'src_ip': src_ip,
                    'dst_ip': item.get('dst_ip', ''),
                    'type': anomaly_type,
                    'anomaly_type': anomaly_type,
                    'timestamp': timestamp,
                    'detect_time': detect_time,
                    'rate_kbps': rate_kbps
                })
            result['raw_data'] = raw_processed
            print(f"[DEBUG] 添加原始数据（不去重）: {len(raw_processed)} 条")
        
        return result
        
    except Exception as e:
        print(f"[ERROR] RYU控制器异常数据请求失败: {e}")
        error_msg = f"获取异常检测数据失败: {str(e)}"
        return {"success": False, "data": [], "message": error_msg}

@router.get("/ports")
async def get_ports():
    return proxy_get("ports")

@router.get("/flowstats")
async def get_flowstats(port: str = "1", start: str = None, end: str = None):
    # 无时间参数 → 缓存加速 + 仅最近 4 小时（48 点）
    if start is None and end is None:
        day = datetime.now().strftime('%Y-%m-%d')
        key = cache_key("flowstats", day, port)
        # 适配数据库中src_port=0的数据
        rows = cached_query(key,
                            "SELECT HOUR(timestamp) as hour, "
                            "SUM(packet_count) as packets, SUM(byte_count) as bytes "
                            "FROM flow_stats "
                            "WHERE DATE(timestamp) = %s AND (src_port = %s OR src_port = 0 OR %s = 'all') "
                            "GROUP BY HOUR(timestamp) ORDER BY hour LIMIT 48",
                            (day, port, port), ttl=30)
        if rows:
            return {"success": True, "data": rows, "message": "ok"}
        else:
            return {"success": True, "data": [], "message": "当前无真实数据可用"}
    
    # 否则按原代理
    params = {"port": port}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    try:
        print(f"[DEBUG] 尝试连接RYU控制器获取flowstats: {RYU_BASE}/flowstats")
        r = requests.get(f"{RYU_BASE}/flowstats", params=params, timeout=TIMEOUT)
        r.raise_for_status()
        print(f"[DEBUG] RYU控制器flowstats响应成功")
        return {"success": True, "data": r.json(), "message": "ok"}
    except Exception as e:
        print(f"[ERROR] RYU控制器flowstats请求失败: {e}")
        return {"success": False, "data": [], "message": f"获取流量统计数据失败: {str(e)}"}

@router.get("/flow-trend")
async def get_flow_trend():
    """
    获取真实的网络流量趋势（时间序列）- 今日数据（0点至今）
    代理到RYU控制器的/v1/flow-trend接口
    """
    try:
        r = requests.get(f"{RYU_BASE}/flow-trend", timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()
        return result
    except Exception as e:
        print(f"[ERROR] RYU控制器flow-trend请求失败: {e}")
        return {"data": [], "count": 0, "error": str(e)}

@router.get("/portrate")
async def get_port_rate(port: str = "1", start: str = None, end: str = None):
    if start is None and end is None:
        day = datetime.now().strftime('%Y-%m-%d')
        key = cache_key("portrate", day, port)
        rows = cached_query(key,
                            "SELECT src_port, "
                            "SUM(byte_count)*8/60 as bps, "
                            "SUM(packet_count)/60 as pps "
                            "FROM flow_stats "
                            "WHERE DATE(timestamp) = %s AND timestamp >= DATE_SUB(NOW(), INTERVAL 1 MINUTE) "
                            "GROUP BY src_port LIMIT 50",
                            (day,), ttl=30)
        return {"success": True, "data": rows, "message": "ok"}
    params = {"port": port}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    try:
        r = requests.get(f"{RYU_BASE}/portrate", params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return {"success": True, "data": r.json(), "message": "ok"}
    except Exception as e:
        return {"success": False, "data": [], "message": str(e)}

@router.get("/protocolratio")
async def get_protocol_ratio(port: str = "1", start: str = None, end: str = None):
    if start is None and end is None:
        day = datetime.now().strftime('%Y-%m-%d')
        key = cache_key("protocolratio", day, port)
        rows = cached_query(key,
                            "SELECT protocol, SUM(byte_count) as bytes "
                            "FROM flow_stats "
                            "WHERE DATE(timestamp) = %s "
                            "GROUP BY protocol",
                            (day,), ttl=30)
        if rows:
            total = sum(r["bytes"] for r in rows) or 1.0
            for r in rows:
                r["value"] = round(r["bytes"] / total * 100, 2)
            return {"success": True, "data": rows, "message": "ok"}
        else:
            # 强制使用真实数据模式，返回空数据
            return {"success": True, "data": [], "message": "当前无真实数据可用"}
    
    params = {"port": port}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    try:
        print(f"[DEBUG] 尝试连接RYU控制器获取protocolratio: {RYU_BASE}/protocolratio")
        r = requests.get(f"{RYU_BASE}/protocolratio", params=params, timeout=TIMEOUT)
        r.raise_for_status()
        print(f"[DEBUG] RYU控制器protocolratio响应成功")
        return {"success": True, "data": r.json(), "message": "ok"}
    except Exception as e:
        print(f"[ERROR] RYU控制器protocolratio请求失败: {e}")
        return {"success": False, "data": [], "message": f"获取协议分布数据失败: {str(e)}"}

@router.post("/chat")
async def chat_command(req: ChatRequest):
    """
    聊天接口代理
    ✅ 支持username和user_id两种参数格式
    """
    try:
        # 构建发送给RYU控制器的数据
        # 优先使用username，如果没有则使用user_id
        payload = {
            "username": req.username or req.user_id,
            "user": req.user
        }
        
        print(f"[DEBUG] 转发聊天请求到RYU: username={payload['username']}, message={req.user[:50]}")
        
        r = requests.post(f"{RYU_BASE}/chat", json=payload, timeout=TIMEOUT)
        r.raise_for_status()
        
        print(f"[DEBUG] RYU响应成功")
        return r.json()
    except Exception as e:
        print(f"[ERROR] 聊天请求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/with-tools")
async def chat_with_tools(req: ChatRequest):
    """
    聊天接口 - 智能路由（通用对话 vs 数据查询）
    一次性返回完整响应（不使用流式）
    """
    import json
    import re
    
    try:
        from security_agent import get_agent_instance
        
        agent = get_agent_instance()
        user_message = req.user
        
        print(f"[DEBUG] 聊天请求: {user_message[:50]}")
        
        # 第1步：意图识别 - 判断是否需要调用工具
        intent_prompt = f"""
你是一个网络安全AI助手。你的名字叫小杜，分析用户的问题，判断是否需要调用数据库或知识库工具。

用户问题："{user_message}"

请判断这个问题属于以下哪一类：
1. 【通用对话】- 闲聊、问名字、问功能等，不需要查询数据
2. 【文档问题】- 用户问关于上传的文档内容、总结、分析等
3. 【数据查询】- 需要查询网络拓扑、IP信息、系统状态等

通用对话的例子：
- "你好"
- "你有没有名字？"
- "你能做什么？"
- "你是谁？"
- "你叫什么名字？"

文档问题的例子：
- "这个文档的主要内容是什么？"
- "帮我总结一下这个文档"
- "文档里讲了什么？"
- "这个PDF的重点是什么？"

数据查询的例子：
- "h1的IP地址是多少？"
- "192.168.1.100最近有没有异常？"
- "当前系统状态如何？"
- "查看网络拓扑"

请直接回答：【通用对话】或【文档问题】或【数据查询】
"""
        
        intent_response = agent._call_llm(intent_prompt, temperature=0.3)
        is_data_query = "数据查询" in intent_response
        is_document_question = "文档问题" in intent_response
        
        print(f"[DEBUG] 意图识别结果: {intent_response}")
        
        # 【重要】如果用户上传了文件，优先识别为文档问题
        if req.has_uploaded_file or req.uploaded_filename:
            print(f"[DEBUG] 检测到用户上传了文件，强制识别为文档问题")
            is_document_question = True
            is_data_query = False
        
        # 如果是文档问题，从知识库检索文档内容
        if is_document_question:
            print(f"[DEBUG] 识别为文档问题，从知识库检索")
            
            # 【重要】如果用户上传了文件，优先搜索该文件的内容
            if req.uploaded_filename:
                print(f"[DEBUG] 用户上传了文件: {req.uploaded_filename}，优先搜索该文件内容")
                # 使用上传文件名作为搜索关键词
                search_query = f"{req.uploaded_filename} {user_message}"
            else:
                search_query = user_message
            
            # 从知识库检索相关文档
            doc_search_result = agent._tool_search_knowledge(search_query)
            
            if doc_search_result['success'] and doc_search_result['data']:
                # 基于检索到的文档内容回答
                doc_content = "\n".join(doc_search_result['data'])
                doc_prompt = f"""
【系统设定】
你是一个友好、专业的网络安全AI助手，名字叫小杜。

【用户问题】
{user_message}

【相关文档内容】
{doc_content}

【回答要求】
1. 基于上面的文档内容回答用户的问题
2. 如果用户要求总结，请用简洁的语言总结文档的主要内容
3. 如果用户问文档讲了什么，请提取关键信息
4. 使用表情符号增加亲切感（如📄、✨、💡等）
5. 保持专业但友好的语气

请基于文档内容回答用户的问题：
"""
                final_response = agent._call_llm(doc_prompt, temperature=0.6)
                
                return {
                    "status": "success",
                    "response": final_response,
                    "tools_called": ["search_knowledge"],
                    "tool_results": {"search_knowledge": doc_search_result['data']},
                    "message": "ok"
                }
            else:
                # 知识库中没有相关文档
                no_doc_response = "抱歉，我在知识库中没有找到相关的文档内容。😊 你可以先上传文档，然后我就能基于文档内容为你回答问题了！"
                return {
                    "status": "success",
                    "response": no_doc_response,
                    "tools_called": [],
                    "tool_results": {},
                    "message": "ok"
                }
        
        # 如果是通用对话，直接用LLM回答
        if not is_data_query:
            print(f"[DEBUG] 识别为通用对话，直接LLM回答")
            general_prompt = f"""
【系统设定】
你是一个友好、活泼的网络安全AI助手。
你的名字是"小杜"，这是你的唯一身份。
你不是Qwen、ChatGPT或任何其他AI助手。
你就是小杜。

你的性格特点：
- 热情友好，充满正能量
- 喜欢使用表情符号来增加亲切感
- 回答时要有温度，给人情绪价值
- 既专业又不失幽默感

【用户问题】
{user_message}

【回答要求】
1. 用中文简洁友好地回答用户的问题
2. 在回答中适当使用表情符号（如😊、✨、🎯、💪等）来增加情感
3. 如果用户问你的名字，你可以回答："我叫小杜呀 😊 很高兴认识你！"
4. 如果用户问你是谁，你可以回答："我是小杜 ✨ 一个专业又友好的网络安全AI助手！"
5. 如果用户问你能做什么，要热情地介绍你的功能，比如："我可以帮你查询网络拓扑 🔍、分析安全状态 🛡️、回答网络安全问题 💡 等等！"
6. 不要提及任何其他AI助手的名字
7. 始终保持"小杜"这个身份
8. 回答要温暖有趣，不要太生硬

现在请回答用户的问题，记得加上表情符号和温暖的语气：
"""
            final_response = agent._call_llm(general_prompt, temperature=0.7)
            
            return {
                "status": "success",
                "response": final_response,
                "tools_called": [],
                "tool_results": {},
                "message": "ok"
            }
        
        # 如果是数据查询，调用MCP工具
        print(f"[DEBUG] 识别为数据查询，调用MCP工具")
        
        # 【新增】完整日志用户问题
        print(f"[DEBUG] 聊天请求（完整）: {user_message}")
        
        # 【新增】提取对话历史上下文
        conversation_context = ""
        if req.conversation_history and len(req.conversation_history) > 0:
            # 获取最近的5条对话历史（避免上下文过长）
            recent_history = req.conversation_history[-5:]
            conversation_context = "【对话历史】\n"
            for msg in recent_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    conversation_context += f"用户: {content}\n"
                else:
                    conversation_context += f"小杜: {content}\n"
            conversation_context += "\n"
            print(f"[DEBUG] 对话历史上下文:\n{conversation_context}")
        
        # 第2步：让LLM决定需要调用哪些工具
        tool_decision_prompt = f"""
你是一个网络安全分析助手。用户提出了以下问题：

{conversation_context}
【当前问题】
"{user_message}"

根据这个问题和对话历史，判断需要调用哪些MCP工具来获取实时数据。
【关键】如果用户的问题很简洁（如"改成256"），要根据对话历史推断用户的真实意图。例如：
- 如果前面讨论的是IP 192.168.1.104，用户说"改成256"，应该理解为"把192.168.1.104的限速改为256kbps"

可用的MCP工具有：

【查询工具】
1. query_acl_status(ip) - 查询单个IP的黑白名单状态
   参数：ip (必需) - 要查询的IP地址
   返回：该IP是否在黑名单、白名单或正常状态
   
1.5. query_acl_blacklist() - 查询所有黑名单IP（完整列表）
   参数：无
   返回：所有黑名单IP的完整列表，包括添加时间
   【关键】用户问"黑名单里有什么IP"或"查看黑名单"时，应该调用这个工具，而不是query_acl_status
   
1.6. query_acl_whitelist() - 查询所有白名单IP（完整列表）
   参数：无
   返回：所有白名单IP的完整列表，包括添加时间
   【关键】用户问"白名单里有什么IP"或"查看白名单"时，应该调用这个工具，而不是query_acl_status
   
2. query_rate_limit_history(ip, reason) - 查询限速历史
   参数：ip (可选) - 要查询的IP地址；reason (可选) - 限速原因（如"SYN Flood"）
   
3. query_attack_history(ip, attack_type) - 查询攻击历史
   参数：ip (可选) - 要查询的IP地址；attack_type (可选) - 攻击类型（如"SYN Flood"、"ARP欺骗"）
   
4. query_flow_stats(ip) - 查询IP的流量统计
   参数：ip (必需) - 要查询的IP地址
   
5. get_defense_rules(attack_type) - 获取防御规则
   参数：attack_type (可选) - 攻击类型
   
6. query_device_anomalies(device_type, anomaly_type, severity) - 查询设备异常
   参数：device_type (可选) - 设备类型；anomaly_type (可选) - 异常类型；severity (可选) - 严重程度
   
7. query_network_topology() - 查询网络拓扑
   参数：无
   
8. get_current_status() - 获取系统状态
   参数：无

【执行工具】
9. add_to_blacklist(ip, reason) - 将IP加入黑名单
   参数：ip (必需) - 要加黑的IP地址；reason (可选) - 原因
   
10. remove_from_blacklist(ip, reason) - 从黑名单删除IP
    参数：ip (必需) - 要删除的IP地址；reason (可选) - 原因
    
11. add_to_whitelist(ip, reason) - 将IP加入白名单
    参数：ip (必需) - 要加白的IP地址；reason (可选) - 原因
    
12. remove_from_whitelist(ip, reason) - 从白名单删除IP
    参数：ip (必需) - 要删除的IP地址；reason (可选) - 原因
    
13. apply_rate_limit(ip, level, duration_seconds, reason) - 对IP进行【新的】限速（IP当前没有限速时调用）
    参数：ip (必需) - 要限速的IP；level (可选) - 限速档位（"low"=256kbps, "medium"=1024kbps, "high"=2048kbps）；duration_seconds (可选) - 限速时长（秒）；reason (可选) - 原因
    【关键】用户说"限速192.168.1.102"或"给192.168.1.102限速"或"对192.168.1.102进行限速"时，应该调用这个工具
    
14. release_rate_limit(ip, reason) - 解除对IP的限速
    参数：ip (必需) - 要解除限速的IP；reason (可选) - 原因
    
15. modify_rate_limit_duration(ip, duration_seconds, reason) - 修改【已有限速】的时长（IP已经被限速时调用）
    参数：ip (必需) - 要修改的IP；duration_seconds (必需) - 新的限速时长（秒）；reason (可选) - 原因
    【关键】用户说"延长192.168.1.102的限速时间"或"把192.168.1.102的限速延长10分钟"时，应该调用这个工具
    
16. modify_rate_limit_kbps(ip, kbps, reason) - 修改【已有限速】的速率（IP已经被限速时调用）
    参数：ip (必需) - 要修改的IP；kbps (必需) - 新的限速数值（256/512/1024/2048 kbps）；reason (可选) - 原因
    【关键】用户说"降低192.168.1.102的限速到256kbps"或"把192.168.1.102的限速改为512kbps"时，应该调用这个工具

【重要提示】
查询工具使用示例：
- 如果用户问"黑名单里有什么IP"或"查看黑名单"或"黑名单都有哪些"，应该调用 query_acl_blacklist()，而不是query_acl_status
- 如果用户问"白名单里有什么IP"或"查看白名单"或"白名单都有哪些"，应该调用 query_acl_whitelist()，而不是query_acl_status
- 如果用户问"192.168.1.102这个IP在不在黑名单"或"查询某个IP的状态"，应该调用 query_acl_status(ip="192.168.1.102")
- 如果用户问"最近有没有什么IP发起了ARP欺骗攻击"，应该调用 query_attack_history(attack_type="ARP欺骗")
- 如果用户问"最近因为SYN Flood限速的IP有哪些"，应该调用 query_rate_limit_history(reason="SYN Flood")
- 如果用户问"192.168.1.102这个IP有没有限速记录"，应该调用 query_rate_limit_history(ip="192.168.1.102")
- 如果用户问"最近有没有什么设备异常"，应该调用 query_device_anomalies()

【执行工具使用规则】- 优先级最高，用户说执行命令时立即调用，不要先查询：
- 如果用户说"拉黑192.168.1.102"或"把192.168.1.102加入黑名单"或"加黑192.168.1.102"，立即调用 add_to_blacklist(ip="192.168.1.102", reason="用户请求")，不要先查询
- 如果用户说"解除192.168.1.102的黑名单"或"把192.168.1.102从黑名单删除"或"取消黑名单192.168.1.102"，立即调用 remove_from_blacklist(ip="192.168.1.102", reason="用户请求")，不要先查询

【限速工具的智能判断】- 关键：区分"应用新限速"和"修改已有限速"：
- 【新限速】如果用户说"限速192.168.1.102"或"给192.168.1.102限速"或"对192.168.1.102进行限速"或"把192.168.1.102加入限速"或"192.168.1.102加入限速"
  → 调用 apply_rate_limit(ip="192.168.1.102", level="medium", duration_seconds=300, reason="用户请求")
  → 这是应用【新的】限速，IP当前可能没有限速
  
- 【修改限速速率】如果用户说"把192.168.1.102的限速改为256kbps"或"降低192.168.1.102的限速到512kbps"或"修改192.168.1.102的限速为1024kbps"或"把192.168.1.102的速度改为256"
  → 调用 modify_rate_limit_kbps(ip="192.168.1.102", kbps=256或512或1024或2048, reason="用户请求")
  → 这是修改【已有】限速的速率，IP当前必须已经被限速
  
- 【修改限速时长】如果用户说"延长192.168.1.102的限速时间"或"把192.168.1.102的限速延长10分钟"或"修改192.168.1.102的限速时长为600秒"
  → 调用 modify_rate_limit_duration(ip="192.168.1.102", duration_seconds=600, reason="用户请求")
  → 这是修改【已有】限速的时长，IP当前必须已经被限速

- 【解除限速】如果用户说"解除192.168.1.102的限速"或"取消对192.168.1.102的限速"或"解除192.168.1.102限速"
  → 调用 release_rate_limit(ip="192.168.1.102", reason="用户请求")

【代词识别】- 处理简洁表述和代词：
- 如果用户说"修改一下，把他的速度改为256"，应该根据对话历史推断"他"指的是哪个IP
  例如：前面讨论的是192.168.1.105，用户说"把他的速度改为256"，应该理解为"把192.168.1.105的限速改为256kbps"
- 如果用户说"改成256"或"改为256"或"速度改为256"，应该从对话历史中找到最近提到的IP，然后调用modify_rate_limit_kbps

- 【关键】执行工具不需要先查询，直接执行即可。只有当用户问"查看"、"看看"、"有哪些"、"列出"时才调用查询工具

【防止AI幻觉的工具调用规则】
- 只调用用户明确要求的工具，不要凭空编造
- 如果用户说"拉黑192.168.1.102"，应该调用add_to_blacklist，而不是先调用query_acl_status再说"已经在黑名单中"
- 如果用户要求"找出安全的IP"，应该先调用query_acl_status或query_attack_history来获取数据，然后基于实际数据判断
- 不要在没有数据的情况下编造IP列表
- 如果数据不足以回答用户问题，明确说"数据不足"或"需要更多信息"

请返回一个JSON格式的决策，包含：
1. 需要调用的工具列表
2. 每个工具的参数
3. 简短的分析说明

返回格式：
{{
    "tools": [
        {{"tool": "工具名", "params": {{"参数名": "参数值"}}}},
        ...
    ],
    "analysis": "你的分析说明"
}}

只返回JSON，不要其他内容。
"""
        
        try:
            tool_decision = agent._call_llm(tool_decision_prompt, temperature=0.3)
        except Exception as e:
            print(f"⚠️ LLM调用失败: {e}，使用默认工具决策")
            tool_decision = _get_default_tool_decision(user_message)
        
        # 【优化】完整输出工具决策（如果太长则截断显示）
        if len(tool_decision) > 500:
            print(f"[DEBUG] LLM工具决策（完整）: {tool_decision}")
        else:
            print(f"[DEBUG] LLM工具决策: {tool_decision}")
        
        # 第3步：解析LLM的决策
        try:
            json_match = re.search(r'\{.*\}', tool_decision, re.DOTALL)
            if json_match:
                tool_decision_data = json.loads(json_match.group())
            else:
                tool_decision_data = {"tools": [], "analysis": "无法解析工具决策"}
        except Exception as e:
            print(f"[ERROR] JSON解析失败: {e}")
            tool_decision_data = {"tools": [], "analysis": "JSON解析失败"}
        
        # 【新增】第3.5步：从用户问题中提取时间范围
        def extract_time_range(question: str, tools_list: list) -> int:
            """
            从用户问题中提取时间范围（天数）
            【智能判断】：
            - 如果查询的是"黑名单"、"白名单"等持久化列表，返回-1表示不限制时间范围
            - 如果查询的是"攻击历史"、"限速历史"等时间序列数据，才使用时间范围
            - 如果用户明确指定了时间范围，则使用用户指定的范围
            """
            import re
            
            # 【关键】检查是否是持久化列表查询（黑名单、白名单、当前状态）
            # 这些查询不应该受时间范围限制
            persistent_list_keywords = ['黑名单', '白名单', '当前', '现在', '都有', '列表']
            is_persistent_list_query = any(keyword in question for keyword in persistent_list_keywords)
            
            # 检查调用的工具是否是持久化列表工具
            persistent_tools = ['get_current_status', 'query_acl_status', 'query_acl_blacklist', 'query_acl_whitelist']
            is_persistent_tool = any(tool in tools_list for tool in persistent_tools)
            
            # 如果是持久化列表查询且用户没有明确指定时间范围，返回-1表示不限制
            if (is_persistent_list_query or is_persistent_tool) and not any(keyword in question for keyword in ['最近', '一周', '一月', '一年']):
                print(f"[⏰] 检测到持久化列表查询，不限制时间范围")
                return -1
            
            # 检查是否有明确的时间范围
            # 最近N天
            match = re.search(r'最近\s*(\d+)\s*天', question)
            if match:
                days = int(match.group(1))
                print(f"[⏰] 从问题中提取时间范围: 最近{days}天")
                return days
            
            # 【修复】一周/一星期（包括"最近"和不包括"最近"的情况）
            if '一周' in question or '一星期' in question or '最近一周' in question or '最近一星期' in question or '这一周' in question or '这一星期' in question:
                print(f"[⏰] 从问题中提取时间范围: 最近7天")
                return 7
            
            # 【修复】一个月/一月（包括各种表述）
            if '一个月' in question or '一月' in question or '最近一个月' in question or '最近一月' in question or '这个月' in question or '这一个月' in question:
                print(f"[⏰] 从问题中提取时间范围: 最近30天")
                return 30
            
            # 【修复】一年（包括各种表述）
            if '一年' in question or '最近一年' in question or '这一年' in question or '这一年' in question:
                print(f"[⏰] 从问题中提取时间范围: 最近365天")
                return 365
            
            # 具体日期范围（例如：2025-11-01到2025-11-14）
            date_match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', question)
            if date_match:
                print(f"[⏰] 从问题中提取具体日期: {date_match.group()}")
                # 这里可以返回具体的日期范围，暂时返回30天作为默认
                return 30
            
            # 【修复】默认：最近7天（而不是3天）
            # 但对于持久化列表查询，默认不限制时间范围
            if is_persistent_list_query or is_persistent_tool:
                print(f"[⏰] 持久化列表查询，不限制时间范围")
                return -1
            
            print(f"[⏰] 未指定时间范围，使用默认: 最近7天")
            return 7
        
        # 第4步：自动调用这些工具
        tool_results = {}
        tools_list = [t.get("tool") for t in tool_decision_data.get("tools", [])]
        
        # 提取时间范围（需要先获取tools_list）
        time_range_days = extract_time_range(user_message, tools_list)
        
        for tool_call in tool_decision_data.get("tools", []):
            tool_name = tool_call.get("tool")
            params = tool_call.get("params", {})
            
            try:
                if tool_name == "query_acl_status":
                    result = agent._tool_query_acl_status(params.get("ip", ""))
                elif tool_name == "query_acl_blacklist":
                    result = agent._tool_query_acl_blacklist()
                elif tool_name == "query_acl_whitelist":
                    result = agent._tool_query_acl_whitelist()
                elif tool_name == "query_rate_limit_history":
                    # 【修改】支持按IP或按限速原因查询，传入时间范围
                    result = agent._tool_query_rate_limit_history(
                        ip=params.get("ip", ""),
                        reason=params.get("reason", ""),
                        days=time_range_days
                    )
                elif tool_name == "query_attack_history":
                    # 【修改】支持按IP或按攻击类型查询，传入时间范围
                    result = agent._tool_query_attack_history(
                        ip=params.get("ip", ""),
                        attack_type=params.get("attack_type", ""),
                        days=time_range_days
                    )
                elif tool_name == "query_flow_stats":
                    result = agent._tool_query_flow_stats(params.get("ip", ""))
                elif tool_name == "query_device_anomalies":
                    # 【新增】查询设备异常，支持多条件查询
                    result = agent._tool_query_device_anomalies(
                        device_type=params.get("device_type", ""),
                        anomaly_type=params.get("anomaly_type", ""),
                        severity=params.get("severity", ""),
                        days=time_range_days
                    )
                elif tool_name == "get_defense_rules":
                    result = agent._tool_get_defense_rules(params.get("attack_type"))
                elif tool_name == "query_network_topology":
                    result = agent._tool_query_network_topology()
                elif tool_name == "get_current_status":
                    result = agent._tool_get_current_status()
                # 【新增】执行工具（修改数据库）
                elif tool_name == "add_to_blacklist":
                    result = agent._tool_add_to_blacklist(
                        ip=params.get("ip", ""),
                        reason=params.get("reason", "管理员操作")
                    )
                elif tool_name == "remove_from_blacklist":
                    result = agent._tool_remove_from_blacklist(
                        ip=params.get("ip", ""),
                        reason=params.get("reason", "管理员解除")
                    )
                elif tool_name == "add_to_whitelist":
                    result = agent._tool_add_to_whitelist(
                        ip=params.get("ip", ""),
                        reason=params.get("reason", "管理员操作")
                    )
                elif tool_name == "remove_from_whitelist":
                    result = agent._tool_remove_from_whitelist(
                        ip=params.get("ip", ""),
                        reason=params.get("reason", "管理员解除")
                    )
                elif tool_name == "apply_rate_limit":
                    result = agent._tool_apply_rate_limit(
                        ip=params.get("ip", ""),
                        level=params.get("level", "medium"),
                        duration_seconds=int(params.get("duration_seconds", 300)),
                        reason=params.get("reason", "管理员限速")
                    )
                elif tool_name == "release_rate_limit":
                    result = agent._tool_release_rate_limit(
                        ip=params.get("ip", ""),
                        reason=params.get("reason", "管理员解除")
                    )
                elif tool_name == "modify_rate_limit_duration":
                    result = agent._tool_modify_rate_limit_duration(
                        ip=params.get("ip", ""),
                        duration_seconds=int(params.get("duration_seconds", 300)),
                        reason=params.get("reason", "修改限速时长")
                    )
                elif tool_name == "modify_rate_limit_kbps":
                    result = agent._tool_modify_rate_limit_kbps(
                        ip=params.get("ip", ""),
                        kbps=int(params.get("kbps", 1024)),
                        reason=params.get("reason", "修改限速数值")
                    )
                else:
                    result = {"success": False, "error": f"未知工具: {tool_name}"}
                
                # 【修复】提取数据，确保返回有意义的内容
                if result.get("success"):
                    # 工具执行成功，返回data字段
                    data = result.get("data", {})
                    if not data or (isinstance(data, dict) and len(data) == 0):
                        # 如果data为空但成功，返回成功消息
                        data = {
                            "success": True,
                            "message": result.get("message", f"{tool_name}执行成功"),
                            "tool": tool_name
                        }
                        print(f"[⚠️] 工具 {tool_name} 返回的data为空，使用成功消息")
                else:
                    # 工具执行失败，返回错误信息
                    data = {
                        "success": False,
                        "error": result.get("error", "未知错误"),
                        "tool": tool_name
                    }
                    print(f"[⚠️] 工具 {tool_name} 执行失败: {result.get('error')}")
                
                tool_results[tool_name] = data
                print(f"[DEBUG] 工具调用完成: {tool_name} - 返回数据量: {len(str(data))}")
            except Exception as e:
                tool_results[tool_name] = {"error": str(e), "tool": tool_name}
                print(f"[ERROR] 工具调用失败: {tool_name} - {e}")
        
        # 第5步：压缩tool_results数据，防止LLM超时
        # 【优化】对大数据量进行摘要处理
        def compress_tool_results(tool_results):
            """压缩工具结果，防止数据过大导致LLM超时"""
            from collections import Counter
            compressed = {}
            for tool_name, data in tool_results.items():
                if isinstance(data, dict):
                    # 对于字典类型的数据
                    if 'attacks' in data and isinstance(data['attacks'], list):
                        # 攻击历史：保留前20条 + 按攻击类型统计
                        attacks = data['attacks'][:20]
                        attack_types = Counter([a.get('type', 'unknown') for a in data['attacks']])
                        compressed[tool_name] = {
                            **{k: v for k, v in data.items() if k != 'attacks'},
                            'attacks': attacks,
                            'attack_type_summary': dict(attack_types),
                            'note': f'(仅显示前20条，共{data.get("total_attacks", len(data.get("attacks", [])))}条)'
                        }
                    elif 'records' in data and isinstance(data['records'], list):
                        # 限速历史：保留前20条 + 按限速原因统计（关键！）
                        records = data['records'][:20]
                        # 【新增】统计所有限速原因及其出现次数
                        reasons = Counter([r.get('reason', 'unknown') for r in data['records']])
                        compressed[tool_name] = {
                            **{k: v for k, v in data.items() if k != 'records'},
                            'records': records,
                            'reason_summary': dict(reasons),  # 所有限速原因的统计
                            'note': f'(仅显示前20条，共{data.get("count", len(data.get("records", [])))}条)'
                        }
                    elif 'anomalies' in data and isinstance(data['anomalies'], list):
                        # 设备异常：保留前20条 + 按异常类型统计
                        anomalies = data['anomalies'][:20]
                        anomaly_types = Counter([a.get('anomaly_type', 'unknown') for a in data['anomalies']])
                        compressed[tool_name] = {
                            **{k: v for k, v in data.items() if k != 'anomalies'},
                            'anomalies': anomalies,
                            'anomaly_type_summary': dict(anomaly_types),
                            'note': f'(仅显示前20条，共{data.get("total_anomalies", len(data.get("anomalies", [])))}条)'
                        }
                    elif 'limits' in data and isinstance(data['limits'], list):
                        # 当前限速：保留前20条 + 按限速原因统计
                        limits = data['limits'][:20]
                        reasons = Counter([l.get('reason', 'unknown') for l in data['limits']])
                        compressed[tool_name] = {
                            **{k: v for k, v in data.items() if k != 'limits'},
                            'limits': limits,
                            'reason_summary': dict(reasons),
                            'note': f'(仅显示前20条，共{len(data.get("limits", []))}条)'
                        }
                    else:
                        compressed[tool_name] = data
                else:
                    compressed[tool_name] = data
            return compressed
        
        # 压缩数据
        tool_results = compress_tool_results(tool_results)
        print(f"[✅] 数据压缩完成，压缩后大小: {len(str(tool_results))} 字符")
        
        # 第5步：让LLM基于工具结果回答用户问题
        # 分析用户问题的意图
        question_lower = user_message.lower()
        is_asking_about_ip = any(keyword in question_lower for keyword in ['192.168', '查看', '查询', '检查', '状态', '异常', '攻击'])
        is_asking_about_topology = any(keyword in question_lower for keyword in ['拓扑', '网络', '结构', '架构', '设备', '连接', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8', '主机', '地址', 'ip'])
        is_asking_about_rules = any(keyword in question_lower for keyword in ['规则', '防御', '防护', '检测'])
        is_asking_about_status = any(keyword in question_lower for keyword in ['系统状态', '当前状态', '整体状态', '系统'])
        
        # 根据意图构建不同的提示词
        if is_asking_about_topology:
            # 从tool_results中获取拓扑信息（来自RAG知识库）
            topology_data = tool_results.get('query_network_topology', {})
            topology_info = topology_data.get('topology_info', '未能获取拓扑信息')
            host_mapping = topology_data.get('host_mapping', {})
            
            # 构建主机映射表字符串
            host_mapping_str = ""
            if host_mapping:
                host_mapping_str = "【从知识库获取的主机IP映射表】\n"
                for host, ip in sorted(host_mapping.items()):
                    host_mapping_str += f"- {host}: {ip}\n"
            
            focus_instruction = f"""
用户问的是网络拓扑结构或主机信息。请基于以下从知识库获取的信息回答：

{host_mapping_str}

【详细拓扑信息】
{topology_info}

回答要求：
1. 如果用户问某个主机的IP地址（如h1、h2等），必须从上面的映射表中查找并返回准确的IP地址
2. 如果用户问拓扑结构，请详细描述网络拓扑、交换机、主机配置等
3. 必须使用从知识库获取的信息，这是准确的网络配置
4. 不要说"没有记录"或"未能获取"，知识库中有完整的映射信息
5. 回答必须准确，不要猜测或编造IP地址
"""
        elif is_asking_about_rules:
            # 从tool_results中获取防御规则（来自RAG知识库）
            rules_data = tool_results.get('get_defense_rules', {})
            rules_info = rules_data.get('rules', [])
            
            rules_str = ""
            if isinstance(rules_info, list) and len(rules_info) > 0:
                rules_str = "【从知识库获取的防御规则】\n"
                for rule in rules_info:
                    rules_str += f"- {rule}\n"
            
            focus_instruction = f"""
用户问的是防御规则。请基于以下从知识库获取的防御规则信息回答：

{rules_str}

回答要求：
1. 只回答关于防御规则的信息
2. 使用知识库中的防御规则数据
3. 不要涉及具体IP地址的分析
4. 简洁明了地解释规则
"""
        elif is_asking_about_status:
            focus_instruction = """
用户问的是系统整体状态。请基于获得的实时数据回答系统级别的信息，包括：
- 当前限速的IP数量
- 黑名单中的IP数量（这是系统级别的统计，不是特定IP的状态）
- 白名单中的IP数量（这是系统级别的统计，不是特定IP的状态）
- 最近的异常活动
- 系统整体安全状态

不要过度关注单个IP地址。
【重要】区分清楚：
- "系统黑名单有4条"是指整个系统的黑名单共有4条记录
- "192.168.1.102在黑名单中"是指这个特定IP在黑名单中
- 这两个概念完全不同，不要混淆！
"""
        elif is_asking_about_ip:
            focus_instruction = """
用户问的是关于某个IP地址的信息。请专注于分析这个IP的数据，包括：
   - 黑白名单状态
   - 是否正在被限速
   - 历史攻击记录
   - 流量统计信息
不要讨论其他IP地址。
"""
        else:
            focus_instruction = """
请直接回答用户的问题，基于获得的数据进行分析。
"""
        
        final_prompt = f"""
{conversation_context}
【当前问题】
"{user_message}"

【数据说明】
- 当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 查询范围：最近7天的数据
- 如果查询结果为空或数据量少，可能是因为：
  1. 该IP在最近7天内确实没有异常活动
  2. 或者异常活动已被处理/清除
  3. 请根据实际数据做出判断

你已经获得了以下实时数据：
{json.dumps(tool_results, ensure_ascii=False, indent=2, cls=DecimalEncoder)}

{focus_instruction}

回答要求：
1. 【核心】直接回答用户的问题，抓住用户的真实需求和关键信息点

【新增】【上下文理解规则】- 根据对话历史推断用户的真实意图：
- 如果用户的问题很简洁（如"改成256"、"改成512"），必须根据对话历史推断用户指的是哪个IP
- 例如：如果前面讨论的是IP 192.168.1.104，用户说"改成256"，应该理解为"把192.168.1.104的限速改为256kbps"
- 【关键】不要问用户"你指的是哪个IP"，直接从对话历史中提取IP信息
- 【关键】如果对话历史中提到了某个IP，后续用户的操作都默认是针对这个IP的，除非用户明确说了另一个IP
- 【关键】不要说"该IP当前没有在限速名单里"这样的话，而是直接执行用户的命令

2. 【重要】理解数据的含义：
   - query_acl_status返回的是**特定IP**的黑白名单状态（"black"、"white"或"normal"）
   - get_current_status返回的是**系统级别**的统计（黑名单总数、白名单总数等）
   - 这两个数据完全不同，不要混淆！
   - 例如：即使系统黑名单有4条，也不代表某个特定IP在黑名单中

【防止AI幻觉的关键规则】

【新增】【自我认知和避免歧义】
- 你是一个AI助手，名字叫"小杜"，你不是一个IP地址
- 当用户说"黑名单小杜"或"限速小杜"时，用户是在用非正式的语言说"黑名单里的IP"或"限速列表"，不是在问你是不是某个IP
- 【关键】不要问用户"小杜是不是某个IP"这样的问题，这样会显得很傻
- 【关键】不要问用户澄清问题，直接理解用户的真实意图并执行
- 直接理解用户的真实意图：
  - "黑名单小杜" → 用户想查看黑名单里有什么IP
  - "限速小杜" → 用户想查看限速列表
  - "查看一下小杜" → 用户想查看系统状态
  - "小杜是不是某个IP有点那个了" → 用户是在问某个IP是否有异常，直接查询这个IP的状态
- 【重要】用户用"小杜"这个词时，通常是在非正式地指代"系统"或"列表"，不是在问你是不是某个IP
- 【重要】如果用户的表述不够清晰，你应该根据上下文和常识推断用户的真实意图，而不是反问用户

3. 【严格】区分"执行操作"和"查询状态"：
   - 用户说"拉黑192.168.1.102" = 用户要求执行拉黑操作，不是说这个IP已经被拉黑了
   - 用户说"把安全的5个IP给我挑出来" = 用户要求你从数据中找出安全的IP，不是说有5个安全的IP
   - 操作前：先说明当前状态（如"192.168.1.102目前是normal状态"）
   - 操作后：说明操作结果（如"已成功拉黑，现在状态是black"）
   
4. 【严格】只基于实际数据回答，不要凭空编造：
   - ❌ 错误：看到5条限速记录就说"有5个安全的IP"
   - ✅ 正确：说"我找到了这些IP有异常活动"，然后列出具体的IP和原因
   - ❌ 错误：用户没有提供的数据，不要编造出来
   - ✅ 正确：如果数据不足，明确说"查询结果为空"或"最近7天没有该类型的记录"
   
5. 【严格】明确说明操作的前后状态变化：
   - 如果执行了add_to_blacklist，必须说："该IP从normal状态变为black状态"
   - 如果执行了release_rate_limit，必须说："该IP的限速已解除"
   - 不要模糊其词，要明确说明状态变化

6. 【执行工具反馈】如果调用了执行工具（add_to_blacklist、remove_from_blacklist、apply_rate_limit等），必须：
   - 明确告诉用户操作已完成或失败
   - 如果成功，表现出满足感和确定感 ✅😊
   - 如果失败，解释失败原因并建议解决方案 ⚠️
   - 例如："已成功将192.168.1.102加入黑名单！✅ 该IP现在会被直接丢弃。"
   - 【重要】所有执行工具的操作都会立即写入MySQL数据库，RYU控制器会自动同步这些规则并下发流表进行实际限速/拉黑操作
   - 所以不要说"等待RYU同步"，应该说"已立即生效"或"正在下发流表"
7. 【完整列表规则】如果用户问"黑名单里有什么IP"或"白名单里有什么IP"，必须：
   - 列出**所有**黑名单/白名单IP地址（不要只列几个）
   - 对每个IP标注：添加时间、原因（如果有）
   - 按照添加时间倒序排列（最新的在前）
   - 如果列表很长，先显示前20条，然后说"共XX条记录"
   - 不要只是笼统地说"有很多IP"，要具体列举每一个
   - 【关键】必须显示**完整的IP列表**，不能只显示部分

8. 【重点提炼】如果用户问"被限速的IP有哪些"或"限速列表"，必须：
   - 列出**所有**被限速的IP地址（不要只列几个）
   - 标注每个IP的限速原因（如"SYN Flood"、"ARP欺骗"、"前端手动限速"等）
   - 标注每个IP的限速速率（如"1024 kbps"）
   - 标注每个IP的过期时间（还要限速多久）
   - 按照最频繁或最严重的优先排序
   - 不要只是笼统地说"有很多被限速的IP"，要具体列举
   - 【关键】必须提及所有不同的限速原因，包括"前端手动限速"这样的特殊原因
   - 如果列表很长，先显示前20条，然后说"共XX条记录"

9. 【新增】如果数据中包含reason_summary字段（限速原因统计），必须：
   - 列出所有不同的限速原因及其出现次数
   - 例如："SYN Flood限速了XX次，ARP欺骗限速了XX次，前端手动限速了XX次"
   - 这样可以让管理员了解所有类型的限速情况

10. 如果用户问"攻击历史"或"最近的攻击"，必须列出**所有**主要的攻击类型和受影响的IP
    - 列出每个攻击的：源IP、攻击类型、数据包数、时间、状态
    - 如果数据中包含attack_type_summary字段，必须提及所有攻击类型的统计
    - 如果列表很长，先显示前20条，然后说"共XX条记录"

11. 如果用户问"设备异常"或"异常列表"，必须列出**所有**异常类型、严重程度和设备信息
    - 列出每个异常的：异常类型、设备类型、严重程度、检测时间、状态
    - 如果数据中包含anomaly_type_summary字段，必须提及所有异常类型的统计
    - 如果列表很长，先显示前20条，然后说"共XX条记录"

12. 【严格】不要只是笼统地说"有XX个记录"，必须具体列举每一条记录的关键信息
13. 只讨论用户问的内容，不要补充无关的信息
14. 如果数据为空或没有记录，要说明查询的时间范围（最近7天）
15. 用中文简洁回答，避免冗长
16. 在回答中大量使用表情符号来表达情感（如😊、😰、😡、🎉、💪、🔥等）
17. 【重要】保持像朋友一样的语气，有喜怒哀乐的情感：
    - 发现严重安全问题时：表现出担忧和紧张 😰😡⚠️
    - 发现问题已解决时：表现出欣慰和开心 😊✅🎉
    - 数据量很大时：表现出惊讶 😲😮
    - 需要用户注意时：表现出着急 😤💢
    - 一切正常时：表现出放心和满足 😌✨
18. 【重要】如果数据显示有攻击记录或限速记录，必须详细列出关键信息，并表现出相应的情感
19. 不要只是冷冰冰地陈述数据，要像真正的朋友一样用情感去表达
20. 可以用一些口语化的表达，比如"哎呀"、"天哪"、"太好了"、"不好意思"等
21. 根据情况调整语气的严肃程度：
    - 严重安全问题：严肃、着急、充满警告意味
    - 轻微问题：轻松、友好、给人安心感
    - 一切正常：开心、放松、给人满足感
22. 【智能总结】如果数据很多，要学会总结规律：
    - 哪个IP被限速最频繁？
    - 哪种攻击类型最常见？
    - 有没有规律性的模式？
    - 给出你的专业建议

请基于这些数据，用充满情感、像朋友一样的语气，抓住要点地回答用户的问题：
"""
        
        try:
            # 【修改】提高temperature值，让回答更有情感和创意
            final_response = agent._call_llm(final_prompt, temperature=0.7)
        except Exception as e:
            print(f"⚠️ LLM最终分析失败: {e}，使用默认回答")
            final_response = _generate_default_response(user_message, tool_results)
        
        # 【新增】如果用户上传了文件，在回答后自动保存到知识库
        if req.has_uploaded_file and req.uploaded_filename:
            print(f"[📄] 检测到用户上传的文件: {req.uploaded_filename}，准备保存到知识库")
            try:
                # 从知识库目录中查找该文件
                from pathlib import Path
                kb_dir = Path(__file__).parent.parent / "docs" / "knowledge_base"
                
                # 查找最新上传的文件（按修改时间排序）
                uploaded_files = sorted(kb_dir.glob(f"*{req.uploaded_filename.split('.')[0]}*"), 
                                       key=lambda x: x.stat().st_mtime, reverse=True)
                
                if uploaded_files:
                    latest_file = uploaded_files[0]
                    print(f"[✅] 找到上传的文件: {latest_file.name}")
                    
                    # 文件已经在知识库中，无需再次上传
                    # 这里只是确认文件已保存
                    print(f"[✅] 文件 {latest_file.name} 已保存到知识库")
                else:
                    print(f"[⚠️] 未找到上传的文件: {req.uploaded_filename}")
            except Exception as e:
                print(f"[⚠️] 保存文件到知识库失败: {e}")
        
        return {
            "status": "success",
            "response": final_response,
            "tools_called": tools_list,
            "tool_results": tool_results,
            "message": "ok"
        }
        
    except Exception as e:
        print(f"[ERROR] 聊天请求失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
            "response": "处理请求时出错，请稍后重试"
        }

@router.get("/chat/history")
async def get_chat_history(user_id: str = Query(..., description="用户ID"), limit: int = Query(50, description="获取的消息数量")):
    """获取用户的聊天历史记录"""
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            sql = """
                SELECT role, content, created_at
                FROM chat_memory
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            cur.execute(sql, (user_id, limit))
            rows = cur.fetchall()
        
        # 转换为前端需要的格式，按时间正序排列
        messages = []
        for row in reversed(rows):  # 倒序以便最早的消息在前
            role, content, created_at = row
            messages.append({
                "role": role,  # 'user' 或 'ai'
                "content": content,
                "timestamp": int(created_at.timestamp()) if hasattr(created_at, 'timestamp') else int(created_at)
            })
        
        print(f"[INFO] 成功获取 {len(messages)} 条聊天历史，user_id={user_id}")
        return {"success": True, "data": messages, "message": "ok"}
    except Exception as e:
        print(f"[ERROR] 获取聊天历史失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "data": [], "message": f"获取聊天历史失败: {str(e)}"}
    finally:
        if conn:
            conn.close()

# ---------- 2. 新增接口（保持代理，无缓存） ----------
@router.get("/ratelimit")
async def get_ratelimit():
    return proxy_get("ratelimit")

@router.get("/acl")
async def get_acl():
    return proxy_get("acl")

@router.get("/anomalies/week")
async def get_anomalies_week():
    return proxy_get("anomalies/week")

@router.get("/anomalies/top10")
async def get_anomalies_top10():
    return proxy_get("anomalies/top10")

@router.get("/flowstats/top10")
async def get_flowstats_top10():
    return proxy_get("flowstats/top10")

@router.get("/switch/info")
async def get_switch_info():
    return proxy_get("switch/info")

@router.get("/report/weekly")
async def get_report_weekly():
    return proxy_get("report/weekly")

@router.get("/export/pdf")
async def export_pdf():
    try:
        r = requests.get(f"{RYU_BASE}/export/pdf", timeout=15)
        r.raise_for_status()
        from fastapi import Response
        return Response(content=r.content,
                        media_type="application/pdf",
                        headers={"Content-Disposition": 'attachment; filename="weekly.pdf"'})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成 PDF 失败: {str(e)}")

@router.get("/export/weekly-pdf")
async def export_weekly_pdf():
    """生成详细的PDF周报"""
    try:
        print("[DEBUG] 收到周报PDF下载请求")
        r = requests.get(f"{RYU_BASE}/export/weekly-pdf", timeout=30)  # 增加超时时间
        r.raise_for_status()
        
        # 从响应头获取文件名
        content_disp = r.headers.get('Content-Disposition', 'attachment; filename="SDN_Weekly_Report.pdf"')
        
        print(f"[DEBUG] 周报PDF生成成功，大小: {len(r.content)} bytes")
        
        from fastapi import Response
        return Response(
            content=r.content,
            media_type="application/pdf",
            headers={"Content-Disposition": content_disp}
        )
    except Exception as e:
        print(f"[ERROR] 生成PDF周报失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成PDF周报失败: {str(e)}")

@router.get("/geoip/{ip}")
async def get_geoip(ip: str):
    return proxy_get(f"geoip/{ip}")

@router.post("/bulk/acl")
async def bulk_acl(csv_text: str = Form(...)):
    try:
        r = requests.post(f"{RYU_BASE}/bulk/acl",
                          json={"csv": csv_text},
                          timeout=10,
                          headers={"Content-Type": "application/json"})
        r.raise_for_status()
        return {"success": True, "data": r.json(), "message": "导入完成"}
    except Exception as e:
        return {"success": False, "data": {"success": 0, "failed": 0}, "message": str(e)}

@router.put("/settings")
async def put_settings(body: ThresholdBody):
    try:
        r = requests.put(f"{RYU_BASE}/settings",
                         json=body.dict(exclude_none=True),
                         timeout=TIMEOUT,
                         headers={"Content-Type": "application/json"})
        r.raise_for_status()
        return {"success": True, "data": r.json(), "message": "已保存"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存阈值失败: {str(e)}")

# ---------- ACL 黑名单管理接口 ----------

@router.post("/acl/black")
async def add_blacklist(ip: str = Form(...), ttl: int = Form(-1)):
    """添加IP到黑名单"""
    try:
        data = {"ip": ip, "ttl": ttl}
        print(f"[DEBUG] 添加黑名单请求: {data}")
        r = requests.post(f"{RYU_BASE}/acl/black", json=data, timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] RYU控制器响应: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] 添加黑名单失败: {e}")
        return {"success": False, "message": f"添加黑名单失败: {str(e)}"}

@router.delete("/acl/black/{ip}")
async def remove_blacklist(ip: str):
    """从黑名单移除IP"""
    try:
        print(f"[DEBUG] 移除黑名单请求: {ip}")
        r = requests.delete(f"{RYU_BASE}/acl/black/{ip}", timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] RYU控制器响应: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] 移除黑名单失败: {e}")
        return {"success": False, "message": f"移除黑名单失败: {str(e)}"}

# ---------- ACL 白名单管理接口 ----------

@router.post("/acl/white")
async def add_whitelist(ip: str = Form(...), ttl: int = Form(-1)):
    """添加IP到白名单"""
    try:
        data = {"ip": ip, "ttl": ttl}
        print(f"[DEBUG] 添加白名单请求: {data}")
        r = requests.post(f"{RYU_BASE}/acl/white", json=data, timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] RYU控制器响应: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] 添加白名单失败: {e}")
        return {"success": False, "message": f"添加白名单失败: {str(e)}"}

@router.delete("/acl/white/{ip}")
async def remove_whitelist(ip: str):
    """从白名单移除IP"""
    try:
        print(f"[DEBUG] 移除白名单请求: {ip}")
        r = requests.delete(f"{RYU_BASE}/acl/white/{ip}", timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] RYU控制器响应: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] 移除白名单失败: {e}")
        return {"success": False, "message": f"移除白名单失败: {str(e)}"}

# ---------- 限速管理接口 ----------

@router.get("/dashboard/cards")
async def get_dashboard_cards():
    """获取仪表盘卡片数据"""
    return proxy_get("dashboard/cards")

@router.get("/rate-trend")
async def get_rate_trend(type: int = Query(1, description="时间类型: 1=24小时, 3=3天, 7=7天")):
    """获取限速趋势数据"""
    try:
        # 支持整数参数，直接传递给RYU控制器
        # type: 1=24小时, 3=3天, 7=7天
        if type not in [1, 3, 7]:
            print(f"[WARNING] 无效的type参数: {type}，使用默认值1")
            type = 1
        
        params = {"type": type}
        print(f"[DEBUG] 获取限速趋势数据请求: type={type} ({'24小时' if type == 1 else f'{type}天'})")
        r = requests.get(f"{RYU_BASE}/rate-trend", params=params, timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] RYU控制器限速趋势响应成功，数据量: {len(result) if isinstance(result, list) else 'N/A'}")
        if isinstance(result, list) and len(result) > 0:
            print(f"[DEBUG] 趋势数据预览: {result[:3]}")  # 打印前3条数据
        return {"success": True, "data": result, "message": "ok"}
    except Exception as e:
        print(f"[ERROR] 获取限速趋势数据失败: {e}")
        return {"success": False, "data": [], "message": f"获取限速趋势数据失败: {str(e)}"}

@router.get("/rate-reason-stats")
async def get_rate_reason_stats(hours: int = Query(24, description="统计最近N小时的数据")):
    """获取限速原因分布统计"""
    try:
        params = {"hours": hours}
        print(f"[DEBUG] 获取限速原因统计请求: hours={hours}")
        r = requests.get(f"{RYU_BASE}/rate-reason-stats", params=params, timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] RYU控制器限速原因统计响应成功，数据量: {len(result) if isinstance(result, list) else 'N/A'}")
        if isinstance(result, list):
            print(f"[DEBUG] 限速原因统计结果:")
            for item in result:
                print(f"  - {item.get('reason', 'N/A')}: {item.get('count', 0)} 次")
        return {"success": True, "data": result, "message": "ok"}
    except Exception as e:
        print(f"[ERROR] 获取限速原因统计失败: {e}")
        return {"success": False, "data": [], "message": f"获取限速原因统计失败: {str(e)}"}


@router.post("/limit/ip")
async def add_rate_limit(
    ip: str = Form(...), 
    kbps: int = Form(1024), 
    reason: str = Form("前端手动限速"),
    duration_minutes: int = Form(5)  # ✅ 添加时长参数，默认5分钟
):
    """添加IP限速规则"""
    try:
        # ✅ 直接传递duration_minutes参数给RYU控制器（RYU期望的是duration_minutes而不是ttl）
        data = {"ip": ip, "kbps": kbps, "reason": reason, "duration_minutes": duration_minutes}
        print(f"[DEBUG] 添加限速请求: {data} (时长: {duration_minutes}分钟)")
        r = requests.post(f"{RYU_BASE}/limit/ip", json=data, timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] RYU控制器响应: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] 添加限速失败: {e}")
        return {"success": False, "message": f"添加限速失败: {str(e)}"}

@router.delete("/limit/ip/{ip}")
async def remove_rate_limit(ip: str):
    """移除IP限速规则"""
    try:
        print(f"[DEBUG] 移除限速请求: {ip}")
        r = requests.delete(f"{RYU_BASE}/limit/ip/{ip}", timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] RYU控制器响应: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] 移除限速失败: {e}")
        return {"success": False, "message": f"移除限速失败: {str(e)}"}

# ✅ 修改限速速率
@router.put("/rate/speed/{ip}")
async def change_rate_speed(ip: str, req: dict):
    """修改IP限速速率"""
    try:
        print(f"[DEBUG] 修改限速速率请求: {ip}, 新速率: {req.get('kbps')}")
        r = requests.put(f"{RYU_BASE}/rate/speed/{ip}", json=req, timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] RYU控制器响应: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] 修改限速速率失败: {e}")
        return {"success": False, "message": f"修改限速速率失败: {str(e)}"}

# ✅ 修改限速时间
@router.put("/rate/duration/{ip}")
async def change_rate_duration(ip: str, req: dict):
    """修改IP限速时间（延长或缩短）"""
    try:
        print(f"[DEBUG] 修改限速时间请求: {ip}, 调整秒数: {req.get('extra_seconds')}")
        r = requests.put(f"{RYU_BASE}/rate/duration/{ip}", json=req, timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] RYU控制器响应: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] 修改限速时间失败: {e}")
        return {"success": False, "message": f"修改限速时间失败: {str(e)}"}

# ---------- 历史限速记录接口 ----------

@router.get("/rate/history/{day}")
async def get_rate_history_by_day(day: str):
    """获取指定日期的历史限速记录"""
    try:
        # 验证日期格式
        import re
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', day):
            raise HTTPException(status_code=400, detail="日期格式应为 yyyy-mm-dd")
        
        print(f"[DEBUG] 获取历史限速记录请求: day={day}")
        r = requests.get(f"{RYU_BASE}/rate/history/{day}", timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] RYU控制器历史限速记录响应成功，数据量: {len(result.get('data', [])) if isinstance(result, dict) else 'N/A'}")
        return result
    except Exception as e:
        print(f"[ERROR] 获取历史限速记录失败: {e}")
@router.get("/switches")
async def get_switches():
    """获取所有交换机列表"""
    result = proxy_get("switches")
    if result.get("success"):
        # RYU返回的是数组 [1, 2, ...], 前端期望 {success: true, switches: [...]}
        switches_data = result.get("data", [])
        return {
            "success": True,
            "switches": switches_data,
            "message": "ok"
        }
    return result


@router.get("/switches/{dpid}/flows")
async def get_switch_flows(dpid: str):
    """获取指定交换机的流表"""
    result = proxy_get(f"switches/{dpid}/flows")
    print(f"[DEBUG] ===== 流表查询 =====")
    print(f"[DEBUG] DPID: {dpid}, 类型: {type(dpid)}")
    print(f"[DEBUG] proxy_get返回类型: {type(result)}")
    print(f"[DEBUG] proxy_get完整内容: {result}")
    
    if result.get("success"):
        flows_data = result.get("data", [])
        print(f"[DEBUG] flows_data类型: {type(flows_data)}")
        print(f"[DEBUG] flows_data内容预览: {str(flows_data)[:500]}...") 
        
        # ✅ 如果flows_data是字典，尝试提取dpid对应的数组
        if isinstance(flows_data, dict):
            print(f"[DEBUG] flows_data是字典，键: {list(flows_data.keys())}")
            # 尝试多种可能的键格式
            flows_data = flows_data.get(int(dpid) if dpid.isdigit() else dpid, 
                                       flows_data.get(dpid, 
                                       flows_data.get(str(dpid), [])))
            print(f"[DEBUG] 从字典中提取流表后类型: {type(flows_data)}, 数量: {len(flows_data) if isinstance(flows_data, list) else 'N/A'}")
        
        final_flows = flows_data if isinstance(flows_data, list) else []
        print(f"[DEBUG] 最终返回流表数量: {len(final_flows)}")
        if len(final_flows) > 0:
            print(f"[DEBUG] 第一条流表预览: {final_flows[0]}")
        print(f"[DEBUG] ==================")
        
        return {
            "success": True,
            "dpid": dpid,
            "flows": final_flows,
            "flow_count": len(final_flows),
            "message": "ok"
        }
    return result


@router.post("/switches/{dpid}/flows")
async def add_switch_flow(dpid: str, flow_entry: dict):
    """添加流表项（不需要权限验证，直接转发给RYU）"""
    try:
        print(f"[DEBUG] 添加流表请求: dpid={dpid}, flow_entry={flow_entry}")
        r = requests.post(
            f"{RYU_BASE}/switches/{dpid}/flows",
            json=flow_entry,
            timeout=TIMEOUT
        )
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] 流表添加成功")
        return {"success": True, "data": result, "message": "流表添加成功"}
    except Exception as e:
        print(f"[ERROR] 添加流表失败: {e}")
        raise HTTPException(status_code=500, detail=f"添加流表失败: {str(e)}")


@router.delete("/switches/{dpid}/flows")
async def delete_switch_flow(dpid: str, flow_entry: dict):
    """删除流表项"""
    try:
        print(f"[DEBUG] 删除流表请求: dpid={dpid}")
        r = requests.delete(
            f"{RYU_BASE}/switches/{dpid}/flows",
            json=flow_entry,
            timeout=TIMEOUT
        )
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] 流表删除成功")
        return {"success": True, "data": result, "message": "流表删除成功"}
    except Exception as e:
        print(f"[ERROR] 删除流表失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除流表失败: {str(e)}")


@router.delete("/switches/{dpid}/flows/all")
async def delete_all_switch_flows(dpid: str):
    """删除指定交换机的所有流表"""
    try:
        print(f"[DEBUG] 删除所有流表请求: dpid={dpid}")
        r = requests.delete(
            f"{RYU_BASE}/switches/{dpid}/flows/all",
            timeout=TIMEOUT
        )
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] 所有流表删除成功")
        return {"success": True, "data": result, "message": "所有流表删除成功"}
    except Exception as e:
        print(f"[ERROR] 删除所有流表失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除所有流表失败: {str(e)}")


# ---------- Mininet主机管理 ----------
@router.get("/mininet/hosts")
async def get_mininet_hosts():
    """获取Mininet主机列表（从RYU动态获取）"""
    try:
        # 从RYU获取拓扑信息（包括主机和交换机）
        print(f"[DEBUG] 从RYU获取主机拓扑信息")
        r = requests.get(f"{RYU_BASE}/topology/hosts", timeout=TIMEOUT)
        r.raise_for_status()
        hosts_data = r.json()
        
        print(f"[DEBUG] RYU返回主机数据: {len(hosts_data) if isinstance(hosts_data, list) else 'N/A'} 个主机")
        
        # 如果RYU返回了主机列表，直接返回
        if isinstance(hosts_data, list) and len(hosts_data) > 0:
            return {"success": True, "data": hosts_data, "message": "ok"}
        
        # 如果RYU没有返回主机列表，尝试从拓扑信息中提取
        print(f"[DEBUG] RYU未返回主机列表，尝试从拓扑信息中提取")
        r = requests.get(f"{RYU_BASE}/topology", timeout=TIMEOUT)
        r.raise_for_status()
        topology_data = r.json()
        
        # 从拓扑数据中提取主机信息
        hosts = []
        if isinstance(topology_data, dict):
            # 尝试从不同的字段中提取主机信息
            hosts_list = topology_data.get('hosts', [])
            if hosts_list:
                hosts = hosts_list
        
        if hosts:
            print(f"[DEBUG] 从拓扑信息中提取到 {len(hosts)} 个主机")
            return {"success": True, "data": hosts, "message": "ok"}
        
        # 如果RYU都没有返回主机信息，返回空列表和错误信息
        print(f"[WARNING] 无法从RYU获取主机信息")
        return {
            "success": False, 
            "data": [], 
            "message": "RYU控制器未返回主机信息，请确保Mininet网络正在运行"
        }
        
    except Exception as e:
        print(f"[ERROR] 获取主机列表失败: {e}")
        return {
            "success": False,
            "data": [],
            "message": f"获取主机列表失败: {str(e)}"
        }


# ---------- 设备异常查询 ----------
@router.get("/device_anomalies")
async def get_device_anomalies(
    hours: Optional[int] = Query(None, description="查询时间范围（小时，空=全部）"),
    status: Optional[str] = Query(None, description="状态过滤：pending|handled")
):
    """查询设备异常记录（支持时间范围与状态过滤）"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            base_sql = (
                """
                SELECT id, anomaly_type, device_type, device_id, description,
                       severity, detected_at, resolved_at, status,
                       handled_by, handled_at, handle_action
                FROM device_anomalies
                """
            )
            where_clauses = []
            params = []

            # 时间范围过滤（None = 不限，24 = 今日，其他 = 最近N小时）
            if hours is not None:
                if hours == 24:
                    where_clauses.append("DATE(detected_at) = CURDATE()")
                else:
                    where_clauses.append("detected_at >= DATE_SUB(NOW(), INTERVAL %s HOUR)")
                    params.append(hours)

            # 状态过滤
            if status in ("pending", "handled"):
                where_clauses.append("status = %s")
                params.append(status)

            if where_clauses:
                base_sql += " WHERE " + " AND ".join(where_clauses)

            base_sql += " ORDER BY detected_at DESC"

            cur.execute(base_sql, tuple(params))
            rows = cur.fetchall()

            # 转换时间格式
            for row in rows:
                if row.get('detected_at'):
                    row['detected_at'] = row['detected_at'].strftime('%Y-%m-%d %H:%M:%S')
                if row.get('resolved_at'):
                    row['resolved_at'] = row['resolved_at'].strftime('%Y-%m-%d %H:%M:%S')
                if row.get('handled_at'):
                    row['handled_at'] = row['handled_at'].strftime('%Y-%m-%d %H:%M:%S')

            conn.close()
            return {"success": True, "data": rows, "message": "ok"}
    except Exception as e:
        print(f"[ERROR] 查询设备异常失败: {e}")
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=f"查询设备异常失败: {str(e)}")


# ✅ 新增：标记设备异常为已处理（更新本地数据库）
@router.put("/device_anomalies/{anomaly_id}/handle")
async def handle_device_anomaly(anomaly_id: int, req: dict):
    """将设备异常状态更新为 handled，并记录处理人与时间"""
    handled_by = req.get('handled_by', 'admin')
    handle_action = req.get('handle_action', 'frontend_resolve')
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            sql = (
                "UPDATE device_anomalies "
                "SET status=%s, handled_by=%s, handled_at=NOW(), handle_action=%s "
                "WHERE id=%s AND status <> 'handled'"
            )
            cur.execute(sql, ('handled', handled_by, handle_action, anomaly_id))
            affected = cur.rowcount
            conn.commit()
        
        # 查询更新后的记录（可选）
        with conn.cursor(pymysql.cursors.DictCursor) as cur2:
            cur2.execute(
                "SELECT id, status, handled_by, handled_at, handle_action FROM device_anomalies WHERE id=%s",
                (anomaly_id,)
            )
            row = cur2.fetchone()
        conn.close()
        
        if affected == 0:
            # 未更新可能是记录不存在或已是handled
            return {"success": True, "affected_rows": 0, "message": "记录不存在或已处理", "data": row}
        return {"success": True, "affected_rows": affected, "message": "已标记为已处理", "data": row}
    except Exception as e:
        print(f"[ERROR] 标记设备异常为已处理失败: {e}")
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=f"标记设备异常为已处理失败: {str(e)}")


# ========== MCP工具代理接口 ==========

class MCPToolRequest(BaseModel):
    """MCP工具请求"""
    tool_name: str  # 工具名称
    ip: Optional[str] = None  # IP地址（可选）
    attack_type: Optional[str] = None  # 攻击类型（可选）
    level: Optional[str] = None  # 限速档位（可选）
    duration_seconds: Optional[int] = 300  # 限速时长（可选）
    reason: Optional[str] = None  # 原因（可选）


@router.post("/agent/tools/call")
async def call_mcp_tool(request: MCPToolRequest):
    """
    调用MCP工具（代理到后端Agent系统）
    
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
    try:
        # 导入Agent系统
        from security_agent import get_agent_instance
        
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
                request.ip, request.level, request.duration_seconds, request.reason
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"工具调用失败: {str(e)}")


@router.get("/agent/tools/list")
async def list_mcp_tools():
    """
    获取所有可用的MCP工具列表
    """
    try:
        from security_agent import get_agent_instance
        
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


# ---------- 知识库文档管理 ----------
@router.get("/knowledge/check")
async def check_knowledge_document(filename: str = Query(..., description="要检查的文件名")):
    """
    检查知识库中是否已存在该文件（按前缀匹配）
    """
    try:
        from pathlib import Path
        
        kb_dir = Path(__file__).parent.parent / "docs" / "knowledge_base"
        
        # 获取文件名前缀（不包括扩展名）
        file_stem = Path(filename).stem  # 例如: "第5章 SDN南向接口协议"
        file_ext = Path(filename).suffix  # 例如: ".pdf"
        
        # 在知识库中查找以相同前缀开头的文件
        exists = False
        found_file = None
        
        for file_in_kb in kb_dir.glob(f"{file_stem}*{file_ext}"):
            if file_in_kb.is_file():
                exists = True
                found_file = file_in_kb.name
                break
        
        print(f"[🔍] 检查文件: {filename} - {'存在' if exists else '不存在'}" + (f" (找到: {found_file})" if found_file else ""))
        
        return {
            "exists": exists,
            "filename": filename,
            "found_file": found_file,
            "message": f"文件{'已在知识库中' if exists else '不在知识库中'}"
        }
    except Exception as e:
        print(f"[❌] 检查文件失败: {e}")
        return {
            "exists": False,
            "filename": filename,
            "message": f"检查失败: {str(e)}"
        }

@router.post("/knowledge/upload")
async def upload_knowledge_document(file: UploadFile = File(...)):
    """
    上传文档到知识库
    支持TXT、PDF、CSV等格式
    """
    import tempfile
    
    try:
        print(f"[📄] 接收到文件上传: {file.filename}")
        
        # 验证文件类型
        allowed_extensions = {'.txt', '.pdf', '.csv', '.docx'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件格式: {file_ext}，支持的格式: {', '.join(allowed_extensions)}"
            )
        
        # 验证文件大小（10MB限制）
        file_size = len(await file.read())
        await file.seek(0)
        
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超过10MB")
        
        # 保存临时文件到项目目录（不用C盘tempfile）
        project_root = Path(__file__).parent.parent
        temp_dir = project_root / "temp_uploads"
        temp_dir.mkdir(exist_ok=True)
        
        # 生成唯一的临时文件名
        tmp_filename = f"{uuid.uuid4()}{file_ext}"
        tmp_path = temp_dir / tmp_filename
        
        # 保存文件内容
        content = await file.read()
        with open(tmp_path, 'wb') as f:
            f.write(content)
        
        print(f"[💾] 临时文件已保存: {tmp_path}")
        
        try:
            # 使用知识库集成器添加文档
            from knowledge_integration import get_knowledge_integrator
            
            integrator = get_knowledge_integrator()
            result = integrator.add_document_sync(str(tmp_path), file.filename)
            
            if result['success']:
                return {
                    "success": True,
                    "message": result['message'],
                    "filename": result['filename'],
                    "chunks_count": result['chunks_count'],
                    "text_length": result['text_length']
                }
            else:
                raise HTTPException(status_code=500, detail=result['message'])
        
        finally:
            # 清理临时文件
            import os
            if os.path.exists(str(tmp_path)):
                try:
                    os.remove(str(tmp_path))
                    print(f"[🧹] 已清理临时文件: {tmp_path}")
                except Exception as e:
                    print(f"[⚠️] 清理临时文件失败: {e}")
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[❌] 文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.get("/knowledge/documents")
async def list_knowledge_documents():
    """
    列出知识库中的所有文档
    """
    try:
        from knowledge_integration import get_knowledge_integrator
        
        integrator = get_knowledge_integrator()
        documents = integrator.list_documents()
        
        return {
            "success": True,
            "documents": documents,
            "total": len(documents)
        }
    
    except Exception as e:
        print(f"[❌] 获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@router.delete("/knowledge/documents/{filename}")
async def delete_knowledge_document(filename: str):
    """
    删除知识库中的文档
    """
    try:
        from knowledge_integration import get_knowledge_integrator
        
        integrator = get_knowledge_integrator()
        result = integrator.delete_document(filename)
        
        if result['success']:
            return {
                "success": True,
                "message": result['message']
            }
        else:
            raise HTTPException(status_code=500, detail=result['message'])
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[❌] 删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")
