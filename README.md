# Online-Ticket-Booking-App

An AI-powered chatbot-based ticket booking system designed for museums, cultural institutions, and events. The app provides a conversational interface for users to seamlessly book tickets, make secure payments, and download their e-tickets.

## ✨ Features

💬 Chatbot Integration – Conversational flow for booking tickets.

🗂 User Data Capture – Collects name, email, and ticket details.

💳 Payment Gateway – Secure Stripe integration for online payments.

🪑 Ticket Management – View, book, and manage tickets dynamically.

📊 Database Support – Uses MySQL or Supabase for storing booking records.

📄 Ticket Confirmation – Generates booking confirmation after successful payment.

## 🛠 Tech Stack

Frontend: HTML, CSS, Streamlit (for chatbot UI)

Backend: Flask / Streamlit

Database: MySQL / Supabase

Payment Gateway: Stripe API

Deployment: Localhost / Cloud (optional)

## 🚀 Getting Started

1. Clone the Repository
git clone https://github.com/ArpitChb2704/Online-Ticket-Booking-App.git
cd Online-Ticket-Booking-App

3. Set Up Virtual Environment
python -m venv venv
source venv/bin/activate   # For Mac/Linux
venv\Scripts\activate      # For Windows

5. Install Dependencies
pip install -r requirements.txt

7. Configure Database
Update app.py with your MySQL or Supabase credentials.
Example MySQL URI:
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/chatbot_db'

9. Stripe Configuration
Create a Stripe account (https://stripe.com).
Add your Publishable Key and Secret Key in the .env file:

STRIPE_PUBLIC_KEY=your_public_key
STRIPE_SECRET_KEY=your_secret_key

10. Run the Application
streamlit run app.py

## Project Idea

I have the Project idea from : https://github.com/Hemanth0192/Online-Chatbot-Based-Ticketing-System

## 📖 Usage

Open the app in your browser.
Chat with the bot to book tickets.
Enter your details (name, email, tickets).
Complete payment via Stripe checkout.
Receive confirmation and download your ticket.

## 📂 Project Structure
Online-Ticket-Booking-App/
│── app.py                # Main application file
│── requirements.txt      # Dependencies
│── templates/            # HTML templates
│── static/               # CSS, JS, assets
│── utils/                # Helper functions
│── tasks/                # Background tasks
└── README.md             # Project documentation

## 🤝 Contributing

Contributions are welcome!

Fork the repository

Create a new branch (feature/your-feature)

Commit changes and open a PR

## 📜 License

This project is licensed under the MIT License.
