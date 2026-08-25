from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr, parseaddr
from io import BytesIO
import os
from pathlib import Path
import re
import smtplib
import ssl

from backend.app.config import BASE_DIR


class ReportEmailError(Exception):
    """Base exception for report delivery failures."""


class ReportEmailConfigurationError(ReportEmailError):
    """Raised when SMTP settings are incomplete."""


class ReportEmailDeliveryError(ReportEmailError):
    """Raised when the SMTP server rejects the message."""


EMAIL_PATTERN = re.compile(
    r"^[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?"
    r"(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+$",
    re.IGNORECASE,
)


def _load_local_env() -> None:
    env_path = BASE_DIR / ".env"

    if not env_path.exists():
        return

    for raw_line in env_path.read_text(
        encoding="utf-8"
    ).splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key:
            os.environ.setdefault(key, value)


def normalize_email_address(value: str) -> str:
    address = parseaddr(value.strip())[1].strip().lower()

    if not address or not EMAIL_PATTERN.fullmatch(address):
        raise ValueError("Geçerli bir alıcı e-posta adresi girin.")

    return address


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


@dataclass(frozen=True)
class SmtpSettings:
    host: str
    port: int
    username: str
    password: str
    from_email: str
    from_name: str
    use_tls: bool
    use_ssl: bool


def get_smtp_settings() -> SmtpSettings:
    _load_local_env()

    host = os.getenv("TECJA_SMTP_HOST", "").strip()
    username = os.getenv("TECJA_SMTP_USERNAME", "").strip()
    password = os.getenv("TECJA_SMTP_PASSWORD", "").strip()
    from_email = os.getenv(
        "TECJA_SMTP_FROM_EMAIL",
        username,
    ).strip()
    from_name = os.getenv(
        "TECJA_SMTP_FROM_NAME",
        "TecJA Analytics",
    ).strip()

    try:
        port = int(os.getenv("TECJA_SMTP_PORT", "587"))
    except ValueError as exc:
        raise ReportEmailConfigurationError(
            "TECJA_SMTP_PORT sayısal olmalıdır."
        ) from exc

    if not host or not from_email:
        raise ReportEmailConfigurationError(
            "E-posta gönderimi yapılandırılmamış. Proje kökündeki "
            ".env dosyasına TECJA_SMTP_HOST ve "
            "TECJA_SMTP_FROM_EMAIL değerlerini ekleyin."
        )

    try:
        normalized_from_email = normalize_email_address(
            from_email
        )
    except ValueError as exc:
        raise ReportEmailConfigurationError(
            "TECJA_SMTP_FROM_EMAIL geçerli bir e-posta "
            "adresi olmalıdır."
        ) from exc

    return SmtpSettings(
        host=host,
        port=port,
        username=username,
        password=password,
        from_email=normalized_from_email,
        from_name=from_name or "TecJA Analytics",
        use_tls=_env_flag("TECJA_SMTP_USE_TLS", True),
        use_ssl=_env_flag("TECJA_SMTP_USE_SSL", False),
    )


def _format_number(value) -> str:
    try:
        return f"{int(float(value)):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(value or "0")


def _register_fonts():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    candidates = [
        (
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf"),
        ),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
    ]

    for regular_path, bold_path in candidates:
        if regular_path.exists() and bold_path.exists():
            pdfmetrics.registerFont(
                TTFont("TecJA-Regular", str(regular_path))
            )
            pdfmetrics.registerFont(
                TTFont("TecJA-Bold", str(bold_path))
            )
            return "TecJA-Regular", "TecJA-Bold"

    return "Helvetica", "Helvetica-Bold"


