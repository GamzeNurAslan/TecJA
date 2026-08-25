from datetime import datetime
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = PROJECT_ROOT / "tecja-email-report-preview.pdf"

sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.api.routes import (  # noqa: E402
    get_ai_insights,
    get_journey_patterns,
    get_risk_summary,
    get_summary,
    get_ticket_categories,
)
from backend.app.report_email import build_report_pdf  # noqa: E402


report_data = {
    "generated_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
    "generated_by": "TecJA verification",
    "summary": get_summary(),
    "risk_summary": get_risk_summary(),
    "journey_patterns": get_journey_patterns(limit=5),
    "ai_insights": get_ai_insights(),
    "ticket_categories": get_ticket_categories(),
}

pdf_bytes = build_report_pdf(report_data)
OUTPUT_PATH.write_bytes(pdf_bytes)
print(f"PDF_PATH={OUTPUT_PATH}")
print(f"PDF_BYTES={len(pdf_bytes)}")
