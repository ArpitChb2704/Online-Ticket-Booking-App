import os
import uuid
from io import BytesIO
from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, url_for, request, session, jsonify, send_file
from flask_babel import Babel
import stripe
from flask_cors import CORS
from models import db  
from chatbot import get_chatbot_response
import qrcode
from supabase import create_client, Client
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
#from apscheduler.schedulers.background import BackgroundScheduler
from supabase import create_client
import random
import io
from dotenv import load_dotenv
load_dotenv()
# -------------------------------
# 🔑 Environment variables
# -------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "your_stripe_public_key")
STRIPE_SECRET_KEY = os.getenv(
    "STRIPE_SECRET_KEY"
)

FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "your_secret_key")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# -------------------------------
# Initialize Flask app
# -------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
app.config['STRIPE_PUBLIC_KEY'] = STRIPE_PUBLIC_KEY
app.config['STRIPE_SECRET_KEY'] = STRIPE_SECRET_KEY
app.config['BABEL_DEFAULT_LOCALE'] = 'en'

# Initialize extensions
babel = Babel(app)
CORS(app)
stripe.api_key = STRIPE_SECRET_KEY

# Optional Supabase client for direct queries
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------
# Locale
# -------------------------------
def get_locale():
    return session.get('locale', 'en')

babel.init_app(app, locale_selector=get_locale)

@app.context_processor
def inject_get_locale():
    return dict(get_locale=get_locale)

@app.route('/set_locale/<locale>')
def set_locale(locale):
    session['locale'] = locale
    return redirect(request.referrer)

@app.route('/test_locale')
def test_locale():
    return f"Current locale: {get_locale()}"

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/view')
def view():
    return render_template('view.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        # You can save to Supabase or send email here
        return "Thank you for your message!"
    return render_template('contact.html')

# -------------------------------
# Ticket Booking
# -------------------------------
@app.route('/book_ticket', methods=['GET', 'POST'])
def book_ticket():
    from models import Ticket
    if request.method == 'POST':
        age = int(request.form['age'])
        if age < 18:
            return "You must be 18 or older to book a ticket."

        visit_date = datetime.strptime(request.form['museum_visit_date'], '%Y-%m-%d').date()

        ticket_data = {
            "name": request.form['name'],
            "age": age,
            "email": request.form['email'],
            "museum_name": request.form['museum_name'],
            "museum_visit_date": str(visit_date),
            "museum_visit_time": request.form['museum_visit_time'],
            "user_id": None,
            "ticket_id": random.randint(100, 999999),
            "payment_status": 'pending',
        }
        response = supabase.table("tickets").insert(ticket_data).execute()
    
        # Extract the id
        if response.data and len(response.data) > 0:
            ticket_i= response.data[0]['ticket_id']
  
        return redirect(url_for('payment', ticket_id=ticket_i))
    return render_template('book_ticket.html')

@app.route('/my_tickets')
def my_tickets():
    from models import Ticket
    user_id = session['user_id']
    tickets = Ticket.query.filter_by(user_id=user_id).all()
    return render_template('my_tickets.html', tickets=tickets)

@app.route('/delete_ticket/<int:ticket_id>', methods=['POST'])
def delete_ticket(ticket_id):
    from models import Ticket
    Ticket.query.filter_by(id=ticket_id).delete()
    db.session.commit()
    return redirect(url_for('my_tickets'))

# -------------------------------
# Payment
# -------------------------------
@app.route('/payment/<int:ticket_id>', methods=['GET'])
def payment(ticket_id):
   # Fetch ticket details from DB using ticket_id
    ticket = supabase.table("tickets").select("*").eq("ticket_id", ticket_id).execute()

    if not ticket.data:
        return "Ticket not found", 404

    ticket = ticket.data[0]   # full dictionary

    return render_template("payment.html", ticket=ticket)
    

    
@app.route('/confirm_payment/<int:ticket_id>', methods=['POST'])
def confirm_payment(ticket_id):
    from models import Ticket
    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.ticket_code = 'MUS-' + str(uuid.uuid4().hex[:8]).upper()
    ticket.payment_status = True
    db.session.commit()
    return render_template('payment_success.html', ticket=ticket)


# -------------------------------
# Stripe Payment
# -------------------------------


@app.route('/create-checkout-session/<int:ticket_id>', methods=['POST'])
def create_checkout_session(ticket_id):
    # fetch ticket details
    ticket = supabase.table("tickets").select("*").eq("ticket_id", ticket_id).execute()
    if not ticket.data:
        return "Ticket not found", 404

    ticket = ticket.data[0]

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'inr',
                    'product_data': {
                        'name': f"Museum Ticket - {ticket['museum_name']}",
                    },
                    'unit_amount': 20000,  # ₹200 in paise
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('payment_success', ticket_id=ticket_id, _external=True),
            cancel_url=url_for('payment_cancel', ticket_id=ticket_id, _external=True),
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return str(e), 400

@app.route('/payment-success/<int:ticket_id>')
def payment_success(ticket_id):
    response = supabase.table("tickets").select("*").eq("ticket_id", ticket_id).execute()
    if not response.data:
        return "Ticket not found", 404

    ticket = response.data[0]
    return render_template("payment_success.html", ticket=ticket)

@app.route('/download_ticket/<ticket_id>')
def download_ticket(ticket_id):
    # Fetch ticket details
    ticket = supabase.table("tickets").select("*").eq("ticket_id", ticket_id).single().execute()
    
    if not ticket.data:
        return "Ticket not found", 404
    
    ticket = ticket.data
    
    # Generate PDF in memory
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 800, "🎟️ Museum Ticket")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, 750, f"Ticket ID: {ticket['ticket_id']}")
    p.drawString(100, 730, f"Name: {ticket['name']}")
    p.drawString(100, 710, f"Email: {ticket['email']}")
    p.drawString(100, 690, f"Age: {ticket['age']}")
    p.drawString(100, 670, f"Museum: {ticket['museum_name']}")
    p.drawString(100, 650, f"Visit Date: {ticket['museum_visit_date']}")
    p.drawString(100, 630, f"Visit Time: {ticket['museum_visit_time']}")
    p.drawString(100, 610, f"Payment Status: {'Paid' if ticket['payment_status'] else 'Pending'}")
    p.drawString(100, 590, f"Transaction ID: {ticket['ticket_id']}")
    
    p.line(100, 580, 500, 580)
    p.drawString(200, 560, "✅ Enjoy your visit!")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name="ticket.pdf", mimetype="application/pdf")

