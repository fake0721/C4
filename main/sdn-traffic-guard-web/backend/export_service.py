import html
import json
import math
import re
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


REPORT_DEFINITIONS = {
    "anomalies": {
        "title": "异常事件报告",
        "summary": "导出指定时间范围内的异常检测事件。",
        "columns": [
            ("风险", "severity"),
            ("攻击类型", "type"),
            ("攻击来源", "src_ip"),
            ("检测时间", "detect_time"),
            ("状态", "status"),
        ],
    },
    "attack_sessions": {
        "title": "攻击会话摘要",
        "summary": "导出攻击会话的来源、类型、状态和处置概况。",
        "columns": [
            ("攻击来源", "src_ip"),
            ("攻击类型", "type"),
            ("风险", "severity"),
            ("检测时间", "detect_time"),
            ("状态", "status"),
        ],
    },
    "ai_analysis": {
        "title": "AI 研判报告",
        "summary": "导出当前 AI 助手会话或本次智能分析结果。",
        "columns": [
            ("角色", "role"),
            ("内容", "content"),
            ("时间", "timestamp"),
        ],
    },
    "handling_records": {
        "title": "处置记录报告",
        "summary": "导出限速、封禁、解除等安全处置记录。",
        "columns": [
            ("处置对象", "src_ip"),
            ("处置动作", "action"),
            ("处置原因", "reason"),
            ("处置时间", "created_at"),
            ("操作者", "operator"),
        ],
    },
}

PALETTE = {
    "navy": "0F2A4A",
    "blue": "2563EB",
    "cyan": "06B6D4",
    "green": "16A34A",
    "orange": "F97316",
    "red": "DC2626",
    "purple": "7C3AED",
    "gray": "F3F6FA",
    "slate": "475569",
    "white": "FFFFFF",
}


