import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import uuid

def generate_ticket_pdf(name, email, tickets):
    ticket_id = str(uuid.uuid4())[:8]
    qr_img = qrcode.make(f"TICKET-{ticket_id}")
    qr_path = f"qr_{ticket_id}.png"
    qr_img.save(qr_path)

    pdf_file = f"ticket_{ticket_id}.pdf"
    c = canvas.Canvas(pdf_file, pagesize=A4)
    c.drawString(100, 750, f"Ticket ID: {ticket_id}")
    c.drawString(100, 730, f"Name: {name}")
    c.drawString(100, 710, f"Email: {email}")
    c.drawString(100, 690, f"No. of Tickets: {tickets}")
    c.drawImage(qr_path, 100, 600, width=120, height=120)
    c.save()
    return pdf_file
