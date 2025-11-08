# 🎓 ITpark Academy - Online Learning Platform

[![Flask](https://img.shields.io/badge/Flask-3.0.3-blue.svg)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Security](https://img.shields.io/badge/Security-Hardened-brightgreen.svg)](#-security-features)

Professional online education platform built with Flask. Features a modern, responsive design with multi-language support (English, Uzbek, Russian) and comprehensive security implementation.

![ITpark Academy](https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=1200&q=80)

## ✨ Features

### 🎯 Core Functionality
- 👤 **User Authentication** - Secure registration and login with bcrypt password hashing
- 🔐 **Role-Based Access Control** - Admin and Student roles with different permissions
- 📚 **Course Management** - Create, edit, and manage courses
- 👨‍🏫 **Teacher Profiles** - Detailed instructor information and specialties
- 📝 **Enrollment System** - Course enrollment requests with status tracking
- 📊 **Attendance Tracking** - Monthly attendance records for students
- 🌐 **Multi-Language Support** - English, O'zbek, Русский
- 🌓 **Dark/Light Mode** - User-preferred theme toggle
- 📱 **Responsive Design** - Mobile-friendly interface

### 🔒 Security Features

✅ **Password Security**
- Bcrypt password hashing (12 rounds)
- No plain-text password storage
- Secure password validation

✅ **CSRF Protection**
- Flask-WTF CSRF tokens on all forms
- Protection against Cross-Site Request Forgery

✅ **Rate Limiting**
- Login: 10 attempts per hour
- Registration: 5 attempts per hour
- Enrollment: 3 per hour
- Protection against brute-force attacks

✅ **Session Security**
- HttpOnly cookies
- SameSite cookie policy
- Secure session configuration

✅ **Input Validation**
- Server-side validation for all user inputs
- Protection against SQL Injection
- XSS prevention

✅ **Error Handling**
- Professional error pages (404, 500)
- Database rollback on errors
- User-friendly error messages

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/itpark-academy.git
cd itpark-academy/fullstackwebsite-main
```

2. **Create virtual environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

Create a `.env` file:
```env
FLASK_SECRET_KEY=your-secret-key-here-min-32-chars
DATABASE_URL=sqlite:///academy.db
FLASK_DEBUG=True
SESSION_COOKIE_SECURE=False
```

5. **Initialize database**
```bash
python init_db.py
```

6. **Run the application**
```bash
python app.py
```

Visit: `http://127.0.0.1:5000`

### Default Login Credentials

**Admin:**
- Username: `admin`
- Password: `admin123`

**Student:**
- Username: `student`
- Password: `student123`

⚠️ **IMPORTANT:** Change these passwords in production!

## 📁 Project Structure

```
fullstackwebsite-main/
├── app.py                  # Main Flask application
├── init_db.py             # Database initialization
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables (create this)
├── .env.example           # Environment template
├── .gitignore            # Git ignore rules
├── LICENSE               # MIT License
├── README.md             # This file
├── Procfile              # Heroku deployment
├── static/               # Static assets
│   ├── css/
│   │   └── style.css    # Main stylesheet
│   └── js/
│       └── main.js      # JavaScript functionality
├── templates/            # HTML templates
│   ├── base.html        # Base template
│   ├── index.html       # Homepage
│   ├── courses.html     # Courses page
│   ├── teachers.html    # Teachers page
│   ├── login.html       # Login page
│   ├── register.html    # Registration page
│   ├── dashboard.html   # User dashboard
│   ├── admin.html       # Admin panel
│   ├── edit_course.html # Course editor
│   ├── edit_teacher.html# Teacher editor
│   └── errors/          # Error pages
│       ├── 404.html
│       └── 500.html
└── instance/            # Instance folder (auto-created)
    └── academy.db       # SQLite database
```

## 🎨 Tech Stack

### Backend
- **Flask 3.0.3** - Web framework
- **SQLAlchemy** - ORM for database operations
- **Flask-Bcrypt** - Password hashing
- **Flask-WTF** - CSRF protection and forms
- **Flask-Limiter** - Rate limiting
- **python-dotenv** - Environment configuration

### Frontend
- **HTML5 & CSS3** - Modern markup and styling
- **Vanilla JavaScript** - No framework dependencies
- **Google Fonts (Inter)** - Typography
- **Responsive Design** - Mobile-first approach

### Database
- **SQLite** (Development)
- **PostgreSQL** (Production-ready)

## 🔧 Configuration

### Development
```env
FLASK_ENV=development
FLASK_DEBUG=True
SESSION_COOKIE_SECURE=False
```

### Production
```env
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_SECRET_KEY=<generate-strong-key>
SESSION_COOKIE_SECURE=True
DATABASE_URL=postgresql://user:pass@host/dbname
```

## 🚀 Deployment

### Heroku

1. Create a Heroku app:
```bash
heroku create your-app-name
```

2. Add PostgreSQL:
```bash
heroku addons:create heroku-postgresql:hobby-dev
```

3. Set environment variables:
```bash
heroku config:set FLASK_SECRET_KEY=your-secret-key
heroku config:set FLASK_ENV=production
```

4. Deploy:
```bash
git push heroku main
```

5. Initialize database:
```bash
heroku run python init_db.py
```

### Other Platforms

The application supports deployment to:
- **Railway** - `railway up`
- **Render** - Use `gunicorn app:app`
- **PythonAnywhere** - WSGI configuration
- **Docker** - Containerized deployment

## 🌍 Multi-Language Support

The platform supports three languages:
- 🇬🇧 **English** (en)
- 🇺🇿 **O'zbek tili** (uz)
- 🇷🇺 **Русский** (ru)

Language can be changed via the dropdown in the navigation bar.

## 🛡️ Security Best Practices

1. **Never commit `.env` file** - Use `.env.example` as template
2. **Use strong SECRET_KEY** - Minimum 32 random characters
3. **Enable HTTPS in production** - Set `SESSION_COOKIE_SECURE=True`
4. **Regular backups** - Backup database regularly
5. **Update dependencies** - Keep packages up to date
6. **Monitor logs** - Check for suspicious activity

## 📝 API Endpoints

### Public Routes
- `GET /` - Homepage
- `GET /courses` - Course listing
- `GET /teachers` - Teacher profiles
- `GET /login` - Login page
- `POST /login` - Login submission
- `GET /register` - Registration page
- `POST /register` - Registration submission

### Protected Routes (Login Required)
- `GET /dashboard` - User dashboard
- `POST /courses/enroll` - Enrollment submission

### Admin Routes (Admin Only)
- `GET /admin` - Admin panel
- `POST /admin/courses/create` - Create course
- `POST /admin/teachers/create` - Create teacher
- `GET /admin/courses/<id>/edit` - Edit course
- `POST /admin/courses/<id>/delete` - Delete course
- And more...

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**ITpark Academy Development Team**

- Website: [itpark.uz](https://itpark.uz)
- Email: info@itpark.uz

## 🙏 Acknowledgments

- Flask community for excellent documentation
- Contributors who helped improve this project
- All our students and teachers

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/itpark-academy/issues) page
2. Create a new issue with detailed description
3. Contact us at support@itpark.uz

---

**⭐ If you find this project useful, please consider giving it a star!**

Made with ❤️ by ITpark Academy Team
