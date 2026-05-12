# SDN网络拓扑搭建指南

## 概述
本指南将帮助你在虚拟机中搭建SDN（软件定义网络）环境，配置Mininet拓扑，并与RYU控制器集成。通过本指南，你将能够创建和管理自定义SDN网络拓扑，并将其与网络管理平台连接。

## 环境准备

### 已安装的组件
- **Mininet**: 网络仿真工具
- **RYU**: SDN控制器
- **Open vSwitch**: 开源虚拟交换机

### 安装验证
在开始之前，请确认这些组件已正确安装：

```bash
# 验证Mininet安装
sudo mn --test pingall

# 验证RYU控制器安装
ryu --version

# 验证Open vSwitch安装
sudo ovs-vsctl show
```

## SDN拓扑配置工具使用

我们已经提供了一个完整的SDN拓扑配置工具`sdn_topology.py`，该工具位于`backend`目录下。

### 功能概述
- 创建默认环形拓扑（4台交换机和4台主机）
- 创建自定义树形拓扑
- 生成RYU应用示例
- 提供详细的配置说明

### 运行拓扑工具

```bash
# 切换到backend目录
cd e:\毕设\network-management-platform\backend

# 运行拓扑工具
python sdn_topology.py
```

运行后，你将看到以下选项：
```
======================================
       SDN网络拓扑配置工具
======================================
选项:
1. 创建默认拓扑 (4交换机4主机的环形拓扑)
2. 创建树形拓扑
3. 生成RYU应用示例
4. 生成拓扑配置说明
```

## 详细配置步骤

### 1. 启动RYU控制器

首先，需要启动RYU控制器并加载交换机应用：

```bash
# 在第一个终端窗口运行
cd e:\毕设\network-management-platform\backend

# 生成RYU应用示例（如果还没有）
python -c "from sdn_topology import create_ryu_app; create_ryu_app()"

# 启动RYU控制器，加载简单交换机应用
ryu-manager simple_switch_13.py
```

控制器启动后，你将看到类似的输出：
```
loading app simple_switch_13.py
loading app ryu.controller.ofp_handler
instantiating app simple_switch_13.py of SimpleSwitch13
instantiating app ryu.controller.ofp_handler of OFPHandler
```

### 2. 创建SDN网络拓扑

在第二个终端窗口，运行拓扑工具创建网络：

```bash
# 在第二个终端窗口运行
cd e:\毕设\network-management-platform\backend

# 创建默认环形拓扑
python sdn_topology.py
# 然后选择选项 1
```

或者创建自定义树形拓扑：

```bash
# 创建树形拓扑
python sdn_topology.py
# 然后选择选项 2，并输入深度和扇出数
```

成功创建后，你将进入Mininet CLI界面，可以执行各种网络测试命令。

### 3. Mininet CLI常用命令

在Mininet CLI中，你可以使用以下命令测试和管理网络：

```bash
# 查看所有节点
mininet> nodes

# 查看网络拓扑
mininet> net

# 查看所有链路
mininet> links

# 所有主机互相ping测试
mininet> pingall

# 特定主机之间的ping测试
mininet> h1 ping h2

# 查看交换机流表
mininet> dpctl dump-flows

# 退出CLI
mininet> exit
```

## 与网络管理平台集成

要将SDN环境与现有的网络管理平台集成，可以按照以下步骤操作：

### 1. 修改SDN拓扑配置

编辑`sdn_topology.py`文件，修改控制器配置以连接到网络管理平台：

```python
# 修改控制器IP和端口
c0 = net.addController('c0', ip='<网络管理平台IP>', port=6633)
```

### 2. 添加网络设备到数据库

将SDN环境中的设备添加到网络管理平台的数据库中：

```sql
-- 连接到数据库
sqlite3 network_management.db

-- 插入SDN设备
INSERT INTO devices (id, name, type, ip_address, mac_address, status, location) VALUES
('sdn-switch-1', 'SDN交换机-1', 'switch', '10.0.0.101', '00:00:00:00:01:01', 'online', '虚拟化环境'),
('sdn-switch-2', 'SDN交换机-2', 'switch', '10.0.0.102', '00:00:00:00:01:02', 'online', '虚拟化环境'),
('sdn-switch-3', 'SDN交换机-3', 'switch', '10.0.0.103', '00:00:00:00:01:03', 'online', '虚拟化环境'),
('sdn-switch-4', 'SDN交换机-4', 'switch', '10.0.0.104', '00:00:00:00:01:04', 'online', '虚拟化环境');

-- 插入SDN链路
INSERT INTO links (id, source_device_id, target_device_id, bandwidth, latency, status) VALUES
('sdn-link-1', 'sdn-switch-1', 'sdn-switch-2', 1000, 1, 'active'),
('sdn-link-2', 'sdn-switch-2', 'sdn-switch-3', 1000, 1, 'active'),
('sdn-link-3', 'sdn-switch-3', 'sdn-switch-4', 1000, 1, 'active'),
('sdn-link-4', 'sdn-switch-4', 'sdn-switch-1', 1000, 1, 'active');
```

