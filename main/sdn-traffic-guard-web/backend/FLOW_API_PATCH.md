# RYU控制器流表管理API补丁

## 问题
`sdn_smart.py` 缺少流表管理的REST API，导致前端无法获取交换机列表和流表信息。

## 需要在 sdn_smart.py 中添加的代码

在你的 `sdn_smart.py` 文件中，找到其他 `@route` 装饰器的位置（例如在 `@route('summary', '/v1/summary')` 附近），添加以下代码：

```python
# ========== 流表管理API ==========

@route('switches_list', '/v1/switches', methods=['GET'])
def get_switches_list(req, **kwargs):
    """获取所有交换机的DPID列表"""
    try:
        dpids = [dp.id for dp in self.datapaths.values()]
        body = json.dumps(dpids)
        return Response(content_type='application/json', body=body)
    except Exception as e:
        self.logger.error(f"获取交换机列表失败: {e}")
        return Response(status=500, body=str(e))


@route('switch_flows', '/v1/switches/{dpid}/flows', methods=['GET'])
def get_switch_flows(req, dpid, **kwargs):
    """获取指定交换机的流表"""
    try:
        dpid_int = int(dpid)
        if dpid_int not in self.datapaths:
            return Response(status=404, body=json.dumps({"error": "交换机不存在"}))
        
        dp = self.datapaths[dpid_int]
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        
        # 发送FlowStatsRequest
        req_msg = ofp_parser.OFPFlowStatsRequest(dp)
        dp.send_msg(req_msg)
        
        # 注意：实际的流表数据需要在FlowStatsReply事件处理器中获取
        # 这里返回一个占位响应，实际项目中需要实现异步等待机制
        body = json.dumps({
            dpid: []  # 暂时返回空列表
        })
        return Response(content_type='application/json', body=body)
    except Exception as e:
        self.logger.error(f"获取流表失败: {e}")
        return Response(status=500, body=str(e))


@route('add_flow', '/v1/switches/{dpid}/flows', methods=['POST'])
def add_flow_entry(req, dpid, **kwargs):
    """添加流表项"""
    try:
        dpid_int = int(dpid)
        if dpid_int not in self.datapaths:
            return Response(status=404, body=json.dumps({"error": "交换机不存在"}))
        
        # 解析请求body
        body = req.body
        if isinstance(body, bytes):
            body = body.decode('utf-8')
        flow_data = json.loads(body)
        
        dp = self.datapaths[dpid_int]
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        
        # 构建match
        match_dict = flow_data.get('match', {})
        match = ofp_parser.OFPMatch(**match_dict)
        
        # 构建actions
        actions = []
        for action in flow_data.get('actions', []):
            if action.get('type') == 'OUTPUT':
                actions.append(ofp_parser.OFPActionOutput(action['port']))
        
        # 添加流表
        priority = flow_data.get('priority', 100)
        self._add_flow(dp, priority, match, actions)
        
        result = json.dumps({"success": True, "message": "流表添加成功"})
        return Response(content_type='application/json', body=result)
    except Exception as e:
        self.logger.error(f"添加流表失败: {e}")
        return Response(status=500, body=json.dumps({"error": str(e)}))


@route('delete_flow', '/v1/switches/{dpid}/flows', methods=['DELETE'])
def delete_flow_entry(req, dpid, **kwargs):
    """删除流表项"""
    try:
        dpid_int = int(dpid)
        if dpid_int not in self.datapaths:
            return Response(status=404, body=json.dumps({"error": "交换机不存在"}))
        
        # 解析请求body
        body = req.body
        if isinstance(body, bytes):
            body = body.decode('utf-8')
        flow_data = json.loads(body)
        
        dp = self.datapaths[dpid_int]
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        
        # 构建match
        match_dict = flow_data.get('match', {})
        match = ofp_parser.OFPMatch(**match_dict)
        
        # 发送删除流表命令
        mod = ofp_parser.OFPFlowMod(
            datapath=dp,
            match=match,
            command=ofp.OFPFC_DELETE,
            out_group=ofp.OFPG_ANY,
            out_port=ofp.OFPP_ANY
        )
        dp.send_msg(mod)
        
        result = json.dumps({"success": True, "message": "流表删除成功"})
        return Response(content_type='application/json', body=result)
    except Exception as e:
        self.logger.error(f"删除流表失败: {e}")
        return Response(status=500, body=json.dumps({"error": str(e)}))


@route('delete_all_flows', '/v1/switches/{dpid}/flows/all', methods=['DELETE'])
def delete_all_flows(req, dpid, **kwargs):
    """删除指定交换机的所有流表"""
    try:
        dpid_int = int(dpid)
        if dpid_int not in self.datapaths:
            return Response(status=404, body=json.dumps({"error": "交换机不存在"}))
        
        dp = self.datapaths[dpid_int]
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        
        # 删除所有流表（除了table-miss）
        match = ofp_parser.OFPMatch()
        mod = ofp_parser.OFPFlowMod(
            datapath=dp,
            command=ofp.OFPFC_DELETE,
            out_group=ofp.OFPG_ANY,
            out_port=ofp.OFPP_ANY,
            match=match,
            priority=0,
            instructions=[]
        )
        dp.send_msg(mod)
        
        result = json.dumps({"success": True, "message": "所有流表已删除"})
        return Response(content_type='application/json', body=result)
    except Exception as e:
        self.logger.error(f"删除所有流表失败: {e}")
        return Response(status=500, body=json.dumps({"error": str(e)}))
```

## 还需要在类的 __init__ 方法中添加

```python
def __init__(self, *args, **kwargs):
    # ... 现有代码 ...
    
    # 添加这一行来存储所有交换机的引用
    self.datapaths = {}  # 如果已经存在就不用添加
```

## 还需要在 state_change 事件处理器中添加

在 `state_change` 方法中，添加对 `self.datapaths` 的管理：

```python
@set_ev_cls(ofp_event.EventOFPStateChange, [CONFIG_DISPATCHER, MAIN_DISPATCHER])
def state_change(self, ev):
    dp = ev.datapath
    if ev.state == CONFIG_DISPATCHER:
        # 交换机断开连接
        if dp.id in self.datapaths:
            del self.datapaths[dp.id]
            self.logger.info(f"交换机 {dp.id} 已断开")
    elif ev.state == MAIN_DISPATCHER:
        # 交换机连接
        self.datapaths[dp.id] = dp
        self.logger.info(f"交换机 {dp.id} 已连接")
        # ... 现有的table-miss安装代码 ...
```

## 安装步骤

1. 打开 `e:\毕设\network-management-platform\SDN\sdn_smart.py`
2. 在文件中找到其他 `@route` 装饰器的位置
3. 复制上面的流表管理API代码，粘贴到合适的位置
4. 确保 `self.datapaths = {}` 已经在 `__init__` 方法中初始化
5. 更新 `state_change` 方法来管理 `datapaths` 字典
6. 重启RYU控制器：
   ```bash
   # 在Ubuntu上
   cd /home/dsw/SDN
   python3 sdn_smart.py
   ```

## 测试

添加完成后，可以用curl测试：

```bash
# 获取交换机列表
curl http://192.168.126.128:8080/v1/switches

# 获取流表（dpid为1的交换机）
curl http://192.168.126.128:8080/v1/switches/1/flows
```
