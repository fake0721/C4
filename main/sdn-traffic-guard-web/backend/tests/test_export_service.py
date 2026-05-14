import tempfile
import unittest
import zipfile
from pathlib import Path

from backend.export_service import ExportService


class ExportServiceTest(unittest.TestCase):
    def test_creates_docx_export_with_task_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ExportService(output_dir=tmpdir)

            result = service.create_export(
                export_type="anomalies",
                export_format="docx",
                filters={"hours": 24},
                username="admin",
                payload={
                    "items": [
                        {
                            "src_ip": "192.168.1.10",
                            "type": "SYN Flood",
                            "severity": "high",
                            "detect_time": "2026-05-12 10:30:00",
                            "status": "pending",
                        }
                    ]
                },
            )

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["format"], "docx")
            self.assertEqual(result["export_type"], "anomalies")
            self.assertTrue(Path(result["file_path"]).exists())
            self.assertGreater(Path(result["file_path"]).stat().st_size, 0)

    def test_rejects_unknown_export_format(self):
        service = ExportService(output_dir=tempfile.mkdtemp())

        with self.assertRaises(ValueError) as context:
            service.create_export(
                export_type="anomalies",
                export_format="xlsx",
                filters={},
                username="admin",
                payload={"items": []},
            )

        self.assertIn("不支持的导出格式", str(context.exception))

    def test_docx_export_uses_plain_text_and_readable_tables(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ExportService(output_dir=tmpdir)

            result = service.create_export(
                export_type="anomalies",
                export_format="docx",
                filters={"hours": 24},
                username="admin",
                payload={
                    "items": [
                        {"src_ip": "10.0.0.1", "type": "SYN Flood", "severity": "high", "status": "pending"},
                        {"src_ip": "10.0.0.2", "type": "UDP Flood", "severity": "medium", "status": "handled"},
                    ]
                },
            )

            with zipfile.ZipFile(result["file_path"]) as archive:
                document_xml = archive.read("word/document.xml").decode("utf-8")

            self.assertIn("统计摘要", document_xml)
            self.assertIn("事件明细", document_xml)
            self.assertIn("w:tblBorders", document_xml)
            self.assertNotIn("风险态势仪表盘", document_xml)
            self.assertNotIn("w:shd", document_xml)

    def test_pdf_export_uses_latin_font_and_landscape_layout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ExportService(output_dir=tmpdir)

            result = service.create_export(
                export_type="anomalies",
                export_format="pdf",
                filters={"hours": 24},
                username="admin",
                payload={
                    "items": [
                        {"src_ip": "10.0.0.1", "type": "SYN Flood", "severity": "high", "status": "pending"},
                        {"src_ip": "10.0.0.2", "type": "UDP Flood", "severity": "medium", "status": "handled"},
                    ]
                },
            )

            pdf_bytes = Path(result["file_path"]).read_bytes()

            self.assertIn(b"/MediaBox [0 0 842 595]", pdf_bytes)
            self.assertIn(b"/Helvetica", pdf_bytes)
            self.assertIn(b"/F2", pdf_bytes)
            self.assertIn(b" rg", pdf_bytes)
            self.assertIn(b" re f", pdf_bytes)
            self.assertIn("风险态势仪表盘".encode("utf-16-be").hex().upper().encode("ascii"), pdf_bytes)

    def test_exports_include_findings_recommendations_and_pdf_pie_chart(self):
        payload = {
            "items": [
                {"src_ip": "10.0.0.1", "type": "SYN Flood", "severity": "high", "status": "pending"},
                {"src_ip": "10.0.0.2", "type": "UDP Flood", "severity": "medium", "status": "handled"},
                {"src_ip": "10.0.0.3", "type": "ARP 欺骗", "severity": "low", "status": "handled"},
            ]
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ExportService(output_dir=tmpdir)
            docx_result = service.create_export("anomalies", "docx", {"hours": 24}, "admin", payload)
            pdf_result = service.create_export("anomalies", "pdf", {"hours": 24}, "admin", payload)

            with zipfile.ZipFile(docx_result["file_path"]) as archive:
                document_xml = archive.read("word/document.xml").decode("utf-8")
            pdf_bytes = Path(pdf_result["file_path"]).read_bytes()

            self.assertIn("重点发现", document_xml)
            self.assertIn("处置建议", document_xml)
            self.assertIn("风险等级饼图".encode("utf-16-be").hex().upper().encode("ascii"), pdf_bytes)
            self.assertIn(b" m ", pdf_bytes)
            self.assertIn(b" l ", pdf_bytes)


if __name__ == "__main__":
    unittest.main()
