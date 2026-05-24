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

## 🔑 Prerequisites & API Keys

Before running the app, you need to gather three credentials. Here is exactly how to get them:

### 1. Supabase Database URL
1. Go to [Supabase](https://supabase.com/) and create a free project.
2. Create a database password and save it somewhere safe.
3. In your Supabase dashboard, go to **Settings** (gear icon on the bottom left) > **Database**.
4. Scroll down to the **Connection Pooler** section.
5. Ensure the port is set to `6543` and copy the connection string. It will look like this:
   `postgresql://postgres.xxx:[YOUR-PASSWORD]@aws-0-xx.pooler.supabase.com:6543/postgres`
6. Replace `[YOUR-PASSWORD]` with your actual password (removing the brackets).

### 2. Google Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google account.
3. Click **Get API key** in the left menu.
4. Click **Create API key** and copy the generated string.

### 3. Gmail API Credentials (`credentials.json`)
*(This is required to let the Python script read your bank emails).*
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Search for the **Gmail API** in the top search bar and click **Enable**.
4. Go to **APIs & Services > OAuth consent screen**. Select **External**, fill in the required app name and email fields, and add your own email address as a "Test user".
5. Go to **APIs & Services > Credentials**.
6. Click **+ Create Credentials > OAuth client ID**.
7. Choose **Desktop app** as the application type and click Create.
8. Click the **Download JSON** button. 
9. Rename the downloaded file to exactly `credentials.json` and place it in the root folder of this project.

---

## 🚀 Local Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/maliyash/expense-tracker.git](https://github.com/maliyash/expense-tracker.git)
   cd expense-tracker
