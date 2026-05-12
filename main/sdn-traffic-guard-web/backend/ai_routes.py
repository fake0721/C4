"""
AI Agent API路由 - 集成Kimi大模型和DashScope嵌入模型
提供对话、文件分析、RAG功能
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import asyncio
import uuid
from sqlalchemy.orm import Session
from datetime import datetime
from ai_service import ai_service
from database import get_db
from models import User, AIConversation, AIMessage
from auth import get_current_user

router = APIRouter(prefix="", tags=["AI Agent"])

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class FileAnalysisRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

class ConversationCreateRequest(BaseModel):
    id: str
    title: str
    messages: Optional[List[Dict[str, Any]]] = []

class MessageSaveRequest(BaseModel):
    messages: List[Dict[str, Any]] = []

@router.post("/chat")
async def chat_with_agent(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """与Kimi AI对话"""
    try:
        # 检查是否为RAG查询
        message = request.message.strip()
        if message.startswith('/rag') or '使用知识库' in message:
            # 提取RAG查询内容
            rag_query = message.replace('/rag', '').replace('使用知识库', '').strip()
            result = await ai_service.rag_query(rag_query)
        else:
            result = await ai_service.chat_with_kimi(request.message, request.context)
        
        return {
            "success": True,
            "response": result["response"],
            "tools_used": result.get("tools_used", ["kimi"]),
            "timestamp": result.get("timestamp", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/stream")
async def chat_with_agent_stream(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """与Kimi AI对话 - 流式响应"""
    try:
        from fastapi.responses import StreamingResponse
        import json
        
        # 检查是否为RAG查询（通过上下文标识或消息内容）
        use_rag = False
        rag_query = request.message.strip()
        
        # 检查上下文中的RAG标识
        if request.context and isinstance(request.context, dict):
            use_rag = request.context.get('use_rag', False)
            
        # 或者检查消息内容中的RAG关键词
        if not use_rag:
            message_lower = rag_query.lower()
            rag_keywords = ['文档', '文件', '上传', '资料', '内容', '知识', 'rag', '知识库']
            use_rag = any(keyword in message_lower for keyword in rag_keywords)
        
        if use_rag:
            # RAG查询 - 使用流式响应
            # 从上下文中获取文档信息
            documents = []
            if request.context and isinstance(request.context, dict):
                documents = request.context.get('documents', [])
            
            result = await ai_service.rag_query(rag_query, documents=documents)
            
            async def generate():
                yield f"data: {json.dumps({'type': 'start', 'message': 'AI正在分析文档...'}, ensure_ascii=False)}\n\n"
                
                # 流式输出RAG响应
                if result.get("response"):
                    # 模拟流式输出
                    response_text = result["response"]
                    chunk_size = 100
                    for i in range(0, len(response_text), chunk_size):
                        chunk = response_text[i:i + chunk_size]
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.01)  # 小延迟模拟流式
                
                yield f"data: {json.dumps({'type': 'done', 'content': result.get('response', '')}, ensure_ascii=False)}\n\n"
                
                # 添加文档引用信息
                if result.get("source_documents"):
                    ref_text = "\n\n**参考文档：**"
                    for i, doc in enumerate(result["source_documents"], 1):
                        doc_name = doc.get("metadata", {}).get("source", "未知文档")
                        ref_text += f"\n{i}. {doc_name}"
                    yield f"data: {json.dumps({'type': 'chunk', 'content': ref_text}, ensure_ascii=False)}\n\n"
                
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(generate(), media_type="text/plain")
        else:
            # 普通流式Kimi响应
            result = await ai_service.chat_with_kimi(request.message, request.context, stream=True)
            
            if result.get("stream"):
                async def generate():
                    yield f"data: {json.dumps({'type': 'start', 'message': 'AI正在思考...'}, ensure_ascii=False)}\n\n"
                    
                    full_response = ""
                    async for chunk in result["generator"]:
                        full_response += chunk
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                    
                    yield f"data: {json.dumps({'type': 'done', 'content': full_response}, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                
                return StreamingResponse(generate(), media_type="text/plain")
            else:
                # 非流式响应
                async def generate():
                    yield f"data: {json.dumps({'type': 'start', 'message': 'AI正在思考...'}, ensure_ascii=False)}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'content': result['response']}, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                
                return StreamingResponse(generate(), media_type="text/plain")
                
    except Exception as e:
        async def generate():
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate(), media_type="text/plain")

@router.post("/analyze-csv")
async def analyze_csv_file(
    file: UploadFile = File(...),
    query: str = Form(...),
    context: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """上传并分析CSV文件"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="只支持CSV文件")
        
        content = await file.read()
        file_content = content.decode('utf-8')
        
        context_dict = json.loads(context) if context else None
        
        result = await ai_service.process_file(
            file_content, 
            file.filename, 
            query
        )
        
        return {
            "success": True,
            "filename": file.filename,
            "analysis": result["response"],
            "timestamp": result.get("timestamp", "")
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="上下文格式错误")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-text")
async def analyze_text_document(
    file: UploadFile = File(...),
    query: str = Form(...),
    context: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """分析文本文档"""
    try:
        allowed_extensions = ['.txt', '.md', '.json', '.log']
        file_extension = '.' + file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"支持的文件类型: {', '.join(allowed_extensions)}"
            )
        
        content = await file.read()
        file_content = content.decode('utf-8')
        
        context_dict = json.loads(context) if context else None
        
        result = await ai_agent_service.process_file(
            file_content, 
            file.filename, 
            query
        )
        
        return {
            "success": True,
            "filename": file.filename,
            "analysis": result["response"],
            "timestamp": result.get("timestamp", "")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/network-diagnosis")
async def diagnose_network(config: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """网络配置诊断"""
    try:
        prompt = f"请分析以下网络配置并提供诊断建议:\n{json.dumps(config, ensure_ascii=False, indent=2)}"
        
        result = await ai_service.process_message(prompt)
        
        return {
            "success": True,
            "diagnosis": result["response"],
            "timestamp": result.get("timestamp", "")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-visualization")
async def create_chart(request: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """创建数据可视化图表"""
    try:
        required_fields = ["data", "chart_type", "title"]
        for field in required_fields:
            if field not in request:
                raise HTTPException(status_code=400, detail=f"缺少必需字段: {field}")
        
        prompt = f"请基于以下数据创建{request['chart_type']}图表:\n数据: {json.dumps(request['data'], ensure_ascii=False)}\n标题: {request['title']}"
        
        if "x_label" in request:
            prompt += f"\nX轴标签: {request['x_label']}"
        if "y_label" in request:
            prompt += f"\nY轴标签: {request['y_label']}"
        
        result = await ai_service.process_message(prompt)
        
        return {
            "success": True,
            "chart_data": result["response"],
            "timestamp": result.get("timestamp", "")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_message(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """通用的AI分析接口 - 使用Kimi模型"""
    try:
        result = await ai_service.chat_with_kimi(request.message, request.context)
        return {
            "success": True,
            "response": result["response"],
            "tools_used": result.get("tools_used", ["kimi"]),
            "timestamp": result.get("timestamp", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rag/upload")
async def upload_to_knowledge_base(
    file: UploadFile = File(...),
    query: str = Form("请分析这份文档"),
    current_user: User = Depends(get_current_user)
):
    """上传文件到知识库 - 支持多种格式"""
    try:
        import os
        import io
        import csv
        import json
        
        content = await file.read()
        filename = file.filename
        file_extension = os.path.splitext(filename)[1].lower()
        
        text_content = ""
        
        # 根据文件类型解析内容
        if file_extension == '.txt':
            text_content = content.decode('utf-8')
            
        elif file_extension == '.pdf':
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
            except ImportError:
                raise HTTPException(status_code=400, detail="PDF解析库未安装，请安装PyPDF2")
                
        elif file_extension == '.docx':
            try:
                from docx import Document
                doc = Document(io.BytesIO(content))
                text_content = ""
                for paragraph in doc.paragraphs:
                    text_content += paragraph.text + "\n"
            except ImportError:
                raise HTTPException(status_code=400, detail="Word解析库未安装，请安装python-docx")
                
        elif file_extension == '.csv':
            try:
                csv_content = content.decode('utf-8')
                csv_reader = csv.reader(io.StringIO(csv_content))
                rows = list(csv_reader)
                if rows:
                    headers = rows[0]
                    text_content = f"CSV文件标题: {', '.join(headers)}\n"
                    text_content += f"共{len(rows)-1}行数据\n"
                    text_content += "前5行数据:\n"
                    for i, row in enumerate(rows[1:6]):
                        text_content += f"行{i+1}: {', '.join(row)}\n"
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"CSV解析错误: {str(e)}")
                
        elif file_extension in ['.json']:
            try:
                json_data = json.loads(content.decode('utf-8'))
                text_content = json.dumps(json_data, ensure_ascii=False, indent=2)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"JSON格式错误: {str(e)}")
                
        elif file_extension in ['.xlsx', '.xls']:
            try:
                import pandas as pd
                excel_data = pd.read_excel(io.BytesIO(content))
                text_content = f"Excel文件信息:\n"
                text_content += f"工作表名称: {excel_data.columns.name or '默认'}\n"
                text_content += f"列数: {len(excel_data.columns)}\n"
                text_content += f"行数: {len(excel_data)}\n"
                text_content += f"列名: {', '.join(excel_data.columns.tolist())}\n"
                text_content += "前5行数据:\n"
                text_content += excel_data.head().to_string()
            except ImportError:
                raise HTTPException(status_code=400, detail="Excel解析库未安装，请安装pandas和openpyxl")
                
        else:
            # 尝试作为文本文件处理
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail=f"不支持的文件格式: {file_extension}")
        
        # 检查内容长度
        max_length = 50000  # 50KB限制
        if len(text_content) > max_length:
            text_content = text_content[:max_length] + "...\n[内容已截断]"
        
        try:
            result = await ai_service.add_to_knowledge_base(text_content, filename)
            return {
                "success": True,
                "filename": filename,
                "file_type": file_extension,
                "content_length": len(text_content),
                "analysis": result
            }
        except Exception as e:
            # 处理API密钥无效的情况
            error_msg = str(e)
            if "Invalid API-key" in error_msg or "API Key" in error_msg:
                return {
                    "success": True,
                    "filename": filename,
                    "file_type": file_extension,
                    "content_length": len(text_content),
                    "analysis": {
                        "success": False,
                        "message": "AI分析功能需要配置有效的DashScope API密钥。请在.env文件中设置DASHSCOPE_API_KEY，获取地址：https://dashscope.console.aliyun.com/",
                        "error_type": "api_key_invalid"
                    }
                }
            else:
                return {
                    "success": True,
                    "filename": filename,
                    "file_type": file_extension,
                    "content_length": len(text_content),
                    "analysis": {
                        "success": False,
                        "message": f"AI分析失败：{error_msg}",
                        "error_type": "analysis_error"
                    }
                }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件处理错误: {str(e)}")

@router.post("/rag/query")
async def rag_query(request: ChatRequest):
    """使用RAG查询知识库"""
    try:
        result = await ai_service.rag_query(request.message)
        return {
            "success": True,
            "response": result["response"],
            "source_documents": result.get("source_documents", []),
            "rag_enabled": result.get("rag_enabled", True)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 对话数据库存储相关API
@router.get("/conversations")
async def get_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取当前用户的对话列表"""
    try:
        conversations = db.query(AIConversation).filter(
            AIConversation.user_id == current_user.id
        ).order_by(AIConversation.last_message_at.desc()).all()
        
        return {
            "success": True,
            "conversations": [{
                "id": conv.id,
                "title": conv.title,
                "lastMessageTime": conv.last_message_at.isoformat(),
                "createdAt": conv.created_at.isoformat(),
                "messages": [{
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat(),
                    "file": json.loads(msg.file_data) if msg.file_data else None
                } for msg in conv.messages]
            } for conv in conversations]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations")
async def create_conversation(request: ConversationCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """创建新对话"""
    try:
        # 检查是否已存在
        existing_conv = db.query(AIConversation).filter(
            AIConversation.id == request.id,
            AIConversation.user_id == current_user.id
        ).first()
        if existing_conv:
            return {"success": True, "conversation_id": existing_conv.id}
        
        # 创建新对话
        new_conv = AIConversation(
            id=request.id,
            user_id=current_user.id,
            title=request.title,
            created_at=datetime.utcnow(),
            last_message_at=datetime.utcnow()
        )
        
        db.add(new_conv)
        db.commit()
        
        # 添加初始消息（如果有）
        if request.messages:
            for msg_data in request.messages:
                new_message = AIMessage(
                    id=str(uuid.uuid4()),
                    conversation_id=request.id,
                    role=msg_data.get('role'),
                    content=msg_data.get('content'),
                    file_data=json.dumps(msg_data.get('file')) if msg_data.get('file') else None,
                    created_at=datetime.utcnow()
                )
                db.add(new_message)
            
            db.commit()
        
        return {"success": True, "conversation_id": request.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations/{conversation_id}/messages")
async def save_messages(
    conversation_id: str, 
    request: MessageSaveRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存对话消息"""
    try:
        # 检查对话是否存在且属于当前用户
        conversation = db.query(AIConversation).filter(
            AIConversation.id == conversation_id,
            AIConversation.user_id == current_user.id
        ).first()
        if not conversation:
            # 如果对话不存在，创建新对话
            conversation = AIConversation(
                id=conversation_id,
                user_id=current_user.id,
                title="新对话",
                created_at=datetime.utcnow(),
                last_message_at=datetime.utcnow()
            )
            db.add(conversation)
        
        # 删除旧消息
        db.query(AIMessage).filter(AIMessage.conversation_id == conversation_id).delete()
        
        # 添加新消息
        for msg_data in request.messages:
            new_message = AIMessage(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role=msg_data.get('role'),
                content=msg_data.get('content'),
                file_data=json.dumps(msg_data.get('file')) if msg_data.get('file') else None,
                created_at=datetime.utcnow()
            )
            db.add(new_message)
        
        # 更新最后消息时间
        conversation.last_message_at = datetime.utcnow()
        
        db.commit()
        return {"success": True, "message_count": len(request.messages)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取特定对话的所有消息"""
    try:
        # 检查对话是否属于当前用户
        conversation = db.query(AIConversation).filter(
            AIConversation.id == conversation_id,
            AIConversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在或无权限访问")
        
        messages = db.query(AIMessage).filter(AIMessage.conversation_id == conversation_id).order_by(AIMessage.created_at).all()
        
        return {
            "success": True,
            "messages": [{
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
                "file": json.loads(msg.file_data) if msg.file_data else None
            } for msg in messages]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除特定对话"""
    try:
        # 删除对话及其所有消息（确保属于当前用户）
        conversation = db.query(AIConversation).filter(
            AIConversation.id == conversation_id,
            AIConversation.user_id == current_user.id
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在或无权限删除")
        
        db.delete(conversation)
        db.commit()
        
        return {"success": True, "message": "对话已删除"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/rag/clear")
async def clear_knowledge_base(current_user: User = Depends(get_current_user)):
    """清空知识库"""
    try:
        result = await ai_service.clear_knowledge_base(user_id=current_user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rag/stats")
async def get_knowledge_stats():
    """获取知识库统计"""
    try:
        stats = ai_service.get_knowledge_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"获取知识库统计失败: {str(e)}\n{error_detail}")

@router.get("/capabilities")
async def get_agent_capabilities():
    """获取AI代理的功能列表"""
    return {
        "success": True,
        "capabilities": [
            {
                "name": "Kimi对话",
                "description": "使用Kimi大模型进行智能对话",
                "endpoint": "/ai/analyze",
                "method": "POST"
            },
            {
                "name": "RAG知识库",
                "description": "基于上传文件的智能问答",
                "endpoint": "/ai/rag/query",
                "method": "POST"
            },
            {
                "name": "文件上传",
                "description": "上传文件到知识库用于RAG查询",
                "endpoint": "/ai/rag/upload",
                "method": "POST"
            },
            {
                "name": "CSV分析",
                "description": "分析CSV文件，提供数据统计和可视化",
                "endpoint": "/ai/analyze-csv",
                "method": "POST"
            },
            {
                "name": "文本分析",
                "description": "分析各种文本文档，提取关键信息",
                "endpoint": "/ai/analyze-text",
                "method": "POST"
            },
            {
                "name": "网络诊断",
                "description": "分析网络配置，提供优化建议",
                "endpoint": "/ai/network-diagnosis",
                "method": "POST"
            },
            {
                "name": "数据可视化",
                "description": "创建各种图表和可视化",
                "endpoint": "/ai/create-visualization",
                "method": "POST"
            }
        ],
        "supported_file_types": ["csv", "txt", "md", "json", "log"],
        "chart_types": ["bar", "line", "pie", "scatter", "histogram"]
    }

@router.post("/rag/analyze")
async def analyze_document_content(
    filename: str = Form(...),
    query: str = Form("请详细分析这份文档的内容"),
    current_user: User = Depends(get_current_user)
):
    """分析已上传文档的内容"""
    try:
        # 从知识库中查找文档
        result = await ai_service.query_document_content(filename, query)
        
        if not result["found"]:
            return {
                "success": False,
                "message": f"未找到文档: {filename}",
                "error_type": "document_not_found"
            }
        
        return {
            "success": True,
            "filename": filename,
            "analysis": result["content"],
            "summary": result.get("summary", ""),
            "key_points": result.get("key_points", []),
            "word_count": result.get("word_count", 0)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"分析失败: {str(e)}",
            "error_type": "analysis_error"
        }

@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "agent_initialized": True,
        "timestamp": datetime.utcnow().isoformat()
    }