### 3. 配置网络管理平台后端

在`backend`目录下创建一个SDN管理模块：

```bash
# 在backend目录下创建sdn_manager.py
python -c "
content = '''#!/usr/bin/env python

\"\"\"SDN网络管理模块\",用于与SDN控制器交互\"\"\"

import requests
import json

class SDNManager:
    def __init__(self, controller_ip='127.0.0.1', controller_port=8080):
        self.controller_ip = controller_ip
        self.controller_port = controller_port
        self.base_url = f'http://{controller_ip}:{controller_port}'
    
    def get_network_topology(self):
        \"\"\"获取网络拓扑信息\"\"\"
        try:
            response = requests.get(f'{self.base_url}/stats/topology')
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"获取拓扑信息失败: {e}")
            return None
    
    def get_switch_flows(self, dpid):
        \"\"\"获取指定交换机的流表信息\"\"\"
        try:
            response = requests.get(f'{self.base_url}/stats/flow/{dpid}')
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"获取流表信息失败: {e}")
            return None
    
    def add_flow_entry(self, dpid, flow_entry):
        \"\"\"向交换机添加流表项\"\"\"
        try:
            response = requests.post(
                f'{self.base_url}/stats/flowentry/add',
                json={"dpid": dpid, "flow": flow_entry}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"添加流表项失败: {e}")
            return False
    
    def delete_flow_entry(self, dpid, flow_entry):
        \"\"\"删除交换机的流表项\"\"\"
        try:
            response = requests.post(
                f'{self.base_url}/stats/flowentry/delete_strict',
                json={"dpid": dpid, "flow": flow_entry}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"删除流表项失败: {e}")
            return False
    
    def get_switch_stats(self):
        \"\"\"获取所有交换机的统计信息\"\"\"
        try:
            response = requests.get(f'{self.base_url}/stats/switches')
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"获取交换机统计信息失败: {e}")
            return None
'''
with open('sdn_manager.py', 'w') as f:
    f.write(content)
print('已创建SDN管理模块: sdn_manager.py')
""
```

### 4. 更新后端API以支持SDN功能

修改`app.py`文件，添加SDN相关的API端点：

```python
# 在app.py中添加以下代码
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from .auth import get_current_user
from .models import User
from .sdn_manager import SDNManager

# 创建SDN管理器实例
sdn_manager = SDNManager()

# 添加SDN相关路由
@app.get("/api/sdn/topology")
async def get_sdn_topology(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取SDN网络拓扑信息"""
    topology = sdn_manager.get_network_topology()
    if not topology:
        raise HTTPException(status_code=500, detail="获取SDN拓扑信息失败")
    return topology

@app.get("/api/sdn/switches")
async def get_sdn_switches(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取SDN交换机列表"""
    switches = sdn_manager.get_switch_stats()
    if switches is None:
        raise HTTPException(status_code=500, detail="获取SDN交换机信息失败")
    return switches

@app.get("/api/sdn/switches/{dpid}/flows")
async def get_switch_flows(dpid: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取指定交换机的流表信息"""
    flows = sdn_manager.get_switch_flows(dpid)
    if flows is None:
        raise HTTPException(status_code=500, detail="获取交换机流表信息失败")
    return flows
```

## 高级功能

### 自定义RYU应用

你可以扩展RYU应用实现更复杂的网络功能。以下是一些示例：

#### 实现简单的负载均衡