class ExportService:
    """Generate export files without requiring optional third-party packages."""

    SUPPORTED_FORMATS = {"pdf", "docx"}

    def __init__(self, output_dir: Optional[str | Path] = None):
        base_dir = Path(__file__).resolve().parent
        self.output_dir = Path(output_dir) if output_dir else base_dir / "generated_exports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_export(
        self,
        export_type: str,
        export_format: str,
        filters: Optional[Dict[str, Any]],
        username: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        export_type = (export_type or "").strip()
        export_format = (export_format or "").strip().lower()
        filters = filters or {}
        payload = payload or {}

        if export_type not in REPORT_DEFINITIONS:
            raise ValueError(f"不支持的导出类型: {export_type}")
        if export_format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的导出格式: {export_format}")

        task_id = str(uuid.uuid4())
        created_at = datetime.now()
        rows = self._extract_rows(export_type, payload)
        report = self._build_report(export_type, filters, username, created_at, rows)
        filename = self._build_filename(export_type, export_format, created_at, task_id)
        file_path = self.output_dir / filename

        if export_format == "docx":
            self._write_docx(file_path, report)
        else:
            self._write_pdf(file_path, report)

        return {
            "id": task_id,
            "export_type": export_type,
            "format": export_format,
            "status": "success",
            "filename": filename,
            "file_path": str(file_path),
            "created_at": created_at.isoformat(timespec="seconds"),
            "completed_at": datetime.now().isoformat(timespec="seconds"),
            "row_count": len(rows),
        }

    def _extract_rows(self, export_type: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        if isinstance(payload.get("items"), list):
            return [self._coerce_mapping(item) for item in payload["items"]]
        if export_type == "ai_analysis" and isinstance(payload.get("messages"), list):
            return [self._coerce_mapping(item) for item in payload["messages"]]
        if export_type == "ai_analysis" and payload.get("analysis"):
            return [{"role": "assistant", "content": str(payload["analysis"]), "timestamp": ""}]
        return []

    def _coerce_mapping(self, value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {"content": str(value)}

    def _build_report(
        self,
        export_type: str,
        filters: Dict[str, Any],
        username: str,
        created_at: datetime,
        rows: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        definition = REPORT_DEFINITIONS[export_type]
        return {
            "title": definition["title"],
            "summary": definition["summary"],
            "columns": definition["columns"],
            "filters": filters,
            "username": username or "unknown",
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "rows": rows,
            "metrics": self._build_metrics(rows),
            "severity_counts": self._count_values(rows, ["severity", "risk_level"]),
            "type_counts": self._count_values(rows, ["type", "anomaly_type", "attack_type", "reason"]),
            "status_counts": self._count_values(rows, ["status", "action"]),
            "findings": self._build_findings(rows),
            "recommendations": self._build_recommendations(rows),
        }

    def _build_filename(self, export_type: str, export_format: str, created_at: datetime, task_id: str) -> str:
        timestamp = created_at.strftime("%Y%m%d_%H%M%S")
        safe_type = re.sub(r"[^a-zA-Z0-9_-]+", "_", export_type)
        return f"{safe_type}_{timestamp}_{task_id[:8]}.{export_format}"

    def _render_lines(self, report: Dict[str, Any]) -> List[str]:
        lines = [
            report["title"],
            f"导出人: {report['username']}",
            f"导出时间: {report['created_at']}",
            f"筛选条件: {json.dumps(report['filters'], ensure_ascii=False)}",
            f"记录数量: {len(report['rows'])}",
            report["summary"],
            "",
        ]
        headers = [label for label, _ in report["columns"]]
        lines.append(" | ".join(headers))
        lines.append("-" * 72)
        for row in report["rows"]:
            values = [self._cell_text(row.get(key, "")) for _, key in report["columns"]]
            lines.append(" | ".join(values))
        if not report["rows"]:
            lines.append("暂无可导出的明细数据")
        return lines

    def _cell_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def _build_metrics(self, rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        unique_sources = {
            self._cell_text(row.get("src_ip") or row.get("ip") or row.get("source") or "")
            for row in rows
            if row.get("src_ip") or row.get("ip") or row.get("source")
        }
        high_risk = sum(1 for row in rows if self._normalise_severity(row.get("severity") or row.get("risk_level")) == "high")
        handled = sum(1 for row in rows if self._normalise_status(row.get("status") or row.get("action")) == "handled")
        return [
            {"label": "总记录数", "value": str(len(rows)), "color": PALETTE["blue"]},
            {"label": "攻击源数量", "value": str(len(unique_sources)), "color": PALETTE["cyan"]},
            {"label": "高风险事件", "value": str(high_risk), "color": PALETTE["red"]},
            {"label": "已处置数量", "value": str(handled), "color": PALETTE["green"]},
        ]

    def _count_values(self, rows: List[Dict[str, Any]], keys: List[str]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for row in rows:
            value = ""
            for key in keys:
                if row.get(key):
                    value = self._cell_text(row[key])
                    break
            value = value or "未知"
            counts[value] = counts.get(value, 0) + 1
        return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:8])

    def _normalise_severity(self, value: Any) -> str:
        text = self._cell_text(value).lower()
        if text in {"high", "critical", "严重", "高", "极高"}:
            return "high"
        if text in {"medium", "moderate", "中", "中等"}:
            return "medium"
        if text in {"low", "低"}:
            return "low"
        return "unknown"

    def _normalise_status(self, value: Any) -> str:
        text = self._cell_text(value).lower()
        if text in {"handled", "resolved", "done", "limit", "release", "block", "已处理", "已处置"}:
            return "handled"
        return "pending"

    def _build_findings(self, rows: List[Dict[str, Any]]) -> List[str]:
        if not rows:
            return ["当前筛选范围内暂无可分析记录。"]
        type_counts = self._count_values(rows, ["type", "anomaly_type", "attack_type", "reason"])
        severity_counts = self._count_values(rows, ["severity", "risk_level"])
        status_counts = self._count_values(rows, ["status", "action"])
        top_type = next(iter(type_counts), "未知")
        high_count = sum(1 for row in rows if self._normalise_severity(row.get("severity") or row.get("risk_level")) == "high")
        pending_count = sum(1 for row in rows if self._normalise_status(row.get("status") or row.get("action")) == "pending")
        return [
            f"本次导出共包含 {len(rows)} 条记录，主要事件类型为 {top_type}。",
            f"高风险事件 {high_count} 条，风险等级分布为 {self._format_counts(severity_counts)}。",
            f"待处理记录 {pending_count} 条，状态/处置分布为 {self._format_counts(status_counts)}。",
        ]

    def _build_recommendations(self, rows: List[Dict[str, Any]]) -> List[str]:
        if not rows:
            return ["保持现有监控策略，继续观察后续异常趋势。"]
        high_count = sum(1 for row in rows if self._normalise_severity(row.get("severity") or row.get("risk_level")) == "high")
        pending_count = sum(1 for row in rows if self._normalise_status(row.get("status") or row.get("action")) == "pending")
        recommendations = []
        if high_count:
            recommendations.append("优先复核高风险来源 IP，必要时执行限速、封禁或隔离策略。")
        if pending_count:
            recommendations.append("对待处理记录建立处置闭环，补充处理人、处理动作和完成时间。")
        recommendations.append("持续观察攻击类型 Top 项，针对重复出现的类型优化检测阈值和防御规则。")
        return recommendations

    def _write_docx(self, path: Path, report: Dict[str, Any]) -> None:
        document_xml = self._docx_document_xml(report)
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", self._docx_content_types())
            archive.writestr("_rels/.rels", self._docx_relationships())
            archive.writestr("word/document.xml", document_xml)

    def _docx_document_xml(self, report: Dict[str, Any]) -> str:
        body_parts = [
            self._docx_paragraph(report["title"], bold=True, size="36"),
            self._docx_paragraph(f"导出人: {report['username']}"),
            self._docx_paragraph(f"导出时间: {report['created_at']}"),
            self._docx_paragraph(f"筛选条件: {json.dumps(report['filters'], ensure_ascii=False)}"),
            self._docx_paragraph("报告说明", bold=True, size="28"),
            self._docx_paragraph(report["summary"]),
            self._docx_paragraph("统计摘要", bold=True, size="28"),
            self._docx_summary_table(report),
            self._docx_paragraph("重点发现", bold=True, size="28"),
            self._docx_list(report["findings"]),
            self._docx_paragraph("处置建议", bold=True, size="28"),
            self._docx_list(report["recommendations"]),
            self._docx_paragraph("事件明细", bold=True, size="28"),
            self._docx_table(report["columns"], report["rows"]),
        ]
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f"<w:body>{''.join(body_parts)}<w:sectPr/></w:body></w:document>"
        )

    def _docx_paragraph(self, text: str, bold: bool = False, size: str = "24", color: str = "111827") -> str:
        escaped = html.escape(text)
        bold_xml = "<w:b/>" if bold else ""
        return (
            "<w:p><w:r><w:rPr>"
            f'{bold_xml}<w:color w:val="{color}"/><w:sz w:val="{size}"/>'
            f"</w:rPr><w:t>{escaped}</w:t></w:r></w:p>"
        )

    def _docx_summary_table(self, report: Dict[str, Any]) -> str:
        rows = [["指标", "数值"]] + [[metric["label"], metric["value"]] for metric in report["metrics"]]
        rows += [["主要攻击类型", self._format_counts(report["type_counts"])]]
        rows += [["风险等级分布", self._format_counts(report["severity_counts"])]]
        rows += [["状态/处置分布", self._format_counts(report["status_counts"])]]
        return self._docx_plain_table(rows, header=True)

    def _docx_list(self, items: List[str]) -> str:
        return "".join(self._docx_paragraph(f"{index}. {item}") for index, item in enumerate(items, start=1))

    def _docx_table(self, columns: Iterable[tuple[str, str]], rows: List[Dict[str, Any]]) -> str:
        columns = list(columns)
        table_rows = [[label for label, _ in columns]]
        for row in rows:
            table_rows.append([self._cell_text(row.get(key, "")) for _, key in columns])
        if not rows:
            table_rows.append(["暂无可导出的明细数据"] + [""] * (len(columns) - 1))
        return self._docx_plain_table(table_rows, header=True)

    def _format_counts(self, counts: Dict[str, int]) -> str:
        if not counts:
            return "暂无数据"
        return "；".join(f"{key}: {value}" for key, value in counts.items())

    def _docx_plain_table(self, rows: List[List[str]], header: bool = False) -> str:
        table_xml = [
            "<w:tbl>",
            "<w:tblPr><w:tblBorders>"
            '<w:top w:val="single" w:sz="6" w:space="0" w:color="999999"/>'
            '<w:left w:val="single" w:sz="6" w:space="0" w:color="999999"/>'
            '<w:bottom w:val="single" w:sz="6" w:space="0" w:color="999999"/>'
            '<w:right w:val="single" w:sz="6" w:space="0" w:color="999999"/>'
            '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
            '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
            "</w:tblBorders></w:tblPr>",
        ]
        for row_index, row in enumerate(rows):
            table_xml.append("<w:tr>")
            for value in row:
                table_xml.append(self._docx_cell(value, bold=header and row_index == 0))
            table_xml.append("</w:tr>")
        table_xml.append("</w:tbl>")
        return "".join(table_xml)

    def _docx_cell(self, value: str, bold: bool = False, size: str = "22") -> str:
        bold_xml = "<w:b/>" if bold else ""
        text_parts = str(value).split("\n")
        runs = "".join(
            f'<w:r><w:rPr>{bold_xml}<w:color w:val="111827"/><w:sz w:val="{size}"/></w:rPr>'
            f"<w:t>{html.escape(part)}</w:t></w:r>"
            + ("<w:r><w:br/></w:r>" if index < len(text_parts) - 1 else "")
            for index, part in enumerate(text_parts)
        )
        return (
            "<w:tc><w:tcPr><w:tcMar>"
            '<w:top w:w="80" w:type="dxa"/><w:left w:w="80" w:type="dxa"/>'
            '<w:bottom w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/>'
            "</w:tcMar></w:tcPr>"
            f"<w:p>{runs}</w:p></w:tc>"
        )

    def _docx_content_types(self) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            "</Types>"
        )

    def _docx_relationships(self) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="word/document.xml"/>'
            "</Relationships>"
        )

    def _write_pdf(self, path: Path, report: Dict[str, Any]) -> None:
        stream_parts = []
        stream_parts.append(self._pdf_rect(0, 520, 842, 75, PALETTE["navy"]))
        stream_parts.append(self._pdf_text(report["title"], 40, 560, 22, PALETTE["white"]))
        stream_parts.append(self._pdf_text(f"导出人: {report['username']}    导出时间: {report['created_at']}", 40, 535, 10, PALETTE["white"]))
        stream_parts.append(self._pdf_text("风险态势仪表盘", 40, 495, 16, PALETTE["navy"]))

        card_x = [40, 238, 436, 634]
        for x, metric in zip(card_x, report["metrics"]):
            stream_parts.append(self._pdf_rect(x, 430, 168, 48, metric["color"]))
            stream_parts.append(self._pdf_text(metric["label"], x + 12, 460, 9, PALETTE["white"]))
            stream_parts.append(self._pdf_text(metric["value"], x + 12, 440, 18, PALETTE["white"]))

        stream_parts.append(self._pdf_text("攻击类型分布", 40, 398, 13, PALETTE["navy"]))
        stream_parts.extend(self._pdf_bar_chart(report["type_counts"], 40, 370, 250, [PALETTE["blue"], PALETTE["cyan"], PALETTE["purple"], PALETTE["orange"]]))
        stream_parts.append(self._pdf_text("风险等级饼图", 455, 398, 13, PALETTE["navy"]))
        stream_parts.extend(self._pdf_pie_chart(report["severity_counts"], 530, 342, 42, [PALETTE["red"], PALETTE["orange"], PALETTE["green"], PALETTE["slate"]]))

        stream_parts.append(self._pdf_text("重点发现", 40, 270, 12, PALETTE["navy"]))
        for index, finding in enumerate(report["findings"][:2]):
            stream_parts.append(self._pdf_text(f"{index + 1}. {self._truncate_for_pdf(finding, 70)}", 40, 250 - index * 16, 8, "111827"))
        stream_parts.append(self._pdf_text("处置建议", 455, 270, 12, PALETTE["navy"]))
        for index, recommendation in enumerate(report["recommendations"][:2]):
            stream_parts.append(self._pdf_text(f"{index + 1}. {self._truncate_for_pdf(recommendation, 52)}", 455, 250 - index * 16, 8, "111827"))

        stream_parts.append(self._pdf_text("事件明细", 40, 205, 13, PALETTE["navy"]))
        y = 177
        headers = [label for label, _ in report["columns"]]
        column_x = [48, 150, 300, 472, 675]
        column_limits = [12, 22, 22, 24, 14]
        stream_parts.append(self._pdf_rect(40, y - 5, 760, 22, PALETTE["navy"]))
        for x, header in zip(column_x, headers[:5]):
            stream_parts.append(self._pdf_text(header, x, y + 2, 9, PALETTE["white"]))
        y -= 26
        for row in report["rows"][:10]:
            severity = self._normalise_severity(row.get("severity") or row.get("risk_level"))
            fill = PALETTE["red"] if severity == "high" else PALETTE["orange"] if severity == "medium" else PALETTE["green"] if severity == "low" else PALETTE["gray"]
            stream_parts.append(self._pdf_rect(40, y - 4, 760, 20, PALETTE["gray"]))
            stream_parts.append(self._pdf_rect(46, y - 1, 82, 14, fill))
            values = [
                self._truncate_for_pdf(self._cell_text(row.get(key, "")), limit)
                for (_, key), limit in zip(report["columns"][:5], column_limits)
            ]
            for index, (x, value) in enumerate(zip(column_x, values)):
                color = PALETTE["white"] if index == 0 and fill != PALETTE["gray"] else "111827"
                stream_parts.append(self._pdf_text(value, x, y + 1, 8, color))
            y -= 22
        if not report["rows"]:
            stream_parts.append(self._pdf_text("暂无可导出的明细数据", 50, y, 10, PALETTE["slate"]))

        content = "\n".join(stream_parts).encode("ascii")

        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] "
            b"/Resources << /Font << /F1 4 0 R /F2 7 0 R >> >> /Contents 8 0 R >>",
            b"<< /Type /Font /Subtype /Type0 /BaseFont /STSong-Light /Encoding /UniGB-UCS2-H "
            b"/DescendantFonts [5 0 R] >>",
            b"<< /Type /Font /Subtype /CIDFontType0 /BaseFont /STSong-Light "
            b"/CIDSystemInfo << /Registry (Adobe) /Ordering (GB1) /Supplement 2 >> "
            b"/FontDescriptor 6 0 R >>",
            b"<< /Type /FontDescriptor /FontName /STSong-Light /Flags 6 "
            b"/FontBBox [0 -200 1000 900] /ItalicAngle 0 /Ascent 880 /Descent -120 "
            b"/CapHeight 700 /StemV 80 >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream",
        ]

        pdf = bytearray(b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n")
        offsets = [0]
        for number, obj in enumerate(objects, start=1):
            offsets.append(len(pdf))
            pdf.extend(f"{number} 0 obj\n".encode("ascii"))
            pdf.extend(obj)
            pdf.extend(b"\nendobj\n")
        xref_offset = len(pdf)
        pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        pdf.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode(
                "ascii"
            )
        )
        path.write_bytes(pdf)

    def _pdf_bar_chart(self, counts: Dict[str, int], x: int, y: int, width: int, colors: List[str]) -> List[str]:
        if not counts:
            return [self._pdf_text("暂无可视化数据", x, y, 9, PALETTE["slate"])]
        commands = []
        max_value = max(counts.values()) or 1
        for index, (label, value) in enumerate(counts.items()):
            row_y = y - index * 28
            bar_width = max(8, int(value / max_value * width))
            commands.append(self._pdf_text(self._truncate_for_pdf(label, 18), x, row_y + 6, 8, "111827"))
            commands.append(self._pdf_rect(x + 120, row_y, bar_width, 12, colors[index % len(colors)]))
            commands.append(self._pdf_text(str(value), x + 128 + bar_width, row_y + 2, 8, PALETTE["slate"]))
        return commands

    def _pdf_pie_chart(self, counts: Dict[str, int], cx: int, cy: int, radius: int, colors: List[str]) -> List[str]:
        if not counts:
            return [self._pdf_text("暂无可视化数据", cx - radius, cy, 8, PALETTE["slate"])]
        commands = []
        total = sum(counts.values()) or 1
        start_angle = -90.0
        legend_y = cy + radius - 4
        for index, (label, value) in enumerate(counts.items()):
            angle = value / total * 360.0
            end_angle = start_angle + angle
            commands.append(self._pdf_slice(cx, cy, radius, start_angle, end_angle, colors[index % len(colors)]))
            legend_color = colors[index % len(colors)]
            commands.append(self._pdf_rect(cx + radius + 24, legend_y - index * 18, 10, 10, legend_color))
            percent = round(value / total * 100)
            commands.append(self._pdf_text(f"{label}: {value} ({percent}%)", cx + radius + 40, legend_y - index * 18, 8, "111827"))
            start_angle = end_angle
        return commands

    def _pdf_slice(self, cx: int, cy: int, radius: int, start_angle: float, end_angle: float, color: str) -> str:
        r, g, b = self._hex_to_rgb(color)
        span = max(1.0, end_angle - start_angle)
        steps = max(4, int(span / 12))
        points = [(cx, cy)]
        for step in range(steps + 1):
            angle = math.radians(start_angle + span * step / steps)
            points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
        path = [f"{points[0][0]:.1f} {points[0][1]:.1f} m"]
        path.extend(f"{x:.1f} {y:.1f} l" for x, y in points[1:])
        path.append("f")
        return f"q {r:.4f} {g:.4f} {b:.4f} rg {' '.join(path)} Q"

    def _pdf_rect(self, x: int, y: int, width: int, height: int, color: str) -> str:
        r, g, b = self._hex_to_rgb(color)
        return f"q {r:.4f} {g:.4f} {b:.4f} rg {x} {y} {width} {height} re f Q"

    def _pdf_text(self, text: str, x: int, y: int, size: int, color: str) -> str:
        r, g, b = self._hex_to_rgb(color)
        commands = []
        cursor_x = float(x)
        for run, is_latin in self._split_pdf_runs(self._cell_text(text)):
            font = "F2" if is_latin else "F1"
            payload = self._pdf_literal(run) if is_latin else f"<{run.encode('utf-16-be').hex().upper()}>"
            commands.append(
                f"q {r:.4f} {g:.4f} {b:.4f} rg BT /{font} {size} Tf {cursor_x:.1f} {y} Td {payload} Tj ET Q"
            )
            cursor_x += self._estimate_pdf_width(run, size, is_latin)
        return "\n".join(commands)

    def _split_pdf_runs(self, text: str) -> List[tuple[str, bool]]:
        if not text:
            return [("", True)]
        runs: List[tuple[str, bool]] = []
        current = []
        current_is_latin = self._is_latin_pdf_char(text[0])
        for char in text:
            is_latin = self._is_latin_pdf_char(char)
            if is_latin != current_is_latin and current:
                runs.append(("".join(current), current_is_latin))
                current = []
                current_is_latin = is_latin
            current.append(char)
        if current:
            runs.append(("".join(current), current_is_latin))
        return runs

    def _is_latin_pdf_char(self, char: str) -> bool:
        return ord(char) < 128

    def _pdf_literal(self, text: str) -> str:
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        return f"({escaped})"

    def _estimate_pdf_width(self, text: str, size: int, is_latin: bool) -> float:
        factor = 0.52 if is_latin else 0.95
        return len(text) * size * factor

    def _truncate_for_pdf(self, text: str, limit: int) -> str:
        text = self._cell_text(text)
        width = 0
        result = []
        for char in text:
            width += 1 if ord(char) < 128 else 2
            if width > limit:
                return "".join(result) + "..."
            result.append(char)
        return text

    def _hex_to_rgb(self, color: str) -> tuple[float, float, float]:
        color = color.strip("#")
        return (
            int(color[0:2], 16) / 255,
            int(color[2:4], 16) / 255,
            int(color[4:6], 16) / 255,
        )