def build_report_pdf(report_data: dict) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            KeepTogether,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError as exc:
        raise ReportEmailConfigurationError(
            "PDF motoru kurulu değil. 'pip install reportlab' "
            "komutunu çalıştırın."
        ) from exc

    regular_font, bold_font = _register_fonts()
    navy = colors.HexColor("#0A2947")
    panel = colors.HexColor("#F3F6FA")
    border = colors.HexColor("#D5DFEA")
    cream = colors.HexColor("#F3E4C9")
    coral = colors.HexColor("#FF7755")
    teal = colors.HexColor("#2CBFAE")
    muted = colors.HexColor("#5D7187")

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=15 * mm,
        bottomMargin=13 * mm,
        title="TecJA Customer Journey Intelligence Report",
        author="TecJA Analytics",
    )

    base_styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TecJATitle",
        parent=base_styles["Title"],
        fontName=bold_font,
        fontSize=21,
        leading=24,
        textColor=navy,
        alignment=TA_LEFT,
        spaceAfter=3 * mm,
    )
    subtitle_style = ParagraphStyle(
        "TecJASubtitle",
        parent=base_styles["Normal"],
        fontName=regular_font,
        fontSize=9,
        leading=11,
        textColor=muted,
        spaceAfter=3 * mm,
    )
    section_style = ParagraphStyle(
        "TecJASection",
        parent=base_styles["Heading2"],
        fontName=bold_font,
        fontSize=12,
        leading=14,
        textColor=navy,
        spaceBefore=2 * mm,
        spaceAfter=2 * mm,
    )
    cell_style = ParagraphStyle(
        "TecJACell",
        parent=base_styles["Normal"],
        fontName=regular_font,
        fontSize=7.8,
        leading=9.5,
        textColor=navy,
    )
    cell_bold_style = ParagraphStyle(
        "TecJACellBold",
        parent=cell_style,
        fontName=bold_font,
    )
    center_style = ParagraphStyle(
        "TecJACenter",
        parent=cell_bold_style,
        alignment=TA_CENTER,
    )
    header_style = ParagraphStyle(
        "TecJAHeader",
        parent=cell_bold_style,
        textColor=cream,
    )
    header_center_style = ParagraphStyle(
        "TecJAHeaderCenter",
        parent=header_style,
        alignment=TA_CENTER,
    )

    def paragraph(value, style=cell_style):
        text = str(value if value is not None else "-")
        text = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        return Paragraph(text, style)

    def styled_table(data, widths=None, header=True):
        table = Table(data, colWidths=widths, repeatRows=1 if header else 0)
        commands = [
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 0.6, border),
            ("INNERGRID", (0, 0), (-1, -1), 0.35, border),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("BACKGROUND", (0, 1 if header else 0), (-1, -1), panel),
        ]
        if header:
            commands.extend(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), navy),
                    ("TEXTCOLOR", (0, 0), (-1, 0), cream),
                ]
            )
        table.setStyle(TableStyle(commands))
        return table

    summary = report_data.get("summary", {})
    risks = report_data.get("risk_summary", {}).get("items", [])
    patterns = report_data.get("journey_patterns", {}).get("items", [])
    ai_data = report_data.get("ai_insights", {})
    categories = report_data.get("ticket_categories", {}).get("items", [])
    generated_at = report_data.get("generated_at") or datetime.now().isoformat()
    generated_by = report_data.get("generated_by", "TecJA user")

    story = [
        Paragraph("TecJA Customer Journey Intelligence", title_style),
        Paragraph(
            f"Canlı analitik raporu | Oluşturan: {generated_by} | {generated_at}",
            subtitle_style,
        ),
    ]

    kpis = [
        [
            paragraph("Toplam Müşteri", header_center_style),
            paragraph("Journey Olayı", header_center_style),
            paragraph("Yüksek Risk", header_center_style),
            paragraph("Destek Talebi", header_center_style),
        ],
        [
            paragraph(_format_number(summary.get("total_customers")), center_style),
            paragraph(_format_number(summary.get("total_journey_events")), center_style),
            paragraph(_format_number(summary.get("high_risk_customers")), center_style),
            paragraph(_format_number(summary.get("total_tickets")), center_style),
        ],
    ]
    kpi_table = styled_table(kpis, [44 * mm] * 4, header=True)
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 1), (-1, 1), panel),
                ("TEXTCOLOR", (0, 1), (-1, 1), navy),
                ("FONTSIZE", (0, 1), (-1, 1), 14),
            ]
        )
    )
    story.extend([kpi_table, Spacer(1, 2 * mm)])

    story.append(Paragraph("Risk Dağılımı", section_style))
    risk_rows = [
        [
            paragraph("Risk seviyesi", header_style),
            paragraph("Müşteri", header_style),
            paragraph("Churn", header_style),
            paragraph("Ortalama skor", header_style),
        ]
    ]
    for item in risks:
        risk_rows.append(
            [
                paragraph(item.get("risk_level")),
                paragraph(_format_number(item.get("customer_count"))),
                paragraph(_format_number(item.get("churned_customers"))),
                paragraph(item.get("average_risk_score")),
            ]
        )
    story.extend(
        [
            styled_table(risk_rows, [55 * mm, 40 * mm, 40 * mm, 43 * mm]),
            Spacer(1, 1.5 * mm),
        ]
    )

    pattern_rows = [
        [
            paragraph("En sık müşteri yolculukları", header_style),
            paragraph("Müşteri", header_style),
        ]
    ]
    for item in patterns[:5]:
        pattern_rows.append(
            [
                paragraph(item.get("journey_pattern")),
                paragraph(_format_number(item.get("customer_count"))),
            ]
        )

    story.append(
        KeepTogether(
            [
                Paragraph("Journey Pattern Analizi", section_style),
                styled_table(pattern_rows, [140 * mm, 38 * mm]),
            ]
        )
    )

    story.append(Paragraph("AI Ticket Analizi", section_style))
    ai_rows = [
        [
            paragraph("Tespit edilen sorun", header_style),
            paragraph("Etki", header_style),
            paragraph("Güven", header_style),
            paragraph("Ticket payı", header_style),
        ],
        [
            paragraph(ai_data.get("detected_issue")),
            paragraph(ai_data.get("impact")),
            paragraph(f"%{ai_data.get('confidence_percent', 0)}"),
            paragraph(f"%{ai_data.get('ticket_share_percent', 0)}"),
        ],
    ]
    story.extend(
        [
            styled_table(ai_rows, [70 * mm, 34 * mm, 34 * mm, 40 * mm]),
            Spacer(1, 1 * mm),
            Table(
                [[paragraph("Önerilen aksiyon", cell_bold_style), paragraph(ai_data.get("recommended_action"))]],
                colWidths=[40 * mm, 138 * mm],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E9F8F5")),
                        ("BOX", (0, 0), (-1, -1), 0.7, teal),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 7),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                ),
            ),
        ]
    )

    category_rows = [
        [
            paragraph("Ticket kategorisi", header_style),
            paragraph("Adet", header_style),
            paragraph("Ortalama güven", header_style),
        ]
    ]
    for item in categories:
        category_rows.append(
            [
                paragraph(item.get("category")),
                paragraph(_format_number(item.get("ticket_count"))),
                paragraph(f"%{round(float(item.get('average_confidence') or 0) * 100)}"),
            ]
        )
    story.append(Paragraph("Ticket Kategorileri", section_style))
    story.append(
        styled_table(category_rows, [100 * mm, 38 * mm, 40 * mm])
    )

    def draw_page(canvas, doc):
        canvas.saveState()
        width, height = A4
        canvas.setStrokeColor(coral)
        canvas.setLineWidth(2)
        canvas.line(16 * mm, height - 11 * mm, width - 16 * mm, height - 11 * mm)
        canvas.setFont(regular_font, 7.5)
        canvas.setFillColor(muted)
        canvas.drawString(16 * mm, 9 * mm, "TecJA Analytics - Gizli ve kurumsal kullanım içindir")
        canvas.drawRightString(width - 16 * mm, 9 * mm, f"Sayfa {doc.page}")
        canvas.restoreState()

    document.build(
        story,
        onFirstPage=draw_page,
        onLaterPages=draw_page,
    )
    return buffer.getvalue()


