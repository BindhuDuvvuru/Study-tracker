# 📚 Study Tracker

A smart study planning web application that helps students organize subjects, track progress, and generate optimized weekly study schedules based on priority and exam dates.

---

## 🚀 Features

* 📅 Automatic timetable generation
* 📊 Progress tracking for each subject
* ⚡ Priority-based scheduling (exam date + difficulty)
* 🧠 Smart time allocation algorithm
* 🎯 Urgency classification (High / Medium / Low)
* 💻 Clean and simple user interface

---

## 🛠️ Tech Stack

* **Backend:** Python (Flask)
* **Frontend:** HTML, CSS
* **Database:** SQLite

---

## 🔄 Project Flow (Working Logic)

This system optimizes study efficiency by dynamically allocating time based on urgency and difficulty.

### 🧩 Step 1: User Input

* Add subjects with:

  * Name
  * Difficulty level
  * Exam date
  * Current progress (%)

---

### 🗄️ Step 2: Data Processing

* Stores data in SQLite database
* Calculates:

  * Days remaining until exam
  * Remaining syllabus (100 - progress)

---

### ⚡ Step 3: Priority Calculation

* Priority is based on:

  * Exam proximity (fewer days → higher priority)
  * Difficulty level (harder subjects → higher priority)

👉 Higher priority subjects get more focus

---

### 🧠 Step 4: Smart Time Allocation

* User enters available study hours per day
* System distributes weekly hours (7 days)
* Uses weighted allocation:

  * High priority → more hours
  * Low priority → fewer hours

---

### 📅 Step 5: Timetable Generation

* Generates structured weekly plan
* Ensures:

  * Balanced workload
  * Focus on urgent subjects
  * Coverage of all subjects

---

### 🎯 Step 6: Output

* Displays:

  * Daily study schedule
  * Suggested study hours
  * Urgency levels

---

## 🔁 Flow Overview

User Input → Data Processing → Priority Calculation → Smart Allocation → Timetable → Output

---

## 📁 Project Structure

```
Study-tracker/
│
├── study_tracker/
│   ├── app.py
│   ├── templates/
│   │   ├── index.html
│   │   ├── subjects.html
│   │   ├── timetable.html
│   │   └── exam_schedule.html
│   ├── static/
│   │   ├── style.css
│   │   └── scripts.js
│   └── __pycache__/
│
├── README.md
└── .gitignore
```

> Note: Database file is excluded for portability and cleaner repository.

---

## ▶️ How to Run

### 1. Clone the repository

```bash
git clone https://github.com/BindhuDuvvuru/Study-tracker.git
```

### 2. Navigate to project folder

```bash
cd Study-tracker
```

### 3. Install dependencies

```bash
pip install flask
```

### 4. Run the application

```bash
python app.py
```

### 5. Open in browser

```
http://127.0.0.1:5000/
```

---

## 💡 Future Enhancements

* 📱 Responsive mobile design
* 🔐 User authentication system
* ☁️ Cloud database integration
* 📊 Analytics dashboard
* 📌 Reminder notifications

---

## 👩‍💻 Author

**Bindhu Duvvuru**

---

## ⭐ If you like this project

Give it a ⭐ on GitHub!
