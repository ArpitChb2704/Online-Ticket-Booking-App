
import random
from datetime import datetime
from supabase import create_client
import os
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, request, session, jsonify, send_file

load_dotenv()
# Supabase client (already configured in your app)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

MUSEUMS = [
    "Bada Imambara",
    "Taj Mahal",
    "Chota Imambara",
    "Hawa Mahal",
    "Amer Fort",
    "Jaigarh Fort"
]

GUIDELINES = """
1. Carry a valid ID proof.
2. Tickets once booked cannot be refunded.
3. Follow COVID protocols at the premises.
4. Entry allowed only during booked slot.
5. Children below 12 must be accompanied by adults.
"""

# Store sessions in memory (use DB/Redis if scaling)
user_sessions = {}

def get_chatbot_response(user_id, user_message):
    session = user_sessions.get(user_id, {"step": "start", "ticket_data": {}})
    step = session["step"]

    # --- Start ---
    if step == "start":
        if user_message.lower() in ["hi", "hello"]:
            session["step"] = "menu"
            user_sessions[user_id] = session
            return "Welcome to Online Ticket Booking System.\n1. Book Ticket\n2. Guidelines\nType option to continue."
        else:
            return "Type 'hi' to start the booking process."

    # --- Menu ---
    if step == "menu":
        if user_message.strip() == "1":
            session["step"] = "name"
            user_sessions[user_id] = session
            return "Please enter your name:"
        elif user_message.strip() == "2":
            session["step"] = "start"
            user_sessions[user_id] = session
            return f"Guidelines:\n{GUIDELINES}\n\nType 'hi' to return to main menu."
        else:
            return "Invalid option. Type 1 for Book Ticket or 2 for Guidelines."

    # --- Name ---
    if step == "name":
        session["ticket_data"]["name"] = user_message.strip()
        session["step"] = "age"
        user_sessions[user_id] = session
        return "Enter your age (must be >= 18):"

    # --- Age ---
    if step == "age":
        try:
            age = int(user_message.strip())
            if age < 18:
                session["step"] = "start"
                user_sessions[user_id] = session
                return "Sorry, you must be 18 or older to book tickets. Type 'hi' to start again."
            session["ticket_data"]["age"] = age
            session["step"] = "email"
            user_sessions[user_id] = session
            return "Enter your email:"
        except:
            return "Please enter a valid number for age."

    # --- Email ---
    if step == "email":
        if "@" not in user_message:
            return "Please enter a valid email address."
        session["ticket_data"]["email"] = user_message.strip()
        session["step"] = "museum"
        user_sessions[user_id] = session
        return "Select a museum:\n" + "\n".join([f"{i+1}. {m}" for i, m in enumerate(MUSEUMS)])

    # --- Museum ---
    if step == "museum":
        try:
            idx = int(user_message.strip()) - 1
            if idx < 0 or idx >= len(MUSEUMS):
                return "Invalid selection. Choose a valid number."
            session["ticket_data"]["museum_name"] = MUSEUMS[idx]
            session["step"] = "date"
            user_sessions[user_id] = session
            return "Enter visit date (DD/MM/YYYY):"
        except:
            return "Enter a valid number for museum choice."

    # --- Date ---
    if step == "date":
        try:
            visit_date = datetime.strptime(user_message.strip(), "%d/%m/%Y").date()
            session["ticket_data"]["museum_visit_date"] = str(visit_date)
            session["step"] = "time"
            user_sessions[user_id] = session
            return "Enter visit time (e.g., 10:30 AM):"
        except:
            return "Invalid date format. Please enter in DD/MM/YYYY format."

    # --- Time ---
    if step == "time":
        session["ticket_data"]["museum_visit_time"] = user_message.strip()
        session["step"] = "confirm"
        user_sessions[user_id] = session
        d = session["ticket_data"]
        return (f"Please confirm your booking details:\n"
                f"Name: {d['name']}\n"
                f"Age: {d['age']}\n"
                f"Email: {d['email']}\n"
                f"Museum: {d['museum_name']}\n"
                f"Date: {d['museum_visit_date']}\n"
                f"Time: {d['museum_visit_time']}\n\n"
                "Type 'confirm' to proceed or 'cancel' to abort.")

    # --- Confirm ---
    if step == "confirm":
        if user_message.lower() == "confirm":
            d = session["ticket_data"]
            ticket_data = {
                "name": d["name"],
                "age": d["age"],
                "email": d["email"],
                "museum_name": d["museum_name"],
                "museum_visit_date": d["museum_visit_date"],
                "museum_visit_time": d["museum_visit_time"],
                "user_id": None,
                "ticket_id": random.randint(100, 999999),
                "payment_status": "pending",
            }

            response = supabase.table("tickets").insert(ticket_data).execute()
            ticket_i = None
            if response.data and len(response.data) > 0:
                ticket_i = response.data[0]['ticket_id']

            # reset session
            user_sessions[user_id] = {"step": "start", "ticket_data": {}}

            return {
                "type": "redirect",
                "url": f"/payment/{ticket_i}"
            }
        elif user_message.lower() == "cancel":
            user_sessions[user_id] = {"step": "start", "ticket_data": {}}
            return "Booking cancelled. Type 'hi' to start again."
        else:
            return "Please type 'confirm' or 'cancel'."

    return "Something went wrong. Type 'hi' to restart."