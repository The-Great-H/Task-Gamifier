# Task-Gamifier
A simple yet effective personal task and habit tracker that makes your tasks a game (with XP and rewards) to motivate progress. Built entirely with Streamlit, Pandas, and Python.

# 🚀 XP Tracker

A simple, personal **Gamified Task and Habit Tracker** built entirely with Python and Streamlit. This app transforms your to-do list into a lighthearted RPG experience by assigning Experience Points (XP) to tasks, allowing you to earn currency, and "spending" that currency on self-defined rewards.

## 🎯 Key Features

* **Gamified System:** Earn XP based on the time spent on defined tasks.
* **Rewards System:** Define and purchase rewards (e.g., "30 minutes of gaming," "Buy a fancy coffee") using your earned XP.
* **Full Tracking:** Log every earning and spending transaction.
* **Interactive Calendar:** Click any day on the calendar to see a dynamic summary of your activity.
* **Statistics Dashboard:** Visualizations for progress tracking, including current XP balance, recent activity charts, and streaks.
* **Simple & Fast:** Built for personal use with an intuitive, single-page Streamlit interface.

## 💻 How to Run Locally

1.  **Clone the repository:**
    ```bash
    git clone [YOUR-REPO-URL-HERE]
    cd xp-tracker
    ```

2.  **Create a virtual environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the requirements:**
    ```bash
    pip install streamlit pandas plotly
    ```

4.  **Run the application:**
    ```bash
    streamlit run app.py
    ```

The app will open automatically in your browser.

## 💾 Data Persistence

The application currently uses local files (`tasks.json`, `rewards.json`, `xp_log.csv`) for data storage. If running the app in the cloud (like Streamlit Community Cloud), these files will be stored temporarily.
