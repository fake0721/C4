"""
API配置管理 - 处理API调用频率限制和重试策略
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class APIRateLimitConfig:
    """API速率限制配置"""
    max_requests_per_minute: int = 30  # 每分钟最大请求数
    max_tokens_per_minute: int = 100000  # 每分钟最大token数
    retry_delay_seconds: int = 5  # 重试延迟秒数
    max_retries: int = 3  # 最大重试次数


class APIRateLimiter:
    """API速率限制器"""
    
    def __init__(self, config: APIRateLimitConfig):
        self.config = config
        self.request_timestamps = []
        self.token_usage = []
        self.last_reset_time = time.time()
    
    def can_make_request(self, estimated_tokens: int = 0) -> bool:
        """检查是否可以发起请求"""
        current_time = time.time()
        
        # 清理过期的请求记录（1分钟内）
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if current_time - ts < 60
        ]
        
        # 清理过期的token使用记录（1分钟内）
        self.token_usage = [
            usage for usage in self.token_usage 
            if current_time - usage['timestamp'] < 60
        ]
        
        # 检查请求次数限制
        if len(self.request_timestamps) >= self.config.max_requests_per_minute:
            return False
        
        # 检查token使用限制
        total_tokens = sum(usage['tokens'] for usage in self.token_usage)
        if total_tokens + estimated_tokens > self.config.max_tokens_per_minute:
            return False
        
        return True
    
    def record_request(self, tokens_used: int = 0):
        """记录请求使用情况"""
        current_time = time.time()
        self.request_timestamps.append(current_time)
        
        if tokens_used > 0:
            self.token_usage.append({
                'timestamp': current_time,
                'tokens': tokens_used
            })
    
    def get_wait_time(self) -> float:
        """获取需要等待的时间（秒）"""
        if not self.request_timestamps:
            return 0
        
        current_time = time.time()
        oldest_request = min(self.request_timestamps)
        
        # 计算距离最早请求满1分钟还需要等待的时间
        wait_time = max(0, 60 - (current_time - oldest_request))
        return wait_time
    
    def get_retry_delay(self, retry_count: int) -> float:
        """获取重试延迟时间（指数退避）"""
        return self.config.retry_delay_seconds * (2 ** retry_count)


# 全局API配置实例
kimi_rate_limit_config = APIRateLimitConfig(
    max_requests_per_minute=30,
    max_tokens_per_minute=100000,
    retry_delay_seconds=5,
    max_retries=3
)

kimi_rate_limiter = APIRateLimiter(kimi_rate_limit_config)