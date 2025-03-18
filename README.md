# Saieed Clinical Laboratory Management System

A comprehensive laboratory management system built with FastAPI and modern web technologies. This system helps manage patient records, lab tests, results, and generates professional lab reports.

## Features

### 1. User Authentication & Authorization
- Secure login system with JWT tokens
- Role-based access control (Admin, Doctor, Technician, Patient)
- Session management and token expiration

### 2. Test Catalog Management
- **Categories:**
  - Routine Health Screening
  - Cardiac Health
  - Diabetes Management
  - Hormone Tests
  - Allergy & Immunology
  - Vitamin & Nutrition
- Detailed test information with pricing
- Easy test search and filtering

### 3. Patient Management
- Patient registration and profile management
- Medical history tracking
- Appointment scheduling
- Insurance information management

### 4. Order Management
- Create and track lab test orders
- Shopping cart functionality
- Order status tracking
- Test preparation instructions

### 5. Results Management
- Digital result entry and verification
- Automated abnormal result flagging
- Historical result comparison
- Result trending and analysis

### 6. Report Generation
- Professional PDF report generation
- Quest Labs style formatting
- Multiple report formats
- Digital signature support
- Email delivery options

## Technical Stack

- **Backend:** FastAPI (Python 3.11+)
- **Database:** MySQL
- **Frontend:** HTML5, TailwindCSS, JavaScript
- **Authentication:** JWT
- **PDF Generation:** ReportLab
- **Documentation:** OpenAPI/Swagger

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/saieed-clinical-lab.git
cd saieed-clinical-lab
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials and other settings
```

5. Initialize the database:
```bash
python init_db.py
```

6. Run the application:
```bash
uvicorn main:app --reload --port 8081
```

## Application Workflow

### 1. Authentication Flow
1. User visits the login page
2. Enters credentials
3. System validates and issues JWT token
4. Token is stored in localStorage
5. User is redirected to dashboard

### 2. Test Ordering Process
1. Browse test catalog
2. Add tests to cart
3. Review cart
4. Enter patient information
5. Select appointment time
6. Confirm order
7. Receive confirmation

### 3. Result Entry Workflow
1. Technician logs in
2. Views pending orders
3. Enters test results
4. System flags abnormal results
5. Results are verified
6. Report is generated

### 4. Report Generation Process
1. Select order/patient
2. System compiles results
3. Generates professional PDF
4. Option to email or print
5. Digital signature applied
6. Report archived

## API Endpoints

### Authentication
- POST `/token` - Login and get access token
- GET `/users/me` - Get current user info

### Patient Management
- POST `/patients` - Register new patient
- GET `/patients/{id}` - Get patient details
- PUT `/patients/{id}` - Update patient info

### Test Management
- GET `/tests` - List all tests
- GET `/tests/{category}` - Get tests by category
- GET `/tests/{id}` - Get test details

### Order Management
- POST `/orders` - Create new order
- GET `/orders/{id}` - Get order details
- PUT `/orders/{id}` - Update order status

### Results
- POST `/results` - Add test results
- GET `/results/{order_id}` - Get order results
- GET `/report/{order_id}` - Generate PDF report

## Security Features

- Password hashing with bcrypt
- JWT token authentication
- Role-based access control
- SQL injection protection
- XSS prevention
- CORS configuration

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@saieedlab.com or open an issue in the repository.

## Acknowledgments

- Quest Diagnostics for UI/UX inspiration
- FastAPI team for the excellent framework
- TailwindCSS team for the styling framework 