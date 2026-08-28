"""
Sertifikat generatsiyasi (TZ v2.6, 17-bo'lim).
- Kursni muvaffaqiyatli tugatgan o'quvchilar uchun IELTS / CEFR formatidagi PDF sertifikat
"""
import io
from datetime import datetime

try:
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
except ImportError:
    canvas = None
    letter = None
    landscape = None
    colors = None


def generate_certificate_pdf(
    student_name: str,
    course_type: str,
    level: str,
    certificate_id: str,
) -> bytes:
    """PDF sertifikat baytlarini generatsiya qiladi."""
    buffer = io.BytesIO()

    if canvas is None or letter is None or landscape is None or colors is None:
        return b"%PDF-1.4 dummy certificate"

    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)

    # Frame & background
    c.setStrokeColor(colors.HexColor("#1e3a8a"))
    c.setLineWidth(6)
    c.rect(30, 30, width - 60, height - 60)

    c.setStrokeColor(colors.HexColor("#d97706"))
    c.setLineWidth(2)
    c.rect(40, 40, width - 80, height - 80)

    # Title
    c.setFont("Helvetica-Bold", 32)
    c.setFillColor(colors.HexColor("#1e3a8a"))
    c.drawCentredString(width / 2, height - 120, "CERTIFICATE OF COMPLETION")

    # Subtitle
    c.setFont("Helvetica", 14)
    c.setFillColor(colors.HexColor("#4b5563"))
    c.drawCentredString(width / 2, height - 160, "This is proudly presented to")

    # Student Name
    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(colors.HexColor("#111827"))
    c.drawCentredString(width / 2, height - 210, student_name)

    # Description
    c.setFont("Helvetica", 13)
    c.setFillColor(colors.HexColor("#374151"))
    cert_text = f"for successfully completing the {course_type} course at {level} level with excellence."
    c.drawCentredString(width / 2, height - 260, cert_text)

    # Date and Certificate ID
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.HexColor("#6b7280"))
    date_str = datetime.utcnow().strftime("%B %d, %Y")
    c.drawString(70, 80, f"Date: {date_str}")
    c.drawRightString(width - 70, 80, f"Certificate ID: {certificate_id}")

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer.getvalue()
