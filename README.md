# Saieed Clinical Laboratory Management System

A comprehensive laboratory information management system built with FastAPI and modern web technologies.

## Features

- Patient Management
- Test Order Management
- Result Entry and Verification
- Report Generation (Basic and Quest Labs style)
- User Authentication and Authorization
- Role-based Access Control
- PDF Report Generation
- Modern UI with TailwindCSS

## Tech Stack

- Backend: FastAPI (Python)
- Frontend: HTML5, TailwindCSS
- Database: SQLite
- Authentication: JWT
- PDF Generation: ReportLab

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- Git

## Installation

1. Clone the repository:
```bash
git clone https://github.com/zub165/saieed-clinical-lab.git
cd saieed-clinical-lab
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following content:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./saieed_lab.db
```

5. Initialize the database:
```bash
python init_db.py
```

## Running the Application

1. Start the development server:
```bash
uvicorn main:app --reload
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

## Default Admin Account

- Username: admin
- Password: admin123

## Project Structure

```
saieed-clinical-lab/
├── main.py              # Main application file
├── models.py            # Database models
├── database.py          # Database configuration
├── requirements.txt     # Python dependencies
├── init_db.py          # Database initialization
├── static/             # Static files (CSS, JS, images)
├── templates/          # HTML templates
└── temp/              # Temporary files for PDF generation
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.