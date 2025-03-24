import sqlite3

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import pandas as pd
import os
import matplotlib.pyplot as plt
import io
from database import initialize_database, DB_PATH

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "supersecretkey"

# Load CSV Data
CSV_PATH = os.path.join(os.getcwd(), "dataset", "sustainability_data.csv")

def load_data():
    data = pd.read_csv(CSV_PATH)
    data["Non_Renewable_Energy_Percentage"] = 100 - data["Renewable_Energy_Percentage"]
    return data

@app.route('/')
def index():

    return render_template("index.html")

@app.route('/display_headers_only')
def display_headers():
    data = load_data().head(10).to_dict(orient="records")
    return jsonify(data)

# ================= Visualization Routes ==================

def save_plot(fig):
    img = io.BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    return img

@app.route('/plot_energy_comparison')
def plot_energy_comparison():
    data = load_data()
    fig, ax = plt.subplots()
    ax.bar(data["Department"], data["Renewable_Energy_Percentage"], color='green', label="Renewable")
    ax.bar(data["Department"], data["Non_Renewable_Energy_Percentage"],
           bottom=data["Renewable_Energy_Percentage"], color='gray', label="Non-Renewable")
    ax.set_title("Renewable vs Non-Renewable Energy Usage")
    ax.set_ylabel("Energy Usage (%)")
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    return send_file(save_plot(fig), mimetype='image/png')

@app.route('/plot_energy_usage')
def plot_energy_usage():
    data = load_data()
    fig, ax = plt.subplots()
    grouped_data = data.groupby("Department")["Energy_Used_kWh"].sum()
    ax.bar(grouped_data.index, grouped_data.values, color='blue')
    ax.set_title("Total Energy Usage by Department")
    ax.set_ylabel("Energy Used (kWh)")
    plt.xticks(rotation=45)
    plt.tight_layout()

    return send_file(save_plot(fig), mimetype='image/png')

@app.route('/plot_waste_generation')
def plot_waste_generation():
    data = load_data()
    fig, ax = plt.subplots()
    ax.bar(data["Department"], data["Waste_Generated_kg"], color='brown')
    ax.set_title("Waste Generation Per Department")
    ax.set_ylabel("Waste (kg)")
    plt.xticks(rotation=45)
    plt.tight_layout()

    return send_file(save_plot(fig), mimetype='image/png')


@app.route('/plot_water_usage')
def plot_water_usage():
    data = load_data()
    fig, ax = plt.subplots()
    ax.hist(data["Water_Usage_Liters"], bins=10, color='blue', alpha=0.7)
    ax.set_title("Water Usage Distribution")
    ax.set_xlabel("Water Usage (Liters)")
    ax.set_ylabel("Frequency")
    plt.tight_layout()

    return send_file(save_plot(fig), mimetype='image/png')


# ================= Login & Signup Routes ==================

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    initialize_database()  # Ensure the database and table exist

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if the user already exists
        cursor.execute("SELECT id FROM user WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        if existing_user:
            conn.close()
            return "User already exists! Try a different username."

        # Insert new user
        cursor.execute("INSERT INTO user (username, email, password) VALUES (?, ?, ?)",
                       (username, email, password))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('signup.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if the user exists with the provided credentials
        cursor.execute("SELECT id FROM user WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user'] = username
            return redirect(url_for('add_record'))
        else:
            return "Invalid credentials. Try again!"

    return render_template('login.html')


# @app.route('/profile')
# def profile():
#     if 'user' not in session:
#         return redirect(url_for('login'))
#     return render_template("profile.html", username=session['user'])

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/analysis')
def analysis():
    data = load_data()
    stats = {
        "total_energy_used": data["Energy_Used_kWh"].sum(),
        "avg_renewable_energy": round(data["Renewable_Energy_Percentage"].mean(), 2),
        "total_waste_generated": data["Waste_Generated_kg"].sum(),
        "avg_recycling": round(data["Recycling_Percentage"].mean(), 2),
        "total_co2_emissions": data["CO2_Emissions_kg"].sum()
    }
    return render_template('analysis.html', stats = stats)


# ================= Add New Sustainability Record ==================
@app.route('/add_record', methods=['GET', 'POST'])
def add_record():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        new_record = {
            "Timestamp": request.form["timestamp"],
            "Department": request.form["department"],
            "Energy_Used_kWh": float(request.form["energy"]),
            "Renewable_Energy_Percentage": float(request.form["renewable"]),
            "Waste_Generated_kg": float(request.form["waste"]),
            "Recycling_Percentage": float(request.form["recycling"]),
            "Water_Usage_Liters": float(request.form["water"]),
            "Efficiency_Score": float(request.form["efficiency"]),
            "CO2_Emissions_kg": float(request.form["co2"]),
            "Sustainable_Transport_Percentage": float(request.form["transport"])
        }
        df = load_data()
        df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
        df.to_csv(CSV_PATH, index=False)
        return redirect(url_for('index'))
    return render_template("add_record.html")


# Run the application
if __name__ == '__main__':
    app.run(debug=True)