def send_report_email(
    recipient: str,
    pdf_bytes: bytes,
    *,
    subject: str = "TecJA Customer Journey Intelligence Report",
) -> None:
    settings = get_smtp_settings()
    recipient = normalize_email_address(recipient)

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr(
        (settings.from_name, settings.from_email)
    )
    message["To"] = recipient
    message.set_content(
        "Merhaba,\n\n"
        "TecJA Customer Journey Intelligence raporu PDF olarak "
        "bu e-postaya eklenmiştir.\n\n"
        "TecJA Analytics"
    )
    message.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=(
            "tecja-customer-journey-report-"
            f"{datetime.now().strftime('%Y%m%d-%H%M')}.pdf"
        ),
    )

    context = ssl.create_default_context()

    try:
        if settings.use_ssl:
            with smtplib.SMTP_SSL(
                settings.host,
                settings.port,
                timeout=20,
                context=context,
            ) as server:
                if settings.username:
                    server.login(
                        settings.username,
                        settings.password,
                    )
                server.send_message(message)
        else:
            with smtplib.SMTP(
                settings.host,
                settings.port,
                timeout=20,
            ) as server:
                server.ehlo()
                if settings.use_tls:
                    server.starttls(context=context)
                    server.ehlo()
                if settings.username:
                    server.login(
                        settings.username,
                        settings.password,
                    )
                server.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        raise ReportEmailDeliveryError(
            "E-posta SMTP sunucusuna gönderilemedi. Sunucu, port ve "
            "uygulama parolası ayarlarını kontrol edin."
        ) from exc