@app.route('/payment-cancel/<int:ticket_id>')
def payment_cancel(ticket_id):
    return f"Payment cancelled for ticket {ticket_id}."


# -------------------------------
# QR Code
# -------------------------------
@app.route('/ticket_qr/<int:ticket_id>')
def ticket_qr(ticket_id):
    from models import Ticket
    ticket = Ticket.query.get_or_404(ticket_id)
    qr_data = f"ID: {ticket.id}\nName: {ticket.name}\nMuseum: {ticket.museum_name}\nDate: {ticket.museum_visit_date.strftime('%d-%m-%Y')}\nTime: {ticket.museum_visit_time}\nCode: {ticket.ticket_code}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


# -------------------------------
# Chatbot
# -------------------------------
@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if request.method == 'POST':
        data = request.get_json()
        user_message = data.get('message')
        user_id = request.remote_addr
        bot_response = get_chatbot_response(user_id, user_message)

        # if bot_response is dict (redirect case), return as-is
        if isinstance(bot_response, dict):
            return jsonify(bot_response)

        # otherwise normal text
        return jsonify({"response": bot_response})

    return render_template('chatbot.html')

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()



# -------------------------------
# PDF Ticket Generation
# -------------------------------
def generate_ticket_pdf(name, museum, date, time, filename=None):
    ticket_id = str(uuid.uuid4())[:8]
    qr = qrcode.make(f'TicketID: {ticket_id} | Name: {name} | Museum: {museum} | Date: {date} | Time: {time}')
    qr_path = 'static/qr_temp.png'
    qr.save(qr_path)

    if not filename:
        filename = f'static/ticket_{ticket_id}.pdf'

    c = canvas.Canvas(filename, pagesize=A4)
    c.setFont("Helvetica", 16)
    c.drawString(100, 780, f"e-Ticket for {museum}")
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, f"Name: {name}")
    c.drawString(100, 730, f"Date: {date}")
    c.drawString(100, 710, f"Time: {time}")
    c.drawString(100, 690, f"Ticket ID: {ticket_id}")
    c.drawImage(qr_path, 100, 550, width=150, height=150)
    c.save()

    os.remove(qr_path)
    return filename

# -------------------------------
# Run App
# -------------------------------
if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)
