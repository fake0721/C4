from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import BlacklistEntry, WhitelistEntry, User
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["security"])

# Pydantic模型
class BlacklistEntryCreate(BaseModel):
    ip_address: str
    mac_address: Optional[str] = None
    description: Optional[str] = None
    rule_type: str = "ip"
    is_active: bool = True

class WhitelistEntryCreate(BaseModel):
    ip_address: str
    mac_address: Optional[str] = None
    description: Optional[str] = None
    rule_type: str = "ip"
    is_active: bool = True

class BlacklistEntryResponse(BaseModel):
    id: int
    ip_address: str
    mac_address: Optional[str]
    description: Optional[str]
    rule_type: str
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class WhitelistEntryResponse(BaseModel):
    id: int
    ip_address: str
    mac_address: Optional[str]
    description: Optional[str]
    rule_type: str
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 黑名单API
@router.get("/blacklist", response_model=List[BlacklistEntryResponse])
async def get_blacklist(db: Session = Depends(get_db)):
    """获取所有黑名单条目"""
    entries = db.query(BlacklistEntry).all()
    return entries

@router.post("/blacklist", response_model=BlacklistEntryResponse)
async def create_blacklist_entry(
    entry: BlacklistEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建黑名单条目"""
    # 检查是否已存在相同的IP地址
    existing = db.query(BlacklistEntry).filter(
        BlacklistEntry.ip_address == entry.ip_address
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该IP地址已在黑名单中"
        )
    
    db_entry = BlacklistEntry(
        ip_address=entry.ip_address,
        mac_address=entry.mac_address,
        description=entry.description,
        rule_type=entry.rule_type,
        is_active=entry.is_active,
        created_by=current_user.id
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.put("/blacklist/{entry_id}", response_model=BlacklistEntryResponse)
async def update_blacklist_entry(
    entry_id: int,
    entry: BlacklistEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新黑名单条目"""
    db_entry = db.query(BlacklistEntry).filter(BlacklistEntry.id == entry_id).first()
    if not db_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="黑名单条目不存在"
        )
    
    db_entry.ip_address = entry.ip_address
    db_entry.mac_address = entry.mac_address
    db_entry.description = entry.description
    db_entry.rule_type = entry.rule_type
    db_entry.is_active = entry.is_active
    db_entry.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.delete("/blacklist/{entry_id}")
async def delete_blacklist_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除黑名单条目"""
    db_entry = db.query(BlacklistEntry).filter(BlacklistEntry.id == entry_id).first()
    if not db_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="黑名单条目不存在"
        )
    
    db.delete(db_entry)
    db.commit()
    return {"message": "黑名单条目已删除"}

# 白名单API
@router.get("/whitelist", response_model=List[WhitelistEntryResponse])
async def get_whitelist(db: Session = Depends(get_db)):
    """获取所有白名单条目"""
    entries = db.query(WhitelistEntry).all()
    return entries

@router.post("/whitelist", response_model=WhitelistEntryResponse)
async def create_whitelist_entry(
    entry: WhitelistEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建白名单条目"""
    # 检查是否已存在相同的IP地址
    existing = db.query(WhitelistEntry).filter(
        WhitelistEntry.ip_address == entry.ip_address
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该IP地址已在白名单中"
        )
    
    db_entry = WhitelistEntry(
        ip_address=entry.ip_address,
        mac_address=entry.mac_address,
        description=entry.description,
        rule_type=entry.rule_type,
        is_active=entry.is_active,
        created_by=current_user.id
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.put("/whitelist/{entry_id}", response_model=WhitelistEntryResponse)
async def update_whitelist_entry(
    entry_id: int,
    entry: WhitelistEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新白名单条目"""
    db_entry = db.query(WhitelistEntry).filter(WhitelistEntry.id == entry_id).first()
    if not db_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="白名单条目不存在"
        )
    
    db_entry.ip_address = entry.ip_address
    db_entry.mac_address = entry.mac_address
    db_entry.description = entry.description
    db_entry.rule_type = entry.rule_type
    db_entry.is_active = entry.is_active
    db_entry.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.delete("/whitelist/{entry_id}")
async def delete_whitelist_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除白名单条目"""
    db_entry = db.query(WhitelistEntry).filter(WhitelistEntry.id == entry_id).first()
    if not db_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="白名单条目不存在"
        )
    
    db.delete(db_entry)
    db.commit()
    return {"message": "白名单条目已删除"}