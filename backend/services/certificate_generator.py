"""
Sertifikat generatsiyasi (TZ v2.6, 17-bo'lim).
- Kursni muvaffaqiyatli tugatgan o'quvchilar uchun IELTS / CEFR formatidagi professional PDF sertifikat
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
    course_type: str = "General English",
    level: str = "B2",
    certificate_id: str | None = None,
) -> bytes:
    """Yuqori sifatli PDF sertifikat baytlarini generatsiya qiladi."""
    buffer = io.BytesIO()

    if canvas is None or letter is None or landscape is None or colors is None:
        return b"%PDF-1.4 dummy certificate"

    if not certificate_id:
        certificate_id = f"CERT-{datetime.utcnow().strftime('%Y%m')}-{abs(hash(student_name)) % 10000:04d}"

    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)

    # 1. Tashqi quyuq ko'k (Navy) ramka
    c.setStrokeColor(colors.HexColor("#0f172a"))
    c.setLineWidth(10)
    c.rect(20, 20, width - 40, height - 40)

    # 2. Ichki oltin rangli (Gold) ramka
    c.setStrokeColor(colors.HexColor("#d97706"))
    c.setLineWidth(2.5)
    c.rect(32, 32, width - 64, height - 64)

    # Burchak bezaklari
    c.setFillColor(colors.HexColor("#d97706"))
    for x in [32, width - 32]:
        for y in [32, height - 32]:
            c.circle(x, y, 6, stroke=0, fill=1)

    # 3. Markaz nomi
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#2563eb"))
    c.drawCentredString(width / 2, height - 75, "ALPHA ENGLISH LANGUAGE CENTER")

    # 4. Asosiy Sarlavha
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawCentredString(width / 2, height - 120, "CERTIFICATE OF COMPLETION")

    # 5. Kichik sarlavha
    c.setFont("Helvetica", 13)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawCentredString(width / 2, height - 160, "This certificate is proudly awarded to")

    # 6. O'quvchining ismi
    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.drawCentredString(width / 2, height - 210, student_name)

    # Ism ostidagi chiziq
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.setLineWidth(1)
    c.line(width / 2 - 200, height - 225, width / 2 + 200, height - 225)

    # 7. Kurs va daraja tavsifi
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.HexColor("#334155"))
    line1 = f"for successfully completing the comprehensive {course_type} program"
    line2 = f"and demonstrating exceptional language proficiency at {level} CEFR / IELTS standard."
    c.drawCentredString(width / 2, height - 265, line1)
    c.drawCentredString(width / 2, height - 285, line2)

    # 8. Pastki panel: Sana va Sertifikat ID
    date_str = datetime.utcnow().strftime("%B %d, %Y")

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(60, 95, f"DATE: {date_str}")
    c.drawString(60, 80, f"VERIFICATION ID: {certificate_id}")

    # Imzolar
    c.setStrokeColor(colors.HexColor("#94a3b8"))
    c.setLineWidth(1)
    c.line(width - 240, 95, width - 60, 95)
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawCentredString(width - 150, 80, "Academic Director / Head Teacher")

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer.getvalue()
