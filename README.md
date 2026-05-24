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
<img width="1677" height="902" alt="image" src="https://github.com/user-attachments/assets/76ce92e2-83ed-46ab-9ca4-617b9ce74482" />


### 📝 Editable Ledger
*(Updating database records directly from the UI)*
<img width="1391" height="861" alt="image" src="https://github.com/user-attachments/assets/b2689a7c-32f7-438e-b192-8a63ecf70cd0" />


### 🔒 Secure Login
*(Session-state password protection)*
<img width="1391" height="861" alt="image" src="https://github.com/user-attachments/assets/c96e9c3c-02e3-4116-b09e-7c8c147c7f60" />


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
