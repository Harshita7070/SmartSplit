# SmartSplit — Smart Expense Splitting & Debt Settlement System

SmartSplit is a full-stack web application that helps groups manage shared expenses, calculate individual balances, and simplify debt settlement. It is designed for friends, roommates, and groups who want to track expenses transparently and fairly.

## Features

- **User Authentication:** Register, log in, and securely access your account.
- **Group Management:** Create groups and organize shared expenses among members.
- **Expense Tracking:** Add expenses and view expense history.
- **Automatic Balance Calculation:** Calculate how much each member owes or is owed.
- **Smart Debt Settlement:** Generate suggested payments to simplify outstanding debts.
- **Settlement Tracking:** Mark payments as paid and track settlement status.
- **Dashboard:** View group and expense summaries.
- **Database Integration:** Store users, groups, expenses, splits, and settlements in MySQL.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web framework |
| MySQL | Database |
| HTML5 | Page structure |
| CSS3 | Styling and responsive UI |
| JavaScript | Client-side interactivity |
| Git & GitHub | Version control |

## Data Structures and Algorithms

SmartSplit demonstrates practical applications of Data Structures and Algorithms:

- **Hash Maps / Dictionaries:** Store and calculate each member's net balance efficiently.
- **Heaps / Priority Queues:** Organize creditors and debtors by outstanding amounts.
- **Greedy Algorithm:** Match debtors with creditors to generate a simplified list of settlement transactions.

The greedy settlement algorithm aims to reduce the number of payments needed to settle group balances.

## Project Structure

```text
SmartSplit/
├── algorithms/
│   ├── balance.py
│   └── settlement.py
├── database/
│   └── db.py
├── routes/
│   ├── auth.py
│   └── groups.py
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── templates/
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python 3
- MySQL Server
- Git

### 1. Clone the repository

```bash
git clone https://github.com/Harshita7070/SmartSplit.git
cd SmartSplit
```

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the database

1. Start MySQL Server.
2. Create a database named `smartsplit`.
3. Configure your database connection settings using environment variables in a local `.env` file.
4. Ensure the required database tables are created before running the application.

**Security note:** Never commit `.env` or publish database passwords or secret keys.

### 5. Run the application

```bash
python app.py
```

Open `http://127.0.0.1:5000/` in your browser.

## Future Improvements

- Support custom and percentage-based expense splits.
- Add charts and detailed spending analytics.
- Improve notifications and settlement history.
- Strengthen validation, authorization, and automated testing.
- Deploy the application for online access.

## Author

**Harshita Jamdar**

Student developer interested in software development, data structures and algorithms, and cybersecurity.

## License

This project is currently available for educational and portfolio purposes. A formal open-source license can be added if needed.
