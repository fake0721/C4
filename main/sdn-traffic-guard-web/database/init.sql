-- 网络管理平台数据库初始化脚本
CREATE DATABASE IF NOT EXISTS network_management;
USE network_management;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
  id VARCHAR(36) PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  email VARCHAR(100),
  role ENUM('admin', 'user') DEFAULT 'user',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 网络设备表
CREATE TABLE IF NOT EXISTS devices (
  id VARCHAR(36) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  type ENUM('router', 'switch', 'firewall', 'server') NOT NULL,
  ip_address VARCHAR(45),
  mac_address VARCHAR(17),
  status ENUM('online', 'offline', 'maintenance') DEFAULT 'offline',
  location VARCHAR(255),
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 网络链路表
CREATE TABLE IF NOT EXISTS links (
  id VARCHAR(36) PRIMARY KEY,
  source_device_id VARCHAR(36),
  target_device_id VARCHAR(36),
  bandwidth INT COMMENT '带宽，单位Mbps',
  latency INT COMMENT '延迟，单位ms',
  status ENUM('active', 'inactive', 'error') DEFAULT 'active',
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (source_device_id) REFERENCES devices(id),
  FOREIGN KEY (target_device_id) REFERENCES devices(id)
);

-- 黑名单表
CREATE TABLE IF NOT EXISTS blacklist (
  id VARCHAR(36) PRIMARY KEY,
  ip_address VARCHAR(45) NOT NULL,
  reason VARCHAR(255),
  blocked_by VARCHAR(36),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (blocked_by) REFERENCES users(id)
);

-- 网络流量统计表
CREATE TABLE IF NOT EXISTS traffic_stats (
  id VARCHAR(36) PRIMARY KEY,
  device_id VARCHAR(36),
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  bytes_in BIGINT DEFAULT 0,
  bytes_out BIGINT DEFAULT 0,
  packets_in INT DEFAULT 0,
  packets_out INT DEFAULT 0,
  errors_in INT DEFAULT 0,
  errors_out INT DEFAULT 0,
  FOREIGN KEY (device_id) REFERENCES devices(id)
);

-- 系统日志表
CREATE TABLE IF NOT EXISTS system_logs (
  id VARCHAR(36) PRIMARY KEY,
  level ENUM('info', 'warning', 'error', 'critical') NOT NULL,
  message TEXT NOT NULL,
  source VARCHAR(100),
  user_id VARCHAR(36),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 插入默认管理员用户 (密码: admin123)
INSERT IGNORE INTO users (id, username, password, email, role) VALUES 
('admin-uuid-12345', 'admin', '$2b$10$rQZ9qF8xL6KoF3yH9Jl.XuK5vQ2N8mP', 'admin@example.com', 'admin');

-- 插入示例设备数据
INSERT IGNORE INTO devices (id, name, type, ip_address, mac_address, status, location) VALUES
('device-1', '核心路由器-1', 'router', '192.168.1.1', '00:1B:44:11:3A:B7', 'online', '机房A'),
('device-2', '汇聚交换机-1', 'switch', '192.168.1.2', '00:1B:44:11:3A:B8', 'online', '机房A'),
('device-3', '接入交换机-1', 'switch', '192.168.1.3', '00:1B:44:11:3A:B9', 'online', '机房B'),
('device-4', '防火墙-1', 'firewall', '192.168.1.254', '00:1B:44:11:3A:BA', 'online', '机房A');

-- 插入示例链路数据
INSERT IGNORE INTO links (id, source_device_id, target_device_id, bandwidth, latency, status) VALUES
('link-1', 'device-1', 'device-2', 1000, 2, 'active'),
('link-2', 'device-2', 'device-3', 100, 5, 'active'),
('link-3', 'device-1', 'device-4', 1000, 1, 'active');

CREATE INDEX idx_devices_ip ON devices(ip_address);
CREATE INDEX idx_links_devices ON links(source_device_id, target_device_id);
CREATE INDEX idx_traffic_timestamp ON traffic_stats(timestamp);
CREATE INDEX idx_logs_level ON system_logs(level, created_at);
CREATE INDEX idx_blacklist_ip ON blacklist(ip_address);