```python
# 在simple_switch_13.py中添加负载均衡功能

class LoadBalancingSwitch(SimpleSwitch13):
    def __init__(self, *args, **kwargs):
        super(LoadBalancingSwitch, self).__init__(*args, **kwargs)
        self.server_ips = ['10.0.0.100', '10.0.0.101', '10.0.0.102']
        self.current_server = 0
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # 原有代码...
        
        # 检查是否为TCP数据包，并且目标IP是虚拟IP
        if eth.ethertype == ether_types.ETH_TYPE_IP:
            ip_pkt = pkt.get_protocol(ipv4.ipv4)
            tcp_pkt = pkt.get_protocol(tcp.tcp)
            
            if ip_pkt and tcp_pkt and ip_pkt.dst == '10.0.0.200':
                # 实现简单的轮询负载均衡
                real_server_ip = self.server_ips[self.current_server]
                self.current_server = (self.current_server + 1) % len(self.server_ips)
                
                # 修改数据包的目标IP
                new_ip = copy.deepcopy(ip_pkt)
                new_ip.dst = real_server_ip
                
                # 重新计算校验和
                del new_ip.csum
                new_ip.csum = new_ip.get_hash()
                
                # 构造新的数据包
                new_pkt = packet.Packet()
                new_pkt.add_protocol(eth)
                new_pkt.add_protocol(new_ip)
                new_pkt.add_protocol(tcp_pkt)
                new_pkt.serialize()
                
                # 发送修改后的数据包
                out_port = self.mac_to_port[dpid].get(real_server_ip, ofproto.OFPP_FLOOD)
                actions = [parser.OFPActionOutput(out_port)]
                out = parser.OFPPacketOut(
                    datapath=datapath, buffer_id=msg.buffer_id,
                    in_port=in_port, actions=actions, data=new_pkt.data
                )
                datapath.send_msg(out)
                return
        
        # 原有代码...
```

### 配置网络QoS

使用RYU的QoS功能为不同类型的流量分配带宽：

```python
# 创建qos_switch.py

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, ipv4, tcp, udp

class QoSSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    def __init__(self, *args, **kwargs):
        super(QoSSwitch, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
    
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # 创建队列用于QoS
        # 队列0: 高优先级 (语音/视频)
        # 队列1: 中优先级 (HTTP)
        # 队列2: 低优先级 (其他流量)
        for queue_id in range(3):
            if queue_id == 0:
                # 高优先级队列 - 保证带宽300Mbps
                config = {'max-rate': 300000000, 'min-rate': 300000000}
            elif queue_id == 1:
                # 中优先级队列 - 保证带宽200Mbps
                config = {'max-rate': 200000000, 'min-rate': 200000000}
            else:
                # 低优先级队列 - 剩余带宽
                config = {'max-rate': 100000000}
            
            # 设置队列
            self.set_queue(datapath, queue_id, config)
        
        # 安装基础流表项
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        
        # 安装QoS流表项
        self.install_qos_flows(datapath)
    
    def set_queue(self, datapath, queue_id, config):
        # 实现队列配置
        pass
    
    def install_qos_flows(self, datapath):
        # 安装QoS相关的流表项
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # 语音流量 (UDP端口5060-5061)
        match = parser.OFPMatch(eth_type=0x0800, ip_proto=17,
                               udp_dst=5060, udp_dst_mask=0xffff)
        actions = [parser.OFPActionSetQueue(queue_id=0),
                   parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
        self.add_flow(datapath, 20, match, actions)
        
        # HTTP流量 (TCP端口80)
        match = parser.OFPMatch(eth_type=0x0800, ip_proto=6,
                               tcp_dst=80)
        actions = [parser.OFPActionSetQueue(queue_id=1),
                   parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
        self.add_flow(datapath, 10, match, actions)
```

## 故障排除

### 常见问题及解决方案

1. **控制器无法连接到交换机**
   - 检查RYU控制器是否正在运行
   - 确认控制器IP和端口配置正确
   - 检查防火墙设置，确保6633端口已开放

2. **Mininet拓扑创建失败**
   - 确认Open vSwitch服务正在运行
   - 检查是否有足够的系统资源
   - 尝试使用`sudo`权限运行

3. **主机之间无法通信**
   - 使用`dpctl dump-flows`检查交换机流表
   - 确认RYU应用正确处理了数据包
   - 检查链路配置是否正确

## 总结

通过本指南，你已经学会了如何在虚拟机中搭建SDN环境，配置Mininet拓扑，并与RYU控制器集成。你还了解了如何将SDN环境与网络管理平台连接，以及如何实现一些高级功能如负载均衡和QoS配置。

要进一步扩展功能，你可以：
- 开发更复杂的RYU应用程序
- 集成更多的SDN功能到网络管理平台
- 实现网络自动化和智能调度策略

祝你在SDN网络实验中取得成功！