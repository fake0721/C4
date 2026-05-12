from fastapi import FastAPI, HTTPException, Depends, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import uuid
import os
from dotenv import load_dotenv

# 确保在项目根目录加载.env文件
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

from database import engine, Base, get_db
from models import User, AIConversation, AIMessage, AIFile, PasswordResetToken
from auth import get_current_user



# 注意：使用已有 MySQL 表结构，启动时不自动建表，避免与现有表类型冲突

# Pydantic模型
class UserCreate(BaseModel):
    username: str
    password: str
    avatar: str = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    created_at: datetime | None = None

class ForgotPasswordRequest(BaseModel):
    username: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class GetPasswordRequest(BaseModel):
    username: str

class ChangePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str

# FastAPI应用
app = FastAPI(title="基于SDN的流量检测与监控系统API", version="1.0.0")

# CORS配置 - 允许前端开发服务器访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173", 
        "http://localhost:5174", "http://127.0.0.1:5174",
        "http://localhost:5175", "http://127.0.0.1:5175",
        "http://localhost:5176", "http://127.0.0.1:5176"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 导入AI路由
# AI路由已移除，使用Ollama替代

# API路由前缀
API_PREFIX = "/api"

# 用户登录API
@app.post(f"{API_PREFIX}/auth/login")
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    username_norm = user_login.username.strip().lower()
    user = (
        db.query(User)
        .filter(func.lower(User.username) == username_norm)
        .first()
    )
    if not user or user.password != user_login.password:
        return {"success": False, "message": "用户名或密码错误"}
    
    # 返回用户信息和token（这里简化处理，使用用户ID作为token）
    return {
        "success": True,
        "message": "登录成功",
        "token": str(user.id),
        "user": {
            "id": str(user.id),
            "username": user.username,
            "role": user.role,
            "created_at": user.created_at,
            "avatar": getattr(user, "avatar", None)
        }
    }

# 导入SDN路由（已迁移到v1_routes.py，不再需要单独的sdn_router）
# from sdn_routes import sdn_router
# app.include_router(sdn_router)

# 导入黑白名单路由
from blacklist_routes import router as blacklist_router
app.include_router(blacklist_router)

# 导入Ollama路由
from ollama_routes import router as ollama_router
app.include_router(ollama_router)

# 导入V1路由
from v1_routes import router as v1_router
# 同时支持/api/v1和/v1两种路径格式
app.include_router(v1_router, prefix="/api")
app.include_router(v1_router)

# 导入Agent路由（RAG + MCP + Agent）
try:
    from agent_routes import router as agent_router
    app.include_router(agent_router)
    print("Agent routes loaded")
except Exception as e:
    print(f"Agent routes load failed: {e}")



# API路由
@app.get("/")
async def root():
    return {"message": "基于SDN的流量检测与监控系统API服务已启动"}

@app.post("/api/auth/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # 输入验证
        if not user.username or len(user.username.strip()) < 3:
            raise HTTPException(status_code=400, detail="用户名长度不能少于3个字符")
        
        if not user.password or len(user.password) < 6:
            raise HTTPException(status_code=400, detail="密码长度不能少于6个字符")
        
        username_clean = user.username.strip()
        username_norm = username_clean.lower()

        # 检查用户名是否已存在
        existing_user = (
            db.query(User)
            .filter(func.lower(User.username) == username_norm)
            .first()
        )
        if existing_user:
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 创建新用户
        new_user = User(
            username=username_clean,
            password=user.password,  # 生产环境应使用哈希
            role="admin"  # 所有新用户设为管理员
        )
        # 如果数据库存在 avatar 字段则写入，否则忽略
        if hasattr(User, "avatar") and user.avatar:
            new_user.avatar = user.avatar.strip()
        # 明确写入时间，避免数据库未自动填充时为空
        if hasattr(new_user, "created_at") and not new_user.created_at:
            new_user.created_at = datetime.utcnow()
        if hasattr(new_user, "updated_at") and not new_user.updated_at:
            new_user.updated_at = datetime.utcnow()
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "success": True,
        "message": "注册成功",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "role": new_user.role,
            "avatar": getattr(new_user, "avatar", None)
        }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"注册错误: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误，请稍后重试")



@app.get("/api/users")
async def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return {"users": [{
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "created_at": user.created_at
    } for user in users]}

@app.get("/api/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前登录用户的信息"""
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
            "created_at": current_user.created_at,
            "avatar": getattr(current_user, "avatar", None)
        }
    }

@app.post("/api/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # 检查用户名是否存在
    username_norm = request.username.strip().lower()
    user = (
        db.query(User)
        .filter(func.lower(User.username) == username_norm)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 生成重置token
    reset_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=30)  # 30分钟后过期
    
    # 保存token到数据库
    reset_entry = PasswordResetToken(
        id=f"reset-{int(datetime.now().timestamp() * 1000)}-{str(uuid.uuid4())[:8]}",
        user_id=user.id,
        token=reset_token,
        expires_at=expires_at
    )
    
    db.add(reset_entry)
    db.commit()
    
    # 在实际环境中，这里应该发送邮件
    # 为了演示，我们返回token
    return {
        "success": True,
        "message": "重置邮件已发送",
        "reset_token": reset_token,  # 演示用，实际应该通过邮件发送
        "expires_at": expires_at.isoformat()
    }

@app.post("/api/auth/verify-reset-token")
async def verify_reset_token(token: str, db: Session = Depends(get_db)):
    # 查找有效的token
    reset_entry = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.expires_at > datetime.utcnow(),
        PasswordResetToken.used == False
    ).first()
    
    if not reset_entry:
        raise HTTPException(status_code=400, detail="无效的或已过期的重置链接")
    
    return {
        "success": True,
        "message": "重置链接有效",
        "user_id": reset_entry.user_id
    }

@app.post("/api/auth/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    # 查找有效的token
    reset_entry = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == request.token,
        PasswordResetToken.expires_at > datetime.utcnow(),
        PasswordResetToken.used == False
    ).first()
    
    if not reset_entry:
        raise HTTPException(status_code=400, detail="无效的或已过期的重置链接")
    
    # 更新用户密码
    user = db.query(User).filter(User.id == reset_entry.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.password = request.new_password  # 生产环境应使用哈希
    reset_entry.used = True
    
    db.commit()
    
    return {
        "success": True,
        "message": "密码重置成功"
    }

@app.post("/api/auth/get-password")
async def get_password(request: GetPasswordRequest, db: Session = Depends(get_db)):
    # 查找用户
    username_norm = request.username.strip().lower()
    user = (
        db.query(User)
        .filter(func.lower(User.username) == username_norm)
        .first()
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "success": True,
        "message": "密码获取成功",
        "password": user.password  # 注意：生产环境不应该返回明文密码
    }

@app.post("/api/auth/change-password")
async def change_password(request: ChangePasswordRequest, db: Session = Depends(get_db)):
    # 检查用户是否存在
    username_norm = request.username.strip().lower()
    user_check = (
        db.query(User)
        .filter(func.lower(User.username) == username_norm)
        .first()
    )
    if not user_check:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 验证密码
    user = (
        db.query(User)
        .filter(
            func.lower(User.username) == username_norm,
            User.password == request.old_password
        )
        .first()
    )
    
    if not user:
        raise HTTPException(status_code=401, detail="原密码错误")
    
    # 更新用户密码
    user.password = request.new_password  # 生产环境应使用哈希
    db.commit()
    
    return {
        "success": True,
        "message": "密码修改成功"
    }

@app.post("/api/auth/update-avatar")
async def update_avatar(
    username: str = Form(...),
    avatar: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """更新用户头像"""
    # 检查用户是否存在
    username_norm = username.strip().lower()
    user = (
        db.query(User)
        .filter(func.lower(User.username) == username_norm)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 验证文件类型
    if not avatar.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="请上传图片文件")
    
    # 读取文件内容
    contents = await avatar.read()
    
    # 检查文件大小 (2MB)
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过2MB")
    
    # 将图片转换为base64
    import base64
    avatar_base64 = base64.b64encode(contents).decode('utf-8')
    
    # 更新用户头像
    if not hasattr(User, "avatar"):
        raise HTTPException(status_code=500, detail="数据库未配置头像字段，请联系管理员")
    user.avatar = f"data:{avatar.content_type};base64,{avatar_base64}"
    if hasattr(user, "updated_at"):
        user.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "头像更新成功",
        "avatar_url": user.avatar
    }

@app.get("/api/auth/user-avatar/{username}")
async def get_user_avatar(username: str, db: Session = Depends(get_db)):
    """获取用户头像"""
    # 检查用户是否存在
    username_norm = username.strip().lower()
    user = (
        db.query(User)
        .filter(func.lower(User.username) == username_norm)
        .first()
    )
    if not user:
        return {
            "success": False,
            "message": "用户不存在",
            "avatar": None
        }
    
    return {
        "success": True,
        "message": "获取头像成功",
        "avatar": getattr(user, "avatar", None)
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
