# Healthcare Management System

A comprehensive full-stack healthcare platform for managing hospitals, patients, ambulances, beds, and real-time emergency dispatch. Built with **Django REST Framework** (Python) backend and **React** (JavaScript) frontend.

---

## 📋 Table of Contents

- [**Project Overview**](#project-overview)
- [**Tech Stack**](#tech-stack)
- [**Features**](#features)
- [**Project Structure**](#project-structure)
- [**Prerequisites**](#prerequisites)
- [**Installation & Setup**](#installation--setup)
- [**Configuration**](#configuration)
- [**Running the Application**](#running-the-application)
- [**API Documentation**](#api-documentation)
- [**Database Schema**](#database-schema)
- [**Key Modules**](#key-modules)
- [**Development Workflow**](#development-workflow)
- [**Deployment**](#deployment)
- [**Troubleshooting**](#troubleshooting)

---

## 🏥 Project Overview

This healthcare management system is a full-featured platform designed to:

- **Manage Hospital Infrastructure**: Multiple hospitals with departments, staff, resources, and bed allocation
- **Patient Management**: Patient registration, medical records, assessment, and health tracking
- **Emergency Dispatch**: Real-time ambulance booking and dispatch with AI-powered routing
- **Analytics & Reporting**: Hospital performance metrics, bed occupancy, resource utilization
- **Real-time Notifications**: WebSocket-based notifications for emergencies and status updates
- **Role-based Access Control**: Different portals for reception staff, supervisors, ambulance drivers, patients, and admins

---

## 🛠 Tech Stack

### **Backend**
- **Framework**: Django 4.x + Django REST Framework
- **Database**: PostgreSQL 12+
- **Cache & Message Broker**: Redis
- **Task Queue**: Celery with Beat scheduler
- **WebSockets**: Django Channels (with Redis)
- **Real-time Communication**: Twilio (SMS), Google Gemini (AI)
- **Additional**: 
  - JWT Authentication (rest_framework_simplejwt)
  - CORS Support (django-cors-headers)
  - Environment Management (python-dotenv)
  - API Filtering (django-filter)

### **Frontend**
- **Framework**: React 19 (with React Router)
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Maps & Geo**: Leaflet, React-Leaflet, Google Maps API
- **HTTP Client**: Axios
- **Animations**: GSAP
- **Charts**: Recharts
- **Mobile**: Capacitor (iOS/Android support)

---

## ✨ Features

### Core Features
- ✅ **Multi-role Authentication** (Reception, Supervisor, Admin, Ambulance Driver, Patient)
- ✅ **Hospital Management** - Create, manage hospitals with departments and staff
- ✅ **Bed Management** - Real-time bed availability, occupancy tracking, patient assignment
- ✅ **Patient Records** - Complete patient profiles with medical history and assessments
- ✅ **Ambulance Services** - Vehicle fleet management with real-time GPS tracking
- ✅ **Emergency Calls** - 911-style emergency dispatch with AI routing
- ✅ **Resource Allocation** - Manage medical equipment and supplies across hospitals
- ✅ **Real-time Notifications** - WebSocket updates for status changes
- ✅ **Analytics Dashboard** - Performance metrics, bed occupancy charts, call statistics
- ✅ **Supervisor Tools** - Resource mismatches, long occupancy alerts, verification workflows
- ✅ **Mobile Support** - Android/iOS via Capacitor and responsive web design

### Advanced Features
- 🤖 **AI-Powered Routing** - Google Gemini integration for smart dispatch decisions
- 📞 **SMS Notifications** - Twilio-based SMS alerts
- 🔔 **Scheduled Tasks** - Celery Beat for periodic checks (long occupancy, resource mismatches)
- 🗺️ **Geolocation** - Real-time map view with Leaflet
- 🔐 **JWT Authentication** - Secure token-based authentication with refresh tokens
- 🗄️ **Redis Caching** - Performance optimization with Redis cache layer

---

## 📁 Project Structure

```
Healthcare Management System/
│
├── backend/
│   ├── apps/
│   │   ├── authentication/          # User models, JWT tokens, auth views
│   │   ├── hospitals/               # Hospital CRUD, departments, staff
│   │   ├── beds/                    # Bed management & occupancy tracking
│   │   ├── patients/                # Patient records & medical history
│   │   ├── ambulances/              # Ambulance fleet & GPS tracking
│   │   ├── calls/                   # Emergency calls & dispatch system
│   │   ├── supervisors/             # Supervisor workflows & tasks
│   │   ├── analytics/               # Dashboard metrics & reporting
│   │   ├── notifications/           # Real-time WebSocket notifications
│   │   ├── resources/               # Medical equipment & supply management
│   │   └── migrations/              # Database migrations
│   │
│   ├── config/
│   │   ├── settings.py              # Django settings (DB, Redis, Celery, Channels)
│   │   ├── urls.py                  # Main URL routing
│   │   ├── asgi.py                  # ASGI for Channels (WebSockets)
│   │   ├── wsgi.py                  # WSGI for production
│   │   └── celery.py                # Celery configuration
│   │
│   ├── core/
│   │   ├── permissions.py           # Custom DRF permissions
│   │   └── __init__.py
│   │
│   ├── manage.py                    # Django management CLI
│   ├── .env                         # Environment variables (secrets, API keys)
│   └── requirements.txt             # Python dependencies
│
├── frontend/
│   ├── hospital/                    # Main React application
│   │   ├── src/
│   │   │   ├── components/          # Reusable React components
│   │   │   ├── pages/               # Page components (Dashboard, Login, etc.)
│   │   │   ├── services/            # API communication (axios)
│   │   │   ├── App.jsx              # Main app component
│   │   │   └── main.jsx             # Entry point
│   │   │
│   │   ├── public/                  # Static assets
│   │   ├── vite.config.js           # Vite configuration
│   │   ├── package.json             # npm dependencies
│   │   ├── eslint.config.js         # Code linting rules
│   │   ├── tailwind.config.js       # Tailwind CSS configuration
│   │   └── README.md                # Frontend-specific docs
│   │
│   └── frontend_old/                # Legacy HTML/CSS frontend (deprecated)
│
├── package.json                     # Root npm package manifest
├── requirements.txt                 # Root Python dependencies (optional)
├── complete_api_reference.html      # Full API documentation (generated)
└── README.md                        # This file
```

---

## 📦 Prerequisites

Before installing, ensure you have:

### System Requirements
- **Python 3.9+** (Tested on 3.10, 3.11)
- **Node.js 18+** and **npm 9+**
- **PostgreSQL 12+** (Database)
- **Redis 6+** (Cache, Message Broker, WebSocket support)
- **Git** (Version control)
- **Virtual Environment Tool** (venv or conda)

### API Keys Required
- **Google Gemini API Key** (AI routing decisions)
- **Twilio Account** (SMS notifications)
  - Account SID
  - Auth Token
  - Phone Number
- **Google Maps API Key** (Optional, for maps visualization)

### External Services
- PostgreSQL server running
- Redis server running (on `localhost:6379` default)
- Internet connection (for third-party API calls)

---

## 🚀 Installation & Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-repo/healthcare-management.git
cd healthcare-management
```

### Step 2: Create Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 4: Install Frontend Dependencies

```bash
cd ../frontend/hospital
npm install
```

---

## ⚙️ Configuration

### Backend Configuration (.env)

Create a `.env` file in the `backend/` directory with the following variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True  # Set to False in production

# Database Configuration
DB_NAME=healthcare_db
DB_USER=postgres
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
REDIS_CHANNELS_URL=redis://localhost:6379/2

# Allowed Hosts (comma-separated)
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Twilio Configuration (SMS)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# AI & APIs
GEMINI_API_KEY=your_google_gemini_api_key
GROQ_API_KEY=your_groq_api_key

# Webhooks (for ngrok tunneling in development)
BASE_WEBHOOK_URL=https://your-ngrok-url.ngrok-free.app
```

### Frontend Configuration

Create `.env` files in `frontend/hospital/` if needed:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

### Database Setup

```bash
cd backend

# Run migrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser

# Load initial data (if fixtures exist)
python manage.py loaddata initial_data.json
```

---

## 🎯 Running the Application

### Option 1: Development Server (Auto-reload)

**Terminal 1 - Backend (Django)**
```bash
cd backend
python manage.py runserver
# Runs on http://localhost:8000
```

**Terminal 2 - Background Tasks (Celery Worker)**
```bash
cd backend
celery -A config worker -l info
# Processes async tasks
```

**Terminal 3 - Scheduled Tasks (Celery Beat)**
```bash
cd backend
celery -A config beat -l info
# Runs scheduled periodic tasks
```

**Terminal 4 - Frontend (Vite Dev Server)**
```bash
cd frontend/hospital
npm run dev
# Runs on http://localhost:5173
```

### Option 2: Production Deployment

For production, use:
- **Gunicorn** for Django
- **Daphne** for WebSocket support
- **Nginx** as reverse proxy
- Reference the [Deployment](#deployment) section

---

## 📚 API Documentation

The API follows **RESTful** design with JSON payloads.

### Authentication

All endpoints (except login/register) require a JWT token:

```bash
# Login endpoint
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "password"
}

# Response
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

# Use token in headers for subsequent requests
Authorization: Bearer <access_token>
```

### Base URL
- **Development**: `http://localhost:8000/api`
- **Production**: `https://yourdomain.com/api`

### API Endpoints Overview

| Module | Endpoints | Methods |
|--------|-----------|---------|
| **Authentication** | `/auth/login`, `/auth/register`, `/auth/refresh` | POST, GET |
| **Hospitals** | `/hospitals/`, `/hospitals/{id}/` | GET, POST, PUT, DELETE |
| **Beds** | `/beds/`, `/beds/{id}/`, `/beds/availability/` | GET, POST, PUT, DELETE |
| **Patients** | `/patients/`, `/patients/{id}/` | GET, POST, PUT, DELETE |
| **Ambulances** | `/ambulances/`, `/ambulances/{id}/track/` | GET, POST, PUT, DELETE |
| **Calls** | `/calls/`, `/calls/{id}/dispatch/` | GET, POST, PUT |
| **Analytics** | `/analytics/dashboard/`, `/analytics/occupancy/` | GET |
| **Supervisors** | `/supervisors/alerts/`, `/supervisors/verifications/` | GET, POST |
| **Resources** | `/resources/`, `/resources/{id}/` | GET, POST, PUT, DELETE |

### Detailed API Documentation
Full API reference is available in `complete_api_reference.html` in the project root.

---

## 🗄️ Database Schema

### Core Models

**User**
- Roles: Reception, Supervisor, Admin, Ambulance Driver, Patient
- Fields: email, phone, full_name, role, hospital (FK), created_at

**Hospital**
- Fields: name, address, coordinates (lat/lng), phone, capacity, verification_status
- Relations: multiple departments, beds, staff users

**Bed**
- Status: Available, Occupied, Maintenance
- Fields: hospital (FK), ward_name, bed_number, patient (FK), check_in_date
- Tracking: occupancy history, alerts for long stays

**Patient**
- Fields: name, age, medical_history, current_hospital (FK)
- Relations: assigned beds, calls, medical assessments

**Ambulance**
- Fields: registration_number, driver (FK), status, current_location (GPS)
- Tracking: real-time location, availability status

**Call** (Emergency Dispatch)
- Status: Pending, Assigned, In-Progress, Completed
- Fields: patient (FK), ambulance (FK), start_time, end_time, dispatch_reason

**Resource**
- Fields: hospital (FK), quantity, type, expiry_date
- Tracking: availability and usage

---

## 🧩 Key Modules

### Authentication (`apps/authentication/`)
- Custom User model with role-based access
- JWT token generation & refresh
- Email validation
- Password reset workflow

### Hospitals (`apps/hospitals/`)
- CRUD operations for hospital profiles
- Department management
- Hospital verification workflows
- Staff assignment

### Beds (`apps/beds/`)
- Real-time bed availability tracking
- Patient-to-bed assignment
- Occupancy analytics
- Long-stay alerts (>20 days)
- Ward management

### Patients (`apps/patients/`)
- Patient registration & profiles
- Medical history tracking
- Assessment records
- Patient search & filtering

### Ambulances (`apps/ambulances/`)
- Fleet management
- Driver assignment
- Real-time GPS tracking
- Availability status
- Route optimization

### Calls (`apps/calls/`)
- Emergency call creation
- AI-powered dispatch decisions (Gemini API)
- Ambulance assignment logic
- Call history & completion tracking
- Timeline tracking

### Supervisors (`apps/supervisors/`)
- Long occupancy alerts (>20 days bed use)
- Resource mismatch detection
- Hospital verification workflows
- Missing resource updates
- Alert notifications

### Analytics (`apps/analytics/`)
- Dashboard metrics
- Bed occupancy rates
- Call response times
- Hospital performance
- Historical data trending

### Notifications (`apps/notifications/`)
- Real-time WebSocket updates via Django Channels
- SMS notifications (Twilio)
- Email alerts
- Notification preferences

### Resources (`apps/resources/`)
- Medical equipment inventory
- Supply tracking
- Expiry date management
- Cross-hospital resource sharing

---

## 💻 Development Workflow

### Code Organization Best Practices

1. **Models** (`models.py`) - Database schema definitions
2. **Serializers** (`serializers.py`) - Data validation and transformation
3. **Views** (`views.py`) - API endpoint logic and request handling
4. **URLs** (`urls.py`) - Route definitions
5. **Services** (`services.py`) - Business logic (calls to external APIs, complex operations)
6. **Tasks** (`tasks.py`) - Async Celery tasks
7. **Helpers** (`helpers.py`) - Utility functions
8. **Cache** (`cache.py`) - Redis caching logic
9. **Filters** (`filters.py`) - DRF filtering configurations
10. **Permissions** (`permissions.py`) - Custom permission classes
11. **Tests** (`tests.py`) - Unit and integration tests

### Testing

Run tests for a specific app:
```bash
python manage.py test apps.hospitals
```

Run all tests:
```bash
python manage.py test
```

### Database Migrations

After model changes:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Linting & Code Quality

For frontend:
```bash
cd frontend/hospital
npm run lint
npm run lint --fix  # Auto-fix issues
```

---

## 🌐 Deployment

### Prerequisites for Production
- Domain name with SSL certificate
- PostgreSQL on managed database service (AWS RDS, Azure Database, etc.)
- Redis managed service (AWS ElastiCache, Azure Cache, etc.)
- Server infrastructure (AWS EC2, Azure VM, Heroku, etc.)

### Deployment Steps

1. **Set Production Environment Variables**
   - `DEBUG=False`
   - `ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com`
   - Use strong `SECRET_KEY`

2. **Collect Static Files**
   ```bash
   python manage.py collectstatic --no-input
   ```

3. **Run Migrations on Production Database**
   ```bash
   python manage.py migrate --settings=config.settings
   ```

4. **Use Gunicorn + Daphne for ASGI**
   ```bash
   daphne -b 0.0.0.0 -p 8000 config.asgi:application
   # Or use gunicorn with Supervision
   ```

5. **Set Up Nginx Reverse Proxy**
   - Forward HTTP requests to Gunicorn
   - Serve static files directly
   - Configure SSL/TLS

6. **Enable Celery & Beat on Production**
   - Use Supervisor or systemd for process management
   - Monitor task queue health

### Docker Deployment (Optional)

Create a `Dockerfile` for backend:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000"]
```

---

## 🐛 Troubleshooting

### Common Issues

**PostgreSQL Connection Error**
```
django.db.utils.OperationalError: could not connect to server
```
- **Solution**: Check if PostgreSQL is running, verify credentials in `.env`

**Redis Connection Error**
```
Connection refused: Trying to connect to Redis on ('localhost', 6379)
```
- **Solution**: Start Redis server (`redis-server` on macOS, `redis-cli` to test)

**Celery Worker Not Processing Tasks**
```
No workers registered for this exchange
```
- **Solution**: Start Celery worker: `celery -A config worker -l info`

**WebSocket Connection Failed**
```
WebSocket connection closed unexpectedly
```
- **Solution**: Ensure Daphne is running and `CHANNEL_LAYERS` is configured in settings

**CORS Issues (Frontend)**
```
Access to XMLHttpRequest blocked by CORS policy
```
- **Solution**: Update `CORS_ALLOWED_ORIGINS` in Django settings

**Static Files Not Loading**
```
404 Not Found for /static/css/style.css
```
- **Solution**: Run `python manage.py collectstatic` and check `STATIC_ROOT`

### Debugging Tips

1. Enable Django Debug Toolbar: `pip install django-debug-toolbar`
2. Check logs: `tail -f logs/django.log`
3. Use Django shell: `python manage.py shell`
4. Monitor Celery tasks: `celery -A config events`
5. Test API endpoints with Postman/curl

---

## 📖 Documentation Files

- **Backend API Reference**: `complete_api_reference.html`
- **Postman Collection**: Import to test API endpoints
- **Database ERD**: Database schema diagrams
- **Architecture Diagram**: System design documentation

---

## 🔐 Security Considerations

- ✅ Use strong `SECRET_KEY` in production
- ✅ Enable HTTPS/SSL in production
- ✅ Store API keys securely (never commit `.env` to git)
- ✅ Use environment variables for secrets
- ✅ Implement rate limiting on API endpoints
- ✅ Validate and sanitize all user inputs
- ✅ Use CSRF tokens for state-changing operations
- ✅ Implement proper CORS policies
- ✅ Regular security audits and dependency updates

---

## 📝 License

This project is proprietary. All rights reserved.

---

## 👥 Support & Contact

For issues, questions, or contributions, please contact the development team or create an issue in the repository.

---

**Last Updated**: March 2026  
**Version**: 1.0.0
