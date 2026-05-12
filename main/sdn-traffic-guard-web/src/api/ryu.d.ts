declare module '@/api/ryu' {
  const ryuApi: {
    // ---- 原有 ----
    getSummary(): Promise<any>;
    getPorts(): Promise<any>;
    getFlowStats(p: any, s: any, e: any): Promise<any>;
    getPortRate(): Promise<any>;
    getProtocolRatio(p: any, s: any, e: any): Promise<any>;
    getAnomalies(hours?: number, limit?: number | null): Promise<any>;
    
    // 获取攻击会话数据（从attack_sessions表）
    getAttackSessions(hours?: number, limit?: number): Promise<any>;
    
    // 统计不同时间段的攻击会话数量
    getAttackSessionsCount(): Promise<any>;
    
    // 统计不同时间段的已处理攻击会话数量
    getHandledSessionsCount(): Promise<any>;
    
    updateAttackStatus(ip: string, action: string, handledBy?: string): Promise<any>;

    // ---- 新增 ----
    getRateLimit(): Promise<any>;
    getACL(): Promise<any>;
    getAnomaliesWeek(): Promise<any>;
    getAnomaliesTop10(): Promise<any>;
    
    // 设备异常API（真正的设备问题：IP配错、端口异常等）
    getDeviceAnomalies(hours?: number | null, status?: 'pending' | 'handled' | null): Promise<any>;
    updateDeviceAnomalyStatus(anomalyId: number, status?: string, handledBy?: string, handleAction?: string): Promise<any>;
    
    getFlowTop10(): Promise<any>;
    getSwitchInfo(): Promise<any>;
    getWeeklyReport(): Promise<any>;
    exportPDF(): Promise<Blob>;
    getGeoIP(ip: string): Promise<any>;
    putThreshold(body: any): Promise<any>;
    bulkACL(csv: string): Promise<any>;
    
    // 限速趋势图API
    getRateTrend(type?: 'hour' | 'day' | number): Promise<any>;
    
    // 加黑和限速API
    addBlacklist(ip: string, ttl?: number): Promise<any>;
    removeBlacklist(ip: string): Promise<any>;
    addRateLimit(ip: string, kbps?: number, reason?: string, duration_minutes?: number): Promise<any>;
    removeRateLimit(ip: string): Promise<any>;
    
    // 修改限速速率和时间
    changeRateSpeed(ip: string, kbps: number, reason?: string): Promise<any>;
    changeRateDuration(ip: string, extra_seconds: number, reason?: string): Promise<any>;
    
    // 历史限速记录API
    getRateHistoryByDay(day: string): Promise<any>;
    
    // 仪表板卡片数据API
    getDashboardCards(): Promise<any>;
    
    // 限速原因统计API
    getRateReasonStats(hours?: number): Promise<any>;
    
    // 真实流量趋势API（时间序列）
    // 支持：getFlowTrend(60) 获取最近60分钟，或 getFlowTrend('today') 获取今日数据
    getFlowTrend(param?: number | 'today'): Promise<any>;

    // ============= SDN流表管理API =============
    // 获取控制器状态
    getSDNControllerStatus(): Promise<any>;
    
    // 获取所有交换机
    getSDNSwitches(): Promise<any>;
    
    // 获取指定交换机的流表
    getSDNSwitchFlows(dpid: string | number): Promise<any>;
    
    // 获取所有流表
    getSDNAllFlows(): Promise<any>;
    
    // 添加流表项
    addSDNFlowEntry(dpid: string | number, flowEntry: any): Promise<any>;
    
    // 删除流表项
    deleteSDNFlowEntry(dpid: string | number, flowEntry: any): Promise<any>;
    
    // 删除所有流表
    deleteSDNAllFlows(dpid: string | number): Promise<any>;
    
    // 获取交换机端口信息
    getSDNSwitchPorts(dpid: string | number): Promise<any>;
    
    // 创建简单流表
    createSDNSimpleFlow(dpid: string | number, params: any): Promise<any>;
    
    // 获取网络拓扑
    getSDNTopology(): Promise<any>;

    // Mininet 主机信息
    getMininetHosts(): Promise<any>;
  };
  
  export default ryuApi;
}