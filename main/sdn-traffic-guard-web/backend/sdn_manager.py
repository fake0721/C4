#!/usr/bin/env python

"""SDN网络管理模块，用于与SDN控制器交互"""

import requests
import json
import time
from typing import Dict, List, Optional, Any


class SDNManager:
    """SDN控制器管理类，提供与RYU控制器交互的各种方法"""
    
    def __init__(self, controller_ip: str = '192.168.126.128', controller_port: int = 8080, timeout: int = 5):
        """初始化SDN管理器
        
        Args:
            controller_ip: RYU控制器的IP地址
            controller_port: RYU控制器的REST API端口
            timeout: HTTP请求超时时间（秒）
        """
        self.controller_ip = controller_ip
        self.controller_port = controller_port
        self.base_url = f'http://{controller_ip}:{controller_port}'
        self.timeout = timeout
        self.headers = {'Content-Type': 'application/json'}
    
    def is_controller_alive(self) -> bool:
        """检查控制器是否在线
        
        Returns:
            bool: 控制器是否在线
        """
        try:
            # 尝试访问/v1/summary接口（更可靠）
            response = requests.get(f'{self.base_url}/v1/summary', timeout=self.timeout)
            return response.status_code == 200
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return False
        except Exception:
            return False
    
    def get_network_topology(self) -> Optional[Dict[str, Any]]:
        """获取网络拓扑信息
        
        Returns:
            Dict: 拓扑信息字典，如果失败则返回None
        """
        try:
            response = requests.get(f'{self.base_url}/stats/topology', headers=self.headers, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"获取拓扑信息失败: {e}")
            return None
    
    def get_switch_flows(self, dpid: str) -> Optional[Dict[str, Any]]:
        """获取指定交换机的流表信息
        
        Args:
            dpid: 交换机的DPID
        
        Returns:
            Dict: 流表信息字典，如果失败则返回None
        """
        try:
            response = requests.get(f'{self.base_url}/v1/switches/{dpid}/flows', headers=self.headers, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"获取流表信息失败: {e}")
            return None
    
    def get_all_flows(self) -> Optional[Dict[str, Any]]:
        """获取所有交换机的流表信息
        
        Returns:
            Dict: 所有交换机的流表信息，如果失败则返回None
        """
        try:
            response = requests.get(f'{self.base_url}/stats/flow/', headers=self.headers, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"获取所有流表信息失败: {e}")
            return None
    
    def add_flow_entry(self, dpid: str, flow_entry: Dict[str, Any]) -> bool:
        """向交换机添加流表项
        
        Args:
            dpid: 交换机的DPID
            flow_entry: 流表项配置字典
        
        Returns:
            bool: 添加是否成功
        """
        try:
            response = requests.post(
                f'{self.base_url}/v1/switches/{dpid}/flows',
                json=flow_entry,
                headers=self.headers,
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception as e:
            print(f"添加流表项失败: {e}")
            return False
    
    def delete_flow_entry(self, dpid: str, flow_entry: Dict[str, Any]) -> bool:
        """删除交换机的流表项
        
        Args:
            dpid: 交换机的DPID
            flow_entry: 要删除的流表项配置字典
        
        Returns:
            bool: 删除是否成功
        """
        try:
            response = requests.delete(
                f'{self.base_url}/v1/switches/{dpid}/flows',
                json=flow_entry,
                headers=self.headers,
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception as e:
            print(f"删除流表项失败: {e}")
            return False
    
    def delete_all_flows(self, dpid: str) -> bool:
        """删除交换机的所有流表项
        
        Args:
            dpid: 交换机的DPID
        
        Returns:
            bool: 删除是否成功
        """
        try:
            response = requests.delete(
                f'{self.base_url}/v1/switches/{dpid}/flows/all',
                headers=self.headers,
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception as e:
            print(f"删除所有流表项失败: {e}")
            return False
    
    def get_switch_stats(self) -> Optional[List[int]]:
        """获取所有交换机的DPID列表
        
        Returns:
            List[int]: 交换机DPID列表，如果失败则返回None
        """
        try:
            response = requests.get(f'{self.base_url}/v1/switches', headers=self.headers, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"获取交换机列表失败: {e}")
            return None
    
    def get_port_stats(self, dpid: str) -> Optional[Dict[str, Any]]:
        """获取交换机的端口统计信息
        
        Args:
            dpid: 交换机的DPID
        
        Returns:
            Dict: 端口统计信息，如果失败则返回None
        """
        try:
            response = requests.get(f'{self.base_url}/stats/port/{dpid}', headers=self.headers, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"获取端口统计信息失败: {e}")
            return None
    
    def get_port_desc(self, dpid: str) -> Optional[Dict[str, Any]]:
        """获取交换机的端口描述信息
        
        Args:
            dpid: 交换机的DPID
        
        Returns:
            Dict: 端口描述信息，如果失败则返回None
        """
        try:
            response = requests.get(f'{self.base_url}/stats/portdesc/{dpid}', headers=self.headers, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"获取端口描述信息失败: {e}")
            return None
    
    def get_queue_stats(self, dpid: str, port_no: int) -> Optional[Dict[str, Any]]:
        """获取交换机端口的队列统计信息
        
        Args:
            dpid: 交换机的DPID
            port_no: 端口号
        
        Returns:
            Dict: 队列统计信息，如果失败则返回None
        """
        try:
            response = requests.get(f'{self.base_url}/stats/queue/{dpid}/{port_no}', headers=self.headers, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"获取队列统计信息失败: {e}")
            return None
    
    def create_simple_flow(self, dpid: str, in_port: int, eth_dst: str, out_port: int) -> bool:
        """创建一个简单的转发流表项
        
        Args:
            dpid: 交换机的DPID
            in_port: 入端口
            eth_dst: 目标MAC地址
            out_port: 出端口
        
        Returns:
            bool: 创建是否成功
        """
        flow_entry = {
            "priority": 1,
            "match": {
                "in_port": in_port,
                "eth_dst": eth_dst
            },
            "actions": [
                {
                    "type": "OUTPUT",
                    "port": out_port
                }
            ]
        }
        return self.add_flow_entry(dpid, flow_entry)
    
    def monitor_network(self, interval: int = 5, duration: int = 30) -> List[Dict[str, Any]]:
        """监控网络状态
        
        Args:
            interval: 监控间隔（秒）
            duration: 监控持续时间（秒）
        
        Returns:
            List[Dict]: 监控数据列表
        """
        monitor_data = []
        end_time = time.time() + duration
        
        while time.time() < end_time:
            try:
                # 获取交换机列表
                switches = self.get_switch_stats()
                if switches:
                    snapshot = {
                        "timestamp": time.time(),
                        "switches": {},
                        "topology": self.get_network_topology()
                    }
                    
                    # 获取每个交换机的端口统计
                    for dpid in switches:
                        dpid_str = str(dpid)
                        snapshot["switches"][dpid_str] = {
                            "port_stats": self.get_port_stats(dpid_str),
                            "flows": len(self.get_switch_flows(dpid_str).get(dpid_str, [])) if switches else 0
                        }
                    
                    monitor_data.append(snapshot)
                
                # 等待下一次监控
                time.sleep(interval)
            except Exception as e:
                print(f"监控网络时发生错误: {e}")
                break
        
        return monitor_data
    
    def get_network_summary(self) -> Dict[str, Any]:
        """获取网络总体摘要信息
        
        Returns:
            Dict: 网络摘要信息
        """
        summary = {
            "controller_status": "online" if self.is_controller_alive() else "offline",
            "timestamp": time.time(),
            "switch_count": 0,
            "total_flows": 0,
            "port_count": 0,
            "links": 0
        }
        
        if summary["controller_status"] == "online":
            # 获取交换机数量
            switches = self.get_switch_stats()
            if switches:
                summary["switch_count"] = len(switches)
                
                # 统计总流表数和端口数
                for dpid in switches:
                    dpid_str = str(dpid)
                    
                    # 统计流表数
                    flows = self.get_switch_flows(dpid_str)
                    if flows and dpid_str in flows:
                        summary["total_flows"] += len(flows[dpid_str])
                    
                    # 统计端口数
                    port_desc = self.get_port_desc(dpid_str)
                    if port_desc and dpid_str in port_desc:
                        summary["port_count"] += len(port_desc[dpid_str])
            
            # 统计链路数
            topology = self.get_network_topology()
            if topology:
                summary["links"] = len(topology.get("links", []))
        
        return summary

    def get_limit_list(self) -> List[Dict[str, Any]]:
        """获取限速主机列表
        
        Returns:
            List[Dict[str, Any]]: 限速主机列表
        """
        try:
            # 尝试从RYU控制器获取限速列表
            response = requests.get(f"{self.base_url}/ratelimit", timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                if "limit_list" in data:
                    return data["limit_list"]
            return []
        except Exception as e:
            print(f"获取限速主机列表失败: {str(e)}")
            return []

    def get_rate_limited_hosts(self) -> List[Dict[str, Any]]:
        """获取限速主机列表（兼容性方法）
        
        Returns:
            List[Dict[str, Any]]: 限速主机列表
        """
        return self.get_limit_list()


# 示例使用
if __name__ == "__main__":
    # 初始化SDN管理器
    sdn_manager = SDNManager()
    
    # 检查控制器状态
    if sdn_manager.is_controller_alive():
        print("控制器在线")
        
        # 获取网络摘要
        summary = sdn_manager.get_network_summary()
        print(f"网络摘要: {json.dumps(summary, indent=2)}")
        
        # 获取网络拓扑
        topology = sdn_manager.get_network_topology()
        if topology:
            print(f"网络拓扑: {json.dumps(topology, indent=2)}")
    else:
        print("控制器离线，请先启动RYU控制器")