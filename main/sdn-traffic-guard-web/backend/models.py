from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), default="admin")  # 默认管理员
    avatar = Column(Text, nullable=True)  # base64 头像，可为空
    # 对齐 MySQL 表字段：created_at / updated_at
    created_at = Column("created_at", DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column("updated_at", DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 仅为满足外键关系映射，不会新增列
    devices = relationship("Device", back_populates="user", uselist=True)
    reset_tokens = relationship("PasswordResetToken", back_populates="user", uselist=True)
    ai_conversations = relationship("AIConversation", back_populates="user", uselist=True)
    ai_files = relationship("AIFile", back_populates="user", uselist=True)

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=False)
    device_type = Column(String(50), nullable=False)
    location = Column(String(200))
    status = Column(String(20), default="offline")
    user_id = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="devices")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(String(50), primary_key=True, index=True, default=lambda: f"reset-{int(datetime.utcnow().timestamp() * 1000)}-{str(uuid.uuid4())[:8]}")
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="reset_tokens")

# AI对话相关模型
class AIConversation(Base):
    __tablename__ = "ai_conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="ai_conversations")
    messages = relationship("AIMessage", back_populates="conversation", cascade="all, delete-orphan")

class AIMessage(Base):
    __tablename__ = "ai_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("ai_conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    file_data = Column(Text)  # JSON字符串存储文件信息
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("AIConversation", back_populates="messages")

class AIFile(Base):
    __tablename__ = "ai_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_data = Column(LargeBinary)  # 存储文件二进制数据
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="ai_files")

# SDN相关模型
class SDNController(Base):
    __tablename__ = "sdn_controllers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=False)
    port = Column(Integer, nullable=False, default=6633)
    type = Column(String(50), nullable=False, default="RYU")
    status = Column(String(20), default="offline")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    switches = relationship("SDNSwitch", back_populates="controller")

class SDNSwitch(Base):
    __tablename__ = "sdn_switches"

    id = Column(Integer, primary_key=True, index=True)
    dpid = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    controller_id = Column(Integer, ForeignKey("sdn_controllers.id"))
    status = Column(String(20), default="disconnected")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    controller = relationship("SDNController", back_populates="switches")
    ports = relationship("SDNPort", back_populates="switch")

class SDNPort(Base):
    __tablename__ = "sdn_ports"

    id = Column(Integer, primary_key=True, index=True)
    switch_id = Column(Integer, ForeignKey("sdn_switches.id"))
    port_number = Column(Integer, nullable=False)
    name = Column(String(100))
    speed = Column(Integer)  # 端口速度，单位Mbps
    status = Column(String(20), default="down")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    switch = relationship("SDNSwitch", back_populates="ports")

class SDNLink(Base):
    __tablename__ = "sdn_links"

    id = Column(Integer, primary_key=True, index=True)
    source_switch_id = Column(Integer, ForeignKey("sdn_switches.id"))
    source_port = Column(Integer, nullable=False)
    destination_switch_id = Column(Integer, ForeignKey("sdn_switches.id"))
    destination_port = Column(Integer, nullable=False)
    bandwidth = Column(Integer)  # 带宽，单位Mbps
    delay = Column(Integer)  # 延迟，单位ms
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    source_switch = relationship("SDNSwitch", foreign_keys=[source_switch_id])
    destination_switch = relationship("SDNSwitch", foreign_keys=[destination_switch_id])

class SDNHost(Base):
    __tablename__ = "sdn_hosts"

    id = Column(Integer, primary_key=True, index=True)
    mac_address = Column(String(50), unique=True, index=True, nullable=False)
    ip_address = Column(String(45), nullable=False)
    name = Column(String(100))
    connected_switch_id = Column(Integer, ForeignKey("sdn_switches.id"))
    connected_port = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    connected_switch = relationship("SDNSwitch")


# 流量监控相关模型
class TrafficFlow(Base):
    __tablename__ = "traffic_flows"

    id = Column(Integer, primary_key=True, index=True)
    switch_dpid = Column(String(50), nullable=False, index=True)
    in_port = Column(Integer, nullable=False)
    eth_src = Column(String(50), nullable=False)
    eth_dst = Column(String(50), nullable=False)
    eth_type = Column(Integer, nullable=False)
    ip_proto = Column(Integer, nullable=True)
    src_ip = Column(String(45), nullable=True)
    dst_ip = Column(String(45), nullable=True)
    src_port = Column(Integer, nullable=True)
    dst_port = Column(Integer, nullable=True)
    packet_count = Column(Integer, default=0)
    byte_count = Column(Integer, default=0)
    duration_sec = Column(Integer, default=0)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TrafficStat(Base):
    __tablename__ = "traffic_stats"

    id = Column(Integer, primary_key=True, index=True)
    switch_dpid = Column(String(50), nullable=False, index=True)
    port_number = Column(Integer, nullable=False)
    rx_packets = Column(Integer, default=0)
    rx_bytes = Column(Integer, default=0)
    rx_errors = Column(Integer, default=0)
    tx_packets = Column(Integer, default=0)
    tx_bytes = Column(Integer, default=0)
    tx_errors = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class PortUtilization(Base):
    __tablename__ = "port_utilizations"

    id = Column(Integer, primary_key=True, index=True)
    switch_dpid = Column(String(50), nullable=False, index=True)
    port_number = Column(Integer, nullable=False)
    utilization_percent = Column(Integer, default=0)  # 端口利用率百分比
    bandwidth_mbps = Column(Integer, default=0)  # 当前带宽使用量
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

# 黑白名单管理模型
class BlacklistEntry(Base):
    __tablename__ = "blacklist_entries"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), nullable=False, index=True)
    mac_address = Column(String(50), nullable=True, index=True)
    description = Column(String(255), nullable=True)
    rule_type = Column(String(20), default="ip")  # ip, mac, ip_range
    is_active = Column(Boolean, default=True)
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = relationship("User")

class WhitelistEntry(Base):
    __tablename__ = "whitelist_entries"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), nullable=False, index=True)
    mac_address = Column(String(50), nullable=True, index=True)
    description = Column(String(255), nullable=True)
    rule_type = Column(String(20), default="ip")  # ip, mac, ip_range
    is_active = Column(Boolean, default=True)
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = relationship("User")
