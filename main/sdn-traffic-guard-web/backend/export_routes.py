import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from export_service import ExportService, REPORT_DEFINITIONS
from models import User


router = APIRouter(prefix="/v1/exports", tags=["exports"])


class ExportCreateRequest(BaseModel):
    export_type: str = Field(..., description="anomalies|attack_sessions|ai_analysis|handling_records")
    format: str = Field(..., description="pdf|docx")
    filters: Dict[str, Any] = Field(default_factory=dict)
    payload: Dict[str, Any] = Field(default_factory=dict)


def ensure_export_tables(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS export_tasks (
              id VARCHAR(36) PRIMARY KEY,
              export_type VARCHAR(50) NOT NULL,
              file_format VARCHAR(20) NOT NULL,
              filters_json TEXT,
              status VARCHAR(20) NOT NULL,
              filename VARCHAR(255),
              file_path TEXT,
              row_count INT DEFAULT 0,
              error_message TEXT,
              created_by VARCHAR(100),
              created_at DATETIME NOT NULL,
              completed_at DATETIME
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS export_audit_logs (
              id VARCHAR(36) PRIMARY KEY,
              task_id VARCHAR(36) NOT NULL,
              username VARCHAR(100),
              export_type VARCHAR(50) NOT NULL,
              file_format VARCHAR(20) NOT NULL,
              filters_json TEXT,
              created_at DATETIME NOT NULL,
              client_ip VARCHAR(64),
              user_agent TEXT
            )
            """
        )
    )
    db.commit()


def resolve_username(request: Request, db: Session) -> str:
    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        return "unknown"
    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return "unknown"
    user = db.query(User).filter(User.id == token).first()
    return user.username if user else "unknown"


def record_export_task(db: Session, result: Dict[str, Any], filters: Dict[str, Any], username: str) -> None:
    ensure_export_tables(db)
    db.execute(
        text(
            """
            INSERT INTO export_tasks
            (id, export_type, file_format, filters_json, status, filename, file_path,
             row_count, error_message, created_by, created_at, completed_at)
            VALUES
            (:id, :export_type, :file_format, :filters_json, :status, :filename, :file_path,
             :row_count, :error_message, :created_by, :created_at, :completed_at)
            """
        ),
        {
            "id": result["id"],
            "export_type": result["export_type"],
            "file_format": result["format"],
            "filters_json": json.dumps(filters, ensure_ascii=False),
            "status": result["status"],
            "filename": result["filename"],
            "file_path": result["file_path"],
            "row_count": result.get("row_count", 0),
            "error_message": result.get("error_message"),
            "created_by": username,
            "created_at": result["created_at"].replace("T", " "),
            "completed_at": result["completed_at"].replace("T", " "),
        },
    )
    db.commit()


def record_export_audit(
    db: Session,
    request: Request,
    result: Dict[str, Any],
    filters: Dict[str, Any],
    username: str,
) -> None:
    db.execute(
        text(
            """
            INSERT INTO export_audit_logs
            (id, task_id, username, export_type, file_format, filters_json,
             created_at, client_ip, user_agent)
            VALUES
            (UUID(), :task_id, :username, :export_type, :file_format, :filters_json,
             :created_at, :client_ip, :user_agent)
            """
        ),
        {
            "task_id": result["id"],
            "username": username,
            "export_type": result["export_type"],
            "file_format": result["format"],
            "filters_json": json.dumps(filters, ensure_ascii=False),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "client_ip": request.client.host if request.client else "",
            "user_agent": request.headers.get("user-agent", ""),
        },
    )
    db.commit()


@router.get("/options")
async def get_export_options():
    return {
        "success": True,
        "types": [
            {"value": key, "label": value["title"], "summary": value["summary"]}
            for key, value in REPORT_DEFINITIONS.items()
        ],
        "formats": ["pdf", "docx"],
    }


@router.post("")
async def create_export(req: ExportCreateRequest, request: Request, db: Session = Depends(get_db)):
    username = resolve_username(request, db)
    try:
        result = ExportService().create_export(
            export_type=req.export_type,
            export_format=req.format,
            filters=req.filters,
            username=username,
            payload=req.payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(exc)}")

    audit_warning = None
    try:
        record_export_task(db, result, req.filters, username)
        record_export_audit(db, request, result, req.filters, username)
    except Exception as exc:
        db.rollback()
        audit_warning = f"导出文件已生成，但任务/审计记录写入失败: {str(exc)}"

    return {
        "success": True,
        "task": {key: value for key, value in result.items() if key != "file_path"},
        "download_url": f"/v1/exports/{result['id']}/download",
        "audit_warning": audit_warning,
    }


@router.get("/{task_id}")
async def get_export_task(task_id: str, db: Session = Depends(get_db)):
    try:
        ensure_export_tables(db)
        row = db.execute(
            text(
                """
                SELECT id, export_type, file_format, filters_json, status, filename,
                       row_count, error_message, created_by, created_at, completed_at
                FROM export_tasks
                WHERE id = :task_id
                """
            ),
            {"task_id": task_id},
        ).mappings().first()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"查询导出任务失败: {str(exc)}")

    if not row:
        raise HTTPException(status_code=404, detail="导出任务不存在")
    return {"success": True, "task": dict(row)}


@router.get("/{task_id}/download")
async def download_export(task_id: str, db: Session = Depends(get_db)):
    try:
        ensure_export_tables(db)
        row = db.execute(
            text("SELECT filename, file_path, file_format FROM export_tasks WHERE id = :task_id"),
            {"task_id": task_id},
        ).mappings().first()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"查询导出文件失败: {str(exc)}")

    if not row:
        raise HTTPException(status_code=404, detail="导出任务不存在")

    file_path = Path(row["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="导出文件不存在或已被清理")

    media_type = (
        "application/pdf"
        if row["file_format"] == "pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    return FileResponse(path=file_path, filename=row["filename"], media_type=media_type)
