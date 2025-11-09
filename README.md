# 🚚 Cargo Tracking System (AI + Web Dashboard)

> **Smart. Real-Time. Transparent.**  
> Track cargo, monitor delivery routes, and predict delays — all in one intelligent system.

![GitHub last commit](https://img.shields.io/github/last-commit/kawemv1/cargo-tracking?color=blue)
![Python](https://img.shields.io/badge/Python-3.10+-yellow?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red?logo=streamlit)
![AI](https://img.shields.io/badge/AI-Enabled-purple?logo=tensorflow)
![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)

---

## ✨ Project Overview

**Cargo Tracking System** is a machine-learning–powered logistics solution built to monitor, analyze, and optimize cargo delivery operations in real-time.

The platform provides:
- 📍 **Live tracking** of shipments and routes  
- ⏱️ **Delivery time prediction** using ML regression  
- ⚙️ **Cargo status management** (in-transit, delayed, delivered)  
- 🛰️ **Map-based visualization** of routes & locations  
- 📊 **Data analytics dashboard** for performance insights  

---

## 🌍 Why This Project?

In modern logistics, **visibility = efficiency**.  
Traditional tracking systems often lack:
- Intelligent delay prediction 🧠  
- Integrated route analytics 🗺️  
- User-friendly dashboards 📈  

This system solves all of that — combining **machine learning**, **geospatial data**, and **interactive visualization** to deliver a truly modern cargo management experience.

---

## 🧠 Key Features

| Category | Description |
|-----------|--------------|
| **🚛 Real-time Tracking** | Monitor cargo location using GPS coordinates or simulated data. |
| **📆 Delivery ETA Prediction** | Predict estimated delivery time using historical data (trained ML model). |
| **📦 Cargo Lifecycle Management** | Automatically update cargo status based on progress. |
| **🌐 Interactive Map Dashboard** | Mapbox/Leaflet integration for visual route tracking. |
| **📊 Analytics Panel** | See top-performing routes, delivery speed, and delay frequency. |
| **⚡ Lightweight Backend** | Powered by FastAPI + SQLite/Postgres for speed and simplicity. |
| **🖥️ Streamlit Web App** | For managers and clients to view tracking data intuitively. |

---

## 🖼️ System Architecture

```text
                   ┌────────────────────┐
                   │   User Interface   │
                   │ (Streamlit / Web)  │
                   └─────────┬──────────┘
                             │
                             ▼
                 ┌────────────────────┐
                 │   REST API Layer   │
                 │   (FastAPI / Flask)│
                 └─────────┬──────────┘
                             │
                             ▼
                 ┌────────────────────┐
                 │   ML Model Engine  │
                 │ (Delay Prediction) │
                 └─────────┬──────────┘
                             │
                             ▼
                 ┌────────────────────┐
                 │ Database / Storage │
                 │ (Postgres / SQLite)│
                 └────────────────────┘
🧩 Tech Stack
Layer	Technology
Frontend	Streamlit / React / Tailwind (optional)
Backend	FastAPI / Flask
Database	SQLite / PostgreSQL
Machine Learning	CatBoost, Scikit-Learn
Visualization	Plotly, Folium, Mapbox, Seaborn
Deployment	Streamlit Cloud / Render / Docker
📦 Example Usage
🚀 Predict Delivery ETA
from catboost import CatBoostRegressor
import pandas as pd

# Load trained model
model = CatBoostRegressor().load_model("models/delivery_eta_model.cbm")

# Example cargo record
cargo = pd.DataFrame([{
    'distance_km': 450,
    'vehicle_type': 'Truck',
    'weather': 'Clear',
    'road_condition': 'Highway',
    'cargo_weight': 2.5,  # tons
}])

eta_hours = model.predict(cargo)[0]
print(f"⏱️ Estimated Delivery Time: {eta_hours:.2f} hours")

🗺️ Example Streamlit Interface
import streamlit as st
import pandas as pd

st.title("🚚 Cargo Tracking Dashboard")
city = st.selectbox("Select Destination City", ["Astana", "Almaty", "Shymkent"])
distance = st.slider("Distance (km)", 10, 2000, 450)
cargo_type = st.selectbox("Cargo Type", ["Standard", "Fragile", "Perishable"])

if st.button("Predict Delivery Time"):
    st.success(f"Predicted ETA: 8.5 hours to {city}")

📊 Model Performance (Example)
Metric	Value
R² Score	0.91
MAE	1.4 hours
RMSE	2.3 hours
Training Data Size	5,000 records
Model Type	CatBoost Regressor
⚙️ Installation
git clone https://github.com/kawemv1/cargo-tracking.git
cd cargo-tracking
pip install -r requirements.txt


Run the dashboard:

streamlit run app/app.py

🧰 Project Structure
cargo-tracking/
│
├─ app/
│   ├─ app.py               # Streamlit dashboard
│   ├─ map_utils.py         # Map functions for routes
│   ├─ api_client.py        # Connects to backend API
│
├─ backend/
│   ├─ main.py              # FastAPI backend
│   ├─ models/              # ML models for ETA prediction
│   └─ database.py
│
├─ data/
│   ├─ deliveries.csv       # Sample dataset
│   └─ routes.json
│
├─ notebooks/
│   ├─ model_training.ipynb
│   ├─ eda.ipynb
│
├─ requirements.txt
└─ README.md

🧭 Future Roadmap

 🛰️ GPS integration for real cargo coordinates

 📱 Mobile-friendly interface for drivers

 ⚙️ Automatic anomaly detection (delays, reroutes)

 🧩 AI-powered route optimization

 💬 Telegram/WhatsApp cargo status notifications

 ☁️ Cloud-based analytics dashboard

💡 Example Dataset Fields
Column	Description
cargo_id	Unique cargo shipment ID
origin_city	Starting point
destination_city	Delivery destination
distance_km	Total route distance
vehicle_type	Truck, Van, Rail, etc.
cargo_weight	Weight in tons
departure_time	Date/time of dispatch
arrival_time	Actual delivery time
delay_hours	Calculated delay
status	Delivered / In transit / Delayed
🌐 Deployment Options

🌍 Streamlit Cloud: easiest for testing

🐳 Docker Compose: scalable multi-container setup

☁️ Render / Railway: free hosting for API + dashboard

🔐 Firebase / Supabase: for storing real tracking data

🧑‍💻 Author

@kawemv1

Building intelligent logistics solutions powered by data, automation, and AI.

📧 Contact: kawemv1.dev@gmail.com

🌍 GitHub: https://github.com/kawemv1

📜 License

Released under the MIT License
.
Free to use, modify, and deploy for educational or commercial purposes.
