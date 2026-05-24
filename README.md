# 💳 Personal Finance OS

An automated, cloud-hosted dashboard that intelligently tracks expenses. It reads bank transaction emails, extracts key financial data using Google's Gemini LLM, stores it securely in PostgreSQL, and visualizes spending trends in a live web app.

## ✨ Features
* **Automated Data Entry:** A GitHub Action runs daily to fetch new transaction emails via the Gmail API.
* **AI Data Extraction:** Uses Google Gemini 2.5 Flash to parse unstructured bank alerts (HDFC, IndusInd) and strictly format them into merchants, amounts, and categories.
* **Cloud Database:** Stores transactions in a remote PostgreSQL database hosted on Supabase.
* **Live Dashboard:** Built with Streamlit and Plotly to visualize spending trends, category breakdowns, and total expenses.
* **Editable Ledger:** A secure, interactive data grid that allows you to correct categories or add notes, writing changes directly back to the database.
* **Secure Authentication:** The live web app is protected by a custom session-state password gateway.

## 📸 Screenshots

### 📊 Main Dashboard
*(Visualizing spending trends and category breakdowns)*
![Dashboard](assets/dashboard.png)

### 📝 Editable Ledger
*(Updating database records directly from the UI)*
![Ledger](assets/ledger.png)

### 🔒 Secure Login
*(Session-state password protection)*
![Login](assets/login.png)

## 🛠️ Tech Stack
* **Frontend/UI:** Streamlit, Pandas, Plotly Express
* **Backend/Automation:** Python, GitHub Actions
* **AI/LLM:** Google GenAI SDK (Gemini 2.5 Flash)
* **Database:** Supabase (PostgreSQL), `psycopg2`, SQLAlchemy
* **APIs:** Gmail API (`google-api-python-client`)

## 🚀 Local Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/maliyash/expense-tracker.git](https://github.com/maliyash/expense-tracker.git)
   cd expense-tracker
