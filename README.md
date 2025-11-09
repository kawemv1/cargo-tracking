<div id="top">

<p align="center">
  <img src="https://cdn-icons-png.flaticon.com/512/942/942751.png" alt="Cargo Logo" width="20%" style="border-radius:15px;">
</p>

<h1 align="center">🚚 Cargo Tracking System</h1>
<p align="center"><em>Real-time logistics and delivery tracking dashboard for modern supply chains.</em></p>

<p align="center">
  <a href="https://github.com/kawemv1/cargo-tracking">
    <img src="https://img.shields.io/github/last-commit/kawemv1/cargo-tracking?logo=github&color=blue" alt="Last Commit">
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.10+-yellow?logo=python" alt="Python Version">
  </a>
  <a href="https://fastapi.tiangolo.com/">
    <img src="https://img.shields.io/badge/FastAPI%20%7C%20Streamlit-blue?logo=fastapi&logoColor=white" alt="Framework">
  </a>
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-green?logo=opensourceinitiative" alt="MIT License">
  </a>
</p>

<img src="https://raw.githubusercontent.com/eli64s/readme-ai/main/docs/docs/assets/svg/line-gradient.svg" width="100%" height="3px">

## 📘 Quick Links
- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Example Shipment](#example-shipment)
- [Future Improvements](#future-improvements)
- [Author](#author)
- [License](#license)

<img src="https://raw.githubusercontent.com/eli64s/readme-ai/main/docs/docs/assets/svg/line-gradient.svg" width="100%" height="3px">

## 🧭 Overview
The **Cargo Tracking System** is a web-based logistics management platform that allows users to register shipments, monitor delivery status, and visualize routes.  
It combines **FastAPI** (backend) and **Streamlit** (frontend) for a clean, modern, and interactive experience.

---

## ⚙️ Features
- 📦 Register and track shipments with unique IDs  
- 🚛 Update delivery status — In Transit / Delivered / Delayed  
- 🌍 Visualize cargo routes and destinations  
- 📅 Manage and schedule delivery timelines  
- 👥 Role-based access for managers, drivers, and clients  
- 🖥️ User-friendly dashboard with data insights  

---

## 🧩 Tech Stack
| Layer | Technology |
|-------|-------------|
| **Backend** | FastAPI |
| **Frontend** | Streamlit |
| **Database** | SQLite / PostgreSQL |
| **Visualization** | Folium / Mapbox |
| **Deployment** | Streamlit Cloud / Render / Docker |

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/kawemv1/cargo-tracking.git
cd cargo-tracking

# Install dependencies
pip install -r requirements.txt

# ▶ Run the Streamlit dashboard
streamlit run app/app.py

# ▶ Or start the FastAPI backend
uvicorn backend.main:app --reload

# ⏹ To stop the server:
# Press CTRL + C
```
---

## 📂 Project Structure

cargo-tracking/  
├── app/              # Streamlit dashboard  
├── backend/          # FastAPI routes & models  
├── data/             # SQLite DB, sample_data.csv  
├── requirements.txt  
└── README.md


---

## 📦 Example Shipment
| Cargo ID  | Origin | Destination | Weight | Status | Last Updated |
|------------|---------|--------------|---------|------------|---------------|
| CARGO-A101 | Almaty | Astana | 2.3t | In Transit | 2025-11-09 15:30 |

---

## 🔮 Future Improvements
- 🛰️ GPS-based live cargo tracking  
- 📱 Mobile-optimized dashboard  
- 💬 Telegram & WhatsApp notifications  
- 📈 Export reports (Excel / PDF)  

---

## 👨‍💻 Author
**[@kawemv1](https://github.com/kawemv1)**  
Building efficient logistics & automation tools with Python and web frameworks.  
📧 **Email:** kawemv1.dev@gmail.com  

---

## 📜 License
Licensed under the **MIT License** — free to use and modify.  
⭐ **If you find this project helpful, please give it a star!**

<img src="https://raw.githubusercontent.com/eli64s/readme-ai/main/docs/docs/assets/svg/line-gradient.svg" width="100%" height="3px">  
</div>
