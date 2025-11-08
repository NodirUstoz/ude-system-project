from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
from datetime import datetime
import json
import os
import secrets

app = Flask(__name__)

# Security configurations
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = None

# Database configuration
database_url = os.environ.get('DATABASE_URL', 'sqlite:///academy.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Constants
MAX_STUDENTS_PER_COURSE = 25
MAX_LESSONS_PER_MONTH = 13


# Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    enrollment_requests = db.relationship('EnrollmentRequest', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    bio = db.Column(db.Text, nullable=False)
    specialty = db.Column(db.String(120), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    courses = db.relationship('Course', backref='teacher', lazy=True)


class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    duration = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)

    students = db.relationship('CourseStudent', backref='course', lazy=True, cascade='all, delete-orphan')
    attendance_months = db.relationship('AttendanceMonth', backref='course', lazy=True, cascade='all, delete-orphan')
    enrollment_requests = db.relationship('EnrollmentRequest', backref='course', lazy=True, cascade='all, delete-orphan')


class EnrollmentRequest(db.Model):
    __tablename__ = 'enrollment_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    experience = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='new')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CourseStudent(db.Model):
    __tablename__ = 'course_students'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attendance_records = db.relationship('AttendanceRecord', backref='student', lazy=True, cascade='all, delete-orphan')


class AttendanceMonth(db.Model):
    __tablename__ = 'attendance_months'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    month_label = db.Column(db.String(60), nullable=False)
    lesson_dates = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    records = db.relationship('AttendanceRecord', backref='month', lazy=True, cascade='all, delete-orphan')


class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'
    id = db.Column(db.Integer, primary_key=True)
    month_id = db.Column(db.Integer, db.ForeignKey('attendance_months.id'), nullable=False)
    course_student_id = db.Column(db.Integer, db.ForeignKey('course_students.id'), nullable=False)
    lesson_index = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(1), nullable=False, default='+')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Translations (keeping from original)
TRANSLATIONS = {
    'en': {
        'nav': {
            'home': 'Home',
            'courses': 'Courses',
            'teachers': 'Teachers',
            'dashboard': 'Dashboard',
            'admin': 'Admin',
            'login': 'Sign In',
            'logout': 'Logout',
            'register': 'Sign Up'
        },
        'hero': {
            'badge': 'Learn. Build. Innovate.',
            'title': 'Level up your tech career with unstoppable confidence',
            'description': 'ITpark Academy pairs ambitious learners with mentors who have shipped world-class products. Build a powerful portfolio while being coached every step of the way.',
            'primary_cta': 'Explore Courses',
            'secondary_cta': 'Meet Our Mentors',
            'card_title': 'Next Cohort Launch',
            'card_date': '15 January 2026',
            'card_status': '68% of seats already reserved'
        },
        'home': {
            'popular_badge': 'Popular pathways',
            'featured_title': 'Signature programs',
            'featured_copy': 'Discover industry-crafted tracks designed to help you ship confidently and interview like a pro.',
            'view_course': 'Discover the program',
            'courses_empty': 'Courses rolling out soon. Stay tuned!',
            'teachers_badge': 'Expert mentors',
            'teachers_title': 'Meet our teaching team',
            'teachers_copy': 'Learn directly from senior engineers, data scientists, and cloud architects who solve real problems every day.',
            'teachers_empty': 'Teacher profiles arriving shortly.',
            'cta_title': 'Ready to accelerate your growth?',
            'cta_copy': 'Join hundreds of graduates thriving at leading tech companies around the globe.',
            'cta_button': 'Join the academy'
        },
        'courses': {
            'title': 'Courses',
            'subtitle': 'Choose a crafted learning experience that unlocks new opportunities and real-world confidence.',
            'search_placeholder': 'Search courses by name',
            'search_button': 'Search',
            'empty': 'No courses match your search right now.',
            'instructor': 'Instructor',
            'enroll_button': 'Enroll in this course'
        },
        'teachers': {
            'title': 'Our teachers',
            'subtitle': 'Get to know the mentors who will guide you through every lab, review, and milestone.',
            'focus': 'Core focus:',
            'empty': 'Mentor profiles are being polished. Check back soon!'
        },
        'auth': {
            'login_heading': 'Welcome back',
            'login_copy': 'Log in to access your dashboard, track milestones, and receive tailored mentor feedback.',
            'benefits': [
                'Personalised learning roadmaps',
                'Hands-on project critiques from mentors',
                'Live community workshops and hiring events'
            ],
            'sign_in': 'Sign in',
            'username': 'Username',
            'password': 'Password',
            'username_placeholder': 'Enter your username',
            'password_placeholder': 'Enter your password',
            'login_button': 'Sign in',
            'admin_hint': '',
            'no_account': "Don't have an account?",
            'create_account': 'Create one',
            'register_heading': 'Create your student profile',
            'register_copy': 'Join the academy today and start building career-defining skills.',
            'confirm_password': 'Confirm password',
            'confirm_placeholder': 'Re-enter your password',
            'signup_button': 'Sign up',
            'have_account': 'Already registered?',
            'login_link': 'Sign in'
        },
        'admin': {
            'title': 'Admin dashboard',
            'subtitle': 'Manage programs, mentors, learners, and attendance from one clean interface.',
            'courses': 'Courses',
            'add_course': 'Create new course',
            'title_label': 'Title',
            'description': 'Description',
            'duration': 'Duration',
            'duration_placeholder': 'e.g., 12 weeks',
            'price': 'Price',
            'image_url': 'Image URL',
            'teacher': 'Teacher',
            'select_teacher': 'Select a teacher',
            'add_button': 'Add course',
            'courses_empty': 'No courses yet. Add one above.',
            'edit': 'Edit',
            'delete': 'Delete',
            'teachers': 'Teachers',
            'add_teacher': 'Add new teacher',
            'name': 'Name',
            'specialty': 'Specialty',
            'bio': 'Bio',
            'add_teacher_button': 'Add teacher',
            'teachers_empty': 'No teachers yet. Add one above.',
            'users': 'Registered users',
            'id': 'ID',
            'username': 'Username',
            'role': 'Role',
            'users_empty': 'No users found.',
            'attendance': 'Attendance tracker',
            'status': 'Status',
            'mark_present': 'Mark present',
            'mark_absent': 'Mark absent',
            'present': 'Present',
            'absent': 'Absent'
        },
        'dashboard': {
            'greeting': 'Hi, {username}!',
            'subtitle': 'Track your learning journey and stay on top of your goals.',
            'profile': 'Profile',
            'username': 'Username',
            'role': 'Role',
            'member_since': 'Member since',
            'enrolled': 'Enrolled courses',
            'none': 'You are not enrolled in any courses yet.'
        },
        'footer': {
            'tagline': 'Empowering learners with cutting-edge technology skills. Join us to build the future.',
            'quick_links': 'Quick links',
            'contact': 'Contact',
            'email': 'Email',
            'phone': 'Phone',
            'address': 'Address',
            'rights': 'All rights reserved.'
        },
        'theme': {
            'toggle': 'Toggle theme'
        },
        'language': {
            'label': 'Language',
            'current': 'Current language'
        },
        'flash': {
            'login_required': 'Please log in to access this page.',
            'not_authorized': 'You are not authorized to view that page.',
            'invalid_credentials': 'Invalid credentials. Please try again.',
            'logout': 'You have been logged out.',
            'welcome': 'Welcome back, {username}!',
            'account_created': 'Account created! Please log in.',
            'username_taken': 'That username is already taken.',
            'password_mismatch': 'Passwords do not match.',
            'course_required': 'All course fields except image are required.',
            'price_numeric': 'Price must be a numeric value.',
            'course_created': 'Course created successfully.',
            'course_updated': 'Course updated successfully.',
            'course_deleted': 'Course deleted.',
            'teacher_required': 'Name, bio, and specialty are required for teachers.',
            'teacher_created': 'Teacher profile created.',
            'teacher_updated': 'Teacher updated successfully.',
            'teacher_deleted': 'Teacher deleted.',
            'teacher_in_use': 'Cannot delete teacher while they are assigned to courses.',
            'attendance_updated': 'Attendance status updated.',
            'attendance_admin_forbidden': 'Attendance is only tracked for students.',
            'enroll_saved': 'Application received! We will reach out shortly.',
            'student_added': 'Student added to the course group.',
            'student_deleted': 'Student removed from the group.',
            'student_limit': 'This group already has the maximum of 25 students.',
            'month_created': 'Attendance month saved.',
            'month_deleted': 'Attendance month removed.',
            'enroll_status_updated': 'Enrollment request status updated.'
        }
    },
    'uz': {
        'nav': {
            'home': 'Bosh sahifa',
            'courses': 'Kurslar',
            'teachers': 'Ustozlar',
            'dashboard': 'Kabinet',
            'admin': 'Administrator',
            'login': 'Kirish',
            'logout': 'Chiqish',
            'register': "Ro'yxatdan o'tish"
        },
        'hero': {
            'badge': "Birgalikda o'rganamiz. Birgalikda yaratamiz. Birgalikda rivojlanamiz.",
            'title': 'IT karyerangizni ishonch bilan boshlang',
            'description': "ITpark Academy — jasoratli o'quvchilarni bozor tajribasiga ega mentorlar bilan bog'laydi. Har bir bosqichda qo'llab-quvvatlovchi jamoa bilan portfolioingizni kuchaytiring.",
            'primary_cta': 'Kurslarni ko\'rish',
            'secondary_cta': 'Mentorlar bilan tanishish',
            'card_title': 'Navbatdagi kurs starti',
            'card_date': '2026-yil 15-yanvar',
            'card_status': 'Joylarning 68% band'
        },
        'home': {
            'popular_badge': "Ommabop yo'nalishlar",
            'featured_title': 'Asosiy dasturlar',
            'featured_copy': "Ish beruvchilar bilan birgalikda ishlab chiqilgan, tez va samarali natija beradigan yo'nalishlarni tanlang.",
            'view_course': 'Dastur haqida batafsil',
            'courses_empty': 'Kurslar tez orada qo'shiladi. Kuzatib boring!',
            'teachers_badge': 'Mutaxassis mentorlar',
            'teachers_title': 'Ustozlar jamoasi',
            'teachers_copy': "Har kuni real muammolarni hal qiladigan yuqori malakali dasturlashchilar va analitiklardan ta'lim oling.",
            'teachers_empty': 'Mentor profillari tayyorlanmoqda.',
            'cta_title': 'Rivojlanish sur'atingizni tezlashtirishga tayyormisiz?',
            'cta_copy': "O'zbekiston va butun dunyo bo'ylab yetakchi IT kompaniyalarda ishlayotgan yuzlab bitiruvchilarga qo'shiling.",
            'cta_button': 'O'quv markaziga qo'shilish'
        },
        'courses': {
            'title': 'Kurslar',
            'subtitle': "Karyerangizni yangi bosqichga olib chiqadigan, ehtiyotkorlik bilan yaratilgan o'quv dasturini tanlang.",
            'search_placeholder': 'Kurs nomi bo'yicha qidirish',
            'search_button': 'Qidirish',
            'empty': 'Hozircha kurslar topilmadi.',
            'instructor': 'Mentor',
            'enroll_button': 'Kursga yozilish'
        },
        'teachers': {
            'title': 'Bizning ustozlar',
            'subtitle': "Har bir laboratoriya, loyiha va suhbatda yoningizda bo'ladigan mentorlar bilan tanishing.",
            'focus': 'Asosiy yo'nalish:',
            'empty': 'Ustoz maʼlumotlari yaqinda qo'shiladi.'
        },
        'auth': {
            'login_heading': 'Xush kelibsiz',
            'login_copy': "Kabinetga kiring, natijalarni kuzating va mentorlarning shaxsiy tavsiyalarini oling.",
            'benefits': [
                "Shaxsiylashtirilgan o'quv yo'li",
                'Mentorlarning loyiha bo'yicha fikrlari',
                'Jonli hamjamiyat tadbirlari va ishga joylashish sessiyalari'
            ],
            'sign_in': 'Kirish',
            'username': 'Foydalanuvchi nomi',
            'password': 'Parol',
            'username_placeholder': 'Foydalanuvchi nomini kiriting',
            'password_placeholder': 'Parolni kiriting',
            'login_button': 'Kirish',
            'admin_hint': ' ',
            'no_account': "Hisobingiz yo'qmi?",
            'create_account': "Ro'yxatdan o'ting",
            'register_heading': 'Shaxsiy profil yarating',
            'register_copy': "Bugunoq akademiyaga qo'shiling va karyerani o'zgartiradigan ko'nikmalarni o'rganing.",
            'confirm_password': 'Parolni tasdiqlang',
            'confirm_placeholder': 'Parolni qayta kiriting',
            'signup_button': "Ro'yxatdan o'tish",
            'have_account': "Allaqachon profil yaratilganmi?",
            'login_link': 'Kirish'
        },
        'admin': {
            'title': 'Admin paneli',
            'subtitle': 'Kurslar, ustozlar, foydalanuvchilar va davomatni bir joyda boshqaring.',
            'courses': 'Kurslar',
            'add_course': 'Yangi kurs yaratish',
            'title_label': 'Sarlavha',
            'description': 'Taʼrif',
            'duration': 'Davomiylik',
            'duration_placeholder': 'masalan, 12 hafta',
            'price': 'Narx',
            'image_url': 'Rasm URL manzili',
            'teacher': 'Ustoz',
            'select_teacher': 'Ustozni tanlang',
            'add_button': 'Kurs qo'shish',
            'courses_empty': 'Hali kurs qo'shilmagan. Yuqoridan qo'shing.',
            'edit': 'Tahrirlash',
            'delete': 'O'chirish',
            'teachers': 'Ustozlar',
            'add_teacher': 'Yangi ustoz qo'shish',
            'name': 'Ism',
            'specialty': 'Ixtisoslik',
            'bio': 'Bio',
            'add_teacher_button': 'Ustoz qo'shish',
            'teachers_empty': 'Hali ustoz kiritilmagan.',
            'users': 'Foydalanuvchilar ro'yxati',
            'id': 'ID',
            'username': 'Foydalanuvchi',
            'role': 'Rol',
            'users_empty': 'Foydalanuvchilar topilmadi.',
            'attendance': 'Davomat nazorati',
            'status': 'Holat',
            'mark_present': 'Bor deb belgilash',
            'mark_absent': 'Yo'q deb belgilash',
            'present': 'Bor',
            'absent': 'Yo'q'
        },
        'dashboard': {
            'greeting': 'Salom, {username}!',
            'subtitle': "Ma'lumotlaringizni kuzatib boring va maqsadlaringizga yeting.",
            'profile': 'Profil',
            'username': 'Foydalanuvchi',
            'role': 'Rol',
            'member_since': 'Aʼzo bo'lingan sana',
            'enrolled': 'Tanlangan kurslar',
            'none': 'Hozircha kurslarga yozilmagansiz.'
        },
        'footer': {
            'tagline': "Zamonaviy texnologik ko'nikmalarni o'rgatib, kelajakni birga quramiz.",
            'quick_links': 'Tezkor havolalar',
            'contact': 'Aloqa',
            'email': 'Elektron pochta',
            'phone': 'Telefon',
            'address': 'Manzil',
            'rights': 'Barcha huquqlar himoyalangan.'
        },
        'theme': {
            'toggle': 'Mavzuni almashtirish'
        },
        'language': {
            'label': 'Til',
            'current': 'Faol til'
        },
        'flash': {
            'login_required': 'Iltimos, ushbu sahifani ko'rish uchun tizimga kiring.',
            'not_authorized': 'Sizda bu sahifaga kirish huquqi yo'q.',
            'invalid_credentials': 'Login yoki parol noto'g'ri.',
            'logout': 'Hisobdan chiqdingiz.',
            'welcome': 'Xush kelibsiz, {username}!',
            'account_created': 'Profil yaratildi! Endi tizimga kiring.',
            'username_taken': 'Bu foydalanuvchi nomi band.',
            'password_mismatch': 'Parollar mos kelmadi.',
            'course_required': 'Rasm tashqari barcha kurs maydonlari majburiy.',
            'price_numeric': 'Narx raqam bo'lishi kerak.',
            'course_created': 'Kurs muvaffaqiyatli yaratildi.',
            'course_updated': 'Kurs yangilandi.',
            'course_deleted': 'Kurs o'chirildi.',
            'teacher_required': 'Ism, bio va ixtisoslik majburiy.',
            'teacher_created': 'Ustoz profili yaratildi.',
            'teacher_updated': 'Ustoz maʼlumotlari yangilandi.',
            'teacher_deleted': 'Ustoz o'chirildi.',
            'teacher_in_use': 'Ustoz kursga biriktirilgan paytda o'chirib bo'lmaydi.',
            'attendance_updated': 'Davomat holati yangilandi.',
            'attendance_admin_forbidden': 'Davomat faqat talabalar uchun yuritiladi.',
            'enroll_saved': 'Arizangiz qabul qilindi. Tez orada siz bilan bog'lanamiz.',
            'student_added': 'Talaba guruhga muvaffaqiyatli qo'shildi.',
            'student_deleted': 'Talaba guruhdan o'chirildi.',
            'student_limit': 'Bu guruhda 25 talabagacha ruxsat etiladi.',
            'month_created': 'Davomat oyi saqlandi.',
            'month_deleted': 'Davomat oyi o'chirildi.',
            'enroll_status_updated': 'Ariza holati yangilandi.'
        }
    },
    'ru': {
        'nav': {
            'home': 'Главная',
            'courses': 'Курсы',
            'teachers': 'Наставники',
            'dashboard': 'Кабинет',
            'admin': 'Админ',
            'login': 'Войти',
            'logout': 'Выйти',
            'register': 'Регистрация'
        },
        'hero': {
            'badge': 'Учись. Создавай. Внедряй.',
            'title': 'Начните карьеру в IT с уверенностью и поддержкой наставников',
            'description': 'ITpark Academy соединяет мотивированных студентов с экспертами, создающими реальные продукты. Соберите сильное портфолио и получайте обратную связь на каждом шаге.',
            'primary_cta': 'Посмотреть курсы',
            'secondary_cta': 'Познакомиться с наставниками',
            'card_title': 'Старт следующего потока',
            'card_date': '15 января 2026',
            'card_status': '68% мест уже забронировано'
        },
        'home': {
            'popular_badge': 'Популярные направления',
            'featured_title': 'Флагманские программы',
            'featured_copy': 'Выбирайте треки, созданные инженерами и рекрутерами, чтобы быстро выйти на новый уровень.',
            'view_course': 'Подробнее о программе',
            'courses_empty': 'Скоро появятся новые программы. Оставайтесь с нами!',
            'teachers_badge': 'Экспертные наставники',
            'teachers_title': 'Команда преподавателей',
            'teachers_copy': 'Учитесь у разработчиков, аналитиков и архитекторов, которые ежедневно решают боевые задачи.',
            'teachers_empty': 'Профили преподавателей скоро будут доступны.',
            'cta_title': 'Готовы ускорить развитие?',
            'cta_copy': 'Присоединяйтесь к выпускникам, работающим в ведущих технологических компаниях.',
            'cta_button': 'Присоединиться к академии'
        },
        'courses': {
            'title': 'Курсы',
            'subtitle': 'Выберите программу, которая откроет новые горизонты и уверенность в навыках.',
            'search_placeholder': 'Поиск курса по названию',
            'search_button': 'Искать',
            'empty': 'Подходящих курсов пока нет.',
            'instructor': 'Преподаватель',
            'enroll_button': 'Записаться на курс'
        },
        'teachers': {
            'title': 'Наши наставники',
            'subtitle': 'Познакомьтесь с экспертами, которые будут сопровождать вас на каждом этапе обучения.',
            'focus': 'Ключевое направление:',
            'empty': 'Преподаватели появятся позже.'
        },
        'auth': {
            'login_heading': 'Рады видеть снова',
            'login_copy': 'Войдите, чтобы отслеживать прогресс, получать комментарии и участвовать в живых созвонах.',
            'benefits': [
                'Персональный план обучения',
                'Обратная связь по проектам от наставников',
                'Живые мероприятия и карьерные консультации'
            ],
            'sign_in': 'Войти',
            'username': 'Логин',
            'password': 'Пароль',
            'username_placeholder': 'Введите логин',
            'password_placeholder': 'Введите пароль',
            'login_button': 'Войти',
            'admin_hint': '',
            'no_account': 'Нет аккаунта?',
            'create_account': 'Зарегистрируйтесь',
            'register_heading': 'Создайте профиль студента',
            'register_copy': 'Присоединяйтесь сегодня и развивайте навыки, которые ценят работодатели.',
            'confirm_password': 'Подтвердите пароль',
            'confirm_placeholder': 'Повторите пароль',
            'signup_button': 'Зарегистрироваться',
            'have_account': 'Уже зарегистрированы?',
            'login_link': 'Войти'
        },
        'admin': {
            'title': 'Админ-панель',
            'subtitle': 'Управляйте программами, наставниками, пользователями и посещаемостью в одном окне.',
            'courses': 'Курсы',
            'add_course': 'Добавить курс',
            'title_label': 'Название',
            'description': 'Описание',
            'duration': 'Продолжительность',
            'duration_placeholder': 'например, 12 недель',
            'price': 'Цена',
            'image_url': 'Ссылка на изображение',
            'teacher': 'Наставник',
            'select_teacher': 'Выберите наставника',
            'add_button': 'Добавить курс',
            'courses_empty': 'Пока нет курсов. Добавьте первый выше.',
            'edit': 'Редактировать',
            'delete': 'Удалить',
            'teachers': 'Наставники',
            'add_teacher': 'Добавить наставника',
            'name': 'Имя',
            'specialty': 'Специализация',
            'bio': 'Био',
            'add_teacher_button': 'Добавить наставника',
            'teachers_empty': 'Наставников пока нет.',
            'users': 'Пользователи',
            'id': 'ID',
            'username': 'Логин',
            'role': 'Роль',
            'users_empty': 'Пользователи не найдены.',
            'attendance': 'Учёт посещаемости',
            'status': 'Статус',
            'mark_present': 'Отметить присутствие',
            'mark_absent': 'Отметить отсутствие',
            'present': 'Присутствует',
            'absent': 'Отсутствует'
        },
        'dashboard': {
            'greeting': 'Привет, {username}!',
            'subtitle': 'Следите за прогрессом и уверенно двигайтесь к целям.',
            'profile': 'Профиль',
            'username': 'Логин',
            'role': 'Роль',
            'member_since': 'С нами с',
            'enrolled': 'Мои курсы',
            'none': 'Вы ещё не записаны ни на один курс.'
        },
        'footer': {
            'tagline': 'Помогаем развивать цифровые навыки и строить будущее вместе.',
            'quick_links': 'Быстрые ссылки',
            'contact': 'Контакты',
            'email': 'Email',
            'phone': 'Телефон',
            'address': 'Адрес',
            'rights': 'Все права защищены.'
        },
        'theme': {
            'toggle': 'Сменить тему'
        },
        'language': {
            'label': 'Язык',
            'current': 'Текущий язык'
        },
        'flash': {
            'login_required': 'Пожалуйста, войдите, чтобы продолжить.',
            'not_authorized': 'У вас нет доступа к этой странице.',
            'invalid_credentials': 'Неверный логин или пароль.',
            'logout': 'Вы вышли из аккаунта.',
            'welcome': 'С возвращением, {username}!',
            'account_created': 'Аккаунт создан! Теперь войдите.',
            'username_taken': 'Этот логин уже используется.',
            'password_mismatch': 'Пароли не совпадают.',
            'course_required': 'Все поля курса, кроме изображения, обязательны.',
            'price_numeric': 'Цена должна быть числом.',
            'course_created': 'Курс успешно создан.',
            'course_updated': 'Курс обновлён.',
            'course_deleted': 'Курс удалён.',
            'teacher_required': 'Имя, био и специализация обязательны.',
            'teacher_created': 'Профиль наставника создан.',
            'teacher_updated': 'Наставник обновлён.',
            'teacher_deleted': 'Наставник удалён.',
            'teacher_in_use': 'Нельзя удалить наставника с активными курсами.',
            'attendance_updated': 'Статус посещаемости обновлён.',
            'attendance_admin_forbidden': 'Учёт посещаемости доступен только для студентов.',
            'enroll_saved': 'Заявка получена! Мы скоро свяжемся с вами.',
            'student_added': 'Студент добавлен в группу.',
            'student_deleted': 'Студент удалён из группы.',
            'student_limit': 'В группе уже максимальное количество студентов (25).',
            'month_created': 'Месяц посещаемости сохранён.',
            'month_deleted': 'Месяц посещаемости удалён.',
            'enroll_status_updated': 'Статус заявки обновлён.'
        }
    }
}

LANGUAGE_OPTIONS = [
    {'code': 'uz', 'label': "O'zbek tili", 'flag': '🇺🇿'},
    {'code': 'en', 'label': 'English', 'flag': '🇬🇧'},
    {'code': 'ru', 'label': 'Русский', 'flag': '🇷🇺'}
]

COURSE_LOCALIZATIONS = {
    'en': {
        1: {
            'title': 'Full-Stack Web Development Bootcamp',
            'description': 'Ship production-ready web apps using HTML, CSS, JavaScript, and Python while mastering deployment best practices.',
            'duration': '16 weeks'
        },
        2: {
            'title': 'Data Science & Machine Learning',
            'description': 'Turn messy datasets into smart decisions using pandas, scikit-learn, and modern storytelling dashboards.',
            'duration': '14 weeks'
        },
        3: {
            'title': 'Cloud Infrastructure Architect',
            'description': 'Design secure multi-cloud systems with Terraform, CI/CD, and observability fundamentals.',
            'duration': '12 weeks'
        }
    },
    'uz': {
        1: {
            'title': "Full-stack veb dasturlash bootkampi",
            'description': "HTML, CSS, JavaScript va Python asosida haqiqiy loyihalarni ishlab, deploy jarayonlarini chuqur o'rganing.",
            'duration': '16 hafta'
        },
        2: {
            'title': 'Maʼlumotlar tahlili va AI',
            'description': "pandas va scikit-learn yordamida maʼlumotlardan yechim chiqarib, vizual tahlil vositalari bilan hikoya qilish.",
            'duration': '14 hafta'
        },
        3: {
            'title': 'Cloud infrastruktura arxitektori',
            'description': "Terraform, CI/CD va monitoring asosida xavfsiz multi-bulut infratuzilmalarini loyihalang.",
            'duration': '12 hafta'
        }
    },
    'ru': {
        1: {
            'title': 'Bootcamp по full-stack разработке',
            'description': 'Создавайте полноценные веб-приложения на HTML, CSS, JavaScript и Python, доводя их до продакшена.',
            'duration': '16 недель'
        },
        2: {
            'title': 'Data Science и машинное обучение',
            'description': 'Преобразуйте данные в инсайты с помощью pandas, scikit-learn и сторителлинга через визуализации.',
            'duration': '14 недель'
        },
        3: {
            'title': 'Архитектор облачной инфраструктуры',
            'description': 'Проектируйте безопасные облачные решения с Terraform, CI/CD и наблюдаемостью.',
            'duration': '12 недель'
        }
    }
}

TEACHER_LOCALIZATIONS = {
    'en': {
        1: {
            'bio': 'A decade of shipping SaaS platforms across fintech and edtech, with a passion for clean architecture and coaching.',
            'specialty': 'Full-stack Engineering'
        },
        2: {
            'bio': 'Transforms raw datasets into business intelligence with machine learning, analytics, and compelling dashboards.',
            'specialty': 'Data Science & AI'
        },
        3: {
            'bio': 'Guides teams through resilient cloud infrastructure, DevOps culture, and security best practices.',
            'specialty': 'Cloud Architecture'
        }
    },
    'uz': {
        1: {
            'bio': "Fintex va edtech loyihalarida 10 yillik tajribaga ega bo'lib, toza dasturlash va mentorlikka alohida e'tibor beradi.",
            'specialty': 'Full-stack dasturlash'
        },
        2: {
            'bio': "Data Science va AI orqali ko'plab ma'lumotlardan yechimlar chiqarishga o'rgatadi.",
            'specialty': 'Data Science & AI'
        },
        3: {
            'bio': "Cloud infratuzilmalari, DevOps madaniyati va xavfsizlik standartlari bo'yicha jamoalarni boshqaradi.",
            'specialty': 'Cloud arxitekturasi'
        }
    },
    'ru': {
        1: {
            'bio': 'Более 10 лет создаёт SaaS-платформы в финтехе и образовании, уделяя внимание архитектуре и наставничеству.',
            'specialty': 'Full-stack разработка'
        },
        2: {
            'bio': 'Преобразует данные в стратегии с помощью ML, аналитики и наглядных дашбордов.',
            'specialty': 'Data Science и AI'
        },
        3: {
            'bio': 'Настраивает надёжные облака, DevOps-процессы и стандарты безопасности для команд.',
            'specialty': 'Облачная архитектура'
        }
    }
}


# Helper functions
def get_language():
    lang = session.get('lang', 'uz')
    return lang if lang in TRANSLATIONS else 'uz'


def resolve_translation(language, key):
    parts = key.split('.')
    data = TRANSLATIONS.get(language, TRANSLATIONS['en'])
    default = TRANSLATIONS['en']

    for part in parts:
        if isinstance(data, dict) and part in data:
            data = data[part]
        else:
            data = None
            break

    for part in parts:
        if isinstance(default, dict) and part in default:
            default = default[part]
        else:
            default = None
            break

    return data if data is not None else default if default is not None else key


def translate(key, **kwargs):
    value = resolve_translation(get_language(), key)
    if isinstance(value, (list, tuple, dict)):
        return value
    if isinstance(value, str) and kwargs:
        try:
            return value.format(**kwargs)
        except KeyError:
            return value
    return value if isinstance(value, str) else key


def localized_course_field(course, field):
    lang = get_language()
    localized = COURSE_LOCALIZATIONS.get(lang, {}).get(course.id, {})
    return localized.get(field, getattr(course, field))


def course_title(course):
    return localized_course_field(course, 'title')


def course_description(course):
    return localized_course_field(course, 'description')


def course_duration(course):
    return localized_course_field(course, 'duration')


def localized_teacher_field(teacher, field):
    lang = get_language()
    localized = TEACHER_LOCALIZATIONS.get(lang, {}).get(teacher.id, {})
    return localized.get(field, getattr(teacher, field))


def teacher_bio(teacher):
    return localized_teacher_field(teacher, 'bio')


def teacher_specialty(teacher):
    return localized_teacher_field(teacher, 'specialty')


def lesson_dates(month):
    try:
        data = json.loads(month.lesson_dates or '[]')
        if isinstance(data, list):
            return data[:MAX_LESSONS_PER_MONTH]
    except json.JSONDecodeError:
        pass
    return []


def build_attendance_map(month):
    mapping = {}
    for record in month.records:
        mapping.setdefault(record.course_student_id, {})[record.lesson_index] = record.status
    return mapping


# Decorators
def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            flash(translate('flash.login_required'), 'warning')
            return redirect(url_for('login', next=request.url))
        return view_func(*args, **kwargs)
    return wrapped_view


def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash(translate('flash.not_authorized'), 'danger')
            return redirect(url_for('login', next=request.url))
        return view_func(*args, **kwargs)
    return wrapped_view


# Context processor
@app.context_processor
def inject_globals():
    return {
        'current_user': {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'role': session.get('role')
        },
        'current_year': datetime.now().year,
        't': translate,
        'languages': LANGUAGE_OPTIONS,
        'current_language': get_language(),
        'course_title': course_title,
        'course_description': course_description,
        'course_duration': course_duration,
        'teacher_bio': teacher_bio,
        'teacher_specialty': teacher_specialty,
        'lesson_dates': lesson_dates,
        'max_students': MAX_STUDENTS_PER_COURSE
    }


# Routes
@app.route('/set-language/<lang>')
def set_language(lang):
    if lang in TRANSLATIONS:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))


@app.route('/')
def index():
    featured_courses = Course.query.limit(3).all()
    highlighted_teachers = Teacher.query.limit(3).all()
    return render_template('index.html', courses=featured_courses, teachers=highlighted_teachers)


@app.route('/courses')
def courses():
    query = request.args.get('q', '', type=str).strip()
    if query:
        # Input validation - only allow alphanumeric and spaces
        if not all(c.isalnum() or c.isspace() for c in query):
            flash(translate('flash.invalid_credentials'), 'danger')
            return redirect(url_for('courses'))
        all_courses = Course.query.filter(Course.title.ilike(f"%{query}%")).all()
    else:
        all_courses = Course.query.all()
    return render_template('courses.html', courses=all_courses, search=query)


@app.route('/teachers')
def teachers():
    all_teachers = Teacher.query.all()
    return render_template('teachers.html', teachers=all_teachers)


@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Input validation
        if not username or not password:
            flash(translate('flash.invalid_credentials'), 'danger')
            return redirect(url_for('register'))

        if len(username) < 3 or len(username) > 80:
            flash('Username must be between 3 and 80 characters', 'danger')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash(translate('flash.password_mismatch'), 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash(translate('flash.username_taken'), 'danger')
            return redirect(url_for('register'))

        try:
            user = User(username=username, role='student')
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash(translate('flash.account_created'), 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash(translate('flash.invalid_credentials'), 'danger')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated', 'danger')
                return render_template('login.html')

            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session.permanent = True

            flash(translate('flash.welcome', username=user.username), 'success')
            next_page = request.args.get('next')

            if user.role == 'admin':
                return redirect(next_page or url_for('admin'))
            return redirect(next_page or url_for('dashboard'))

        flash(translate('flash.invalid_credentials'), 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash(translate('flash.logout'), 'info')
    return redirect(url_for('index'))


@app.route('/admin')
@admin_required
def admin():
    courses = Course.query.order_by(Course.title).all()
    teachers = Teacher.query.order_by(Teacher.name).all()
    users = User.query.order_by(User.role.desc(), User.username).all()
    enrollment_requests = EnrollmentRequest.query.order_by(EnrollmentRequest.created_at.desc()).all()

    course_months = {}
    for course in courses:
        months = AttendanceMonth.query.filter_by(course_id=course.id).order_by(AttendanceMonth.created_at.desc()).all()
        enriched_months = []
        for month in months:
            enriched_months.append({
                'object': month,
                'dates': lesson_dates(month),
                'attendance': build_attendance_map(month)
            })
        course_months[course.id] = enriched_months

    return render_template(
        'admin.html',
        courses=courses,
        teachers=teachers,
        users=users,
        enrollment_requests=enrollment_requests,
        course_months=course_months
    )


@app.route('/admin/courses/create', methods=['POST'])
@admin_required
def create_course():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    duration = request.form.get('duration', '').strip()
    price = request.form.get('price', '').strip()
    image_url = request.form.get('image_url', '').strip()
    teacher_id = request.form.get('teacher_id')

    if not all([title, description, duration, price, teacher_id]):
        flash(translate('flash.course_required'), 'danger')
        return redirect(url_for('admin'))

    try:
        price_value = float(price)
        if price_value < 0:
            raise ValueError("Price cannot be negative")
    except ValueError:
        flash(translate('flash.price_numeric'), 'danger')
        return redirect(url_for('admin'))

    try:
        course = Course(
            title=title,
            description=description,
            duration=duration,
            price=price_value,
            image_url=image_url or None,
            teacher_id=int(teacher_id)
        )
        db.session.add(course)
        db.session.commit()
        flash(translate('flash.course_created'), 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while creating the course', 'danger')

    return redirect(url_for('admin'))


@app.route('/admin/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    teachers = Teacher.query.order_by(Teacher.name).all()

    if request.method == 'POST':
        course.title = request.form.get('title', '').strip()
        course.description = request.form.get('description', '').strip()
        course.duration = request.form.get('duration', '').strip()

        try:
            course.price = float(request.form.get('price', course.price))
            if course.price < 0:
                raise ValueError("Price cannot be negative")
        except ValueError:
            flash(translate('flash.price_numeric'), 'danger')
            return redirect(request.url)

        course.image_url = request.form.get('image_url', '').strip() or None
        course.teacher_id = int(request.form.get('teacher_id'))

        try:
            db.session.commit()
            flash(translate('flash.course_updated'), 'success')
            return redirect(url_for('admin'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the course', 'danger')

    return render_template('edit_course.html', course=course, teachers=teachers)


@app.route('/admin/courses/<int:course_id>/delete', methods=['POST'])
@admin_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    try:
        db.session.delete(course)
        db.session.commit()
        flash(translate('flash.course_deleted'), 'info')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the course', 'danger')
    return redirect(url_for('admin'))


@app.route('/admin/teachers/create', methods=['POST'])
@admin_required
def create_teacher():
    name = request.form.get('name', '').strip()
    bio = request.form.get('bio', '').strip()
    specialty = request.form.get('specialty', '').strip()
    image_url = request.form.get('image_url', '').strip()

    if not all([name, bio, specialty]):
        flash(translate('flash.teacher_required'), 'danger')
        return redirect(url_for('admin'))

    try:
        teacher = Teacher(name=name, bio=bio, specialty=specialty, image_url=image_url or None)
        db.session.add(teacher)
        db.session.commit()
        flash(translate('flash.teacher_created'), 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while creating the teacher', 'danger')

    return redirect(url_for('admin'))


@app.route('/admin/teachers/<int:teacher_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)

    if request.method == 'POST':
        teacher.name = request.form.get('name', '').strip()
        teacher.bio = request.form.get('bio', '').strip()
        teacher.specialty = request.form.get('specialty', '').strip()
        teacher.image_url = request.form.get('image_url', '').strip() or None

        try:
            db.session.commit()
            flash(translate('flash.teacher_updated'), 'success')
            return redirect(url_for('admin'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the teacher', 'danger')

    return render_template('edit_teacher.html', teacher=teacher)


@app.route('/admin/teachers/<int:teacher_id>/delete', methods=['POST'])
@admin_required
def delete_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    if teacher.courses.count() > 0:
        flash(translate('flash.teacher_in_use'), 'danger')
        return redirect(url_for('admin'))

    try:
        db.session.delete(teacher)
        db.session.commit()
        flash(translate('flash.teacher_deleted'), 'info')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the teacher', 'danger')

    return redirect(url_for('admin'))


@app.route('/admin/enrollments/<int:request_id>/status', methods=['POST'])
@admin_required
def update_enrollment_status(request_id):
    enrollment = EnrollmentRequest.query.get_or_404(request_id)
    new_status = request.form.get('status', 'reviewed')

    # Validate status
    if new_status not in ['new', 'reviewed', 'approved', 'rejected']:
        flash('Invalid status', 'danger')
        return redirect(url_for('admin'))

    try:
        enrollment.status = new_status
        db.session.commit()
        flash(translate('flash.enroll_status_updated'), 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred', 'danger')

    return redirect(url_for('admin'))


@app.route('/admin/courses/<int:course_id>/students', methods=['POST'])
@admin_required
def add_course_student(course_id):
    course = Course.query.get_or_404(course_id)

    if course.students.count() >= MAX_STUDENTS_PER_COURSE:
        flash(translate('flash.student_limit'), 'danger')
        return redirect(url_for('admin'))

    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()
    notes = request.form.get('notes', '').strip()

    if not full_name or not phone:
        flash(translate('flash.invalid_credentials'), 'danger')
        return redirect(url_for('admin'))

    try:
        student = CourseStudent(course_id=course.id, full_name=full_name, phone=phone, notes=notes or None)
        db.session.add(student)
        db.session.commit()
        flash(translate('flash.student_added'), 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while adding the student', 'danger')

    return redirect(url_for('admin'))


@app.route('/admin/courses/<int:course_id>/students/<int:student_id>/delete', methods=['POST'])
@admin_required
def delete_course_student(course_id, student_id):
    Course.query.get_or_404(course_id)
    student = CourseStudent.query.get_or_404(student_id)

    try:
        db.session.delete(student)
        db.session.commit()
        flash(translate('flash.student_deleted'), 'info')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the student', 'danger')

    return redirect(url_for('admin'))


@app.route('/admin/attendance/months', methods=['POST'])
@admin_required
def create_attendance_month():
    course_id = request.form.get('course_id', type=int)
    month_label = request.form.get('month_label', '').strip()
    raw_dates = (request.form.get('lesson_dates', '') or '').replace('\r', '')

    course = Course.query.get_or_404(course_id)

    if not month_label or not raw_dates:
        flash(translate('flash.invalid_credentials'), 'danger')
        return redirect(url_for('admin'))

    temp = raw_dates.replace(',', '\n')
    dates = [line.strip() for line in temp.split('\n') if line.strip()]
    dates = dates[:MAX_LESSONS_PER_MONTH]

    try:
        month = AttendanceMonth(course_id=course.id, month_label=month_label, lesson_dates=json.dumps(dates))
        db.session.add(month)
        db.session.commit()
        flash(translate('flash.month_created'), 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while creating the attendance month', 'danger')

    return redirect(url_for('admin'))


@app.route('/admin/attendance/months/<int:month_id>/delete', methods=['POST'])
@admin_required
def delete_attendance_month(month_id):
    month = AttendanceMonth.query.get_or_404(month_id)

    try:
        db.session.delete(month)
        db.session.commit()
        flash(translate('flash.month_deleted'), 'info')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the attendance month', 'danger')

    return redirect(url_for('admin'))


@app.route('/admin/attendance/toggle', methods=['POST'])
@admin_required
def toggle_attendance():
    month_id = request.form.get('month_id', type=int)
    student_id = request.form.get('student_id', type=int)
    lesson_index = request.form.get('lesson_index', type=int)

    month = AttendanceMonth.query.get_or_404(month_id)
    CourseStudent.query.get_or_404(student_id)

    try:
        record = AttendanceRecord.query.filter_by(
            month_id=month.id,
            course_student_id=student_id,
            lesson_index=lesson_index
        ).first()

        if record is None:
            record = AttendanceRecord(
                month_id=month.id,
                course_student_id=student_id,
                lesson_index=lesson_index,
                status='+'
            )
            db.session.add(record)
        elif record.status == '+':
            record.status = '-'
        elif record.status == '-':
            db.session.delete(record)

        db.session.commit()
        flash(translate('flash.attendance_updated'), 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating attendance', 'danger')

    return redirect(url_for('admin'))


@app.route('/courses/enroll', methods=['POST'])
@limiter.limit("3 per hour")
def enroll_course():
    course_id = request.form.get('course_id', type=int)
    course = Course.query.get_or_404(course_id) if course_id else None

    if course is None:
        flash(translate('flash.invalid_credentials'), 'danger')
        return redirect(request.referrer or url_for('courses'))

    if 'user_id' not in session:
        flash(translate('flash.login_required'), 'warning')
        return redirect(url_for('login', next=request.referrer or url_for('courses')))

    full_name = request.form.get('full_name', '').strip()
    age_raw = request.form.get('age', '').strip()
    experience = request.form.get('experience', '').strip()
    phone = request.form.get('phone', '').strip()

    if not full_name or not phone:
        flash(translate('flash.invalid_credentials'), 'danger')
        return redirect(request.referrer or url_for('courses'))

    # Validate phone number format
    if not all(c.isdigit() or c in '+- ()' for c in phone):
        flash('Invalid phone number format', 'danger')
        return redirect(request.referrer or url_for('courses'))

    try:
        age_value = int(age_raw) if age_raw else None
        if age_value and (age_value < 10 or age_value > 80):
            raise ValueError("Age out of range")
    except ValueError:
        age_value = None

    try:
        enrollment = EnrollmentRequest(
            user_id=session.get('user_id'),
            course_id=course.id,
            full_name=full_name,
            age=age_value,
            experience=experience or None,
            phone=phone,
            status='new'
        )
        db.session.add(enrollment)
        db.session.commit()
        flash(translate('flash.enroll_saved'), 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while submitting your enrollment', 'danger')

    return redirect(request.referrer or url_for('courses'))


@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    enrolled_courses = Course.query.limit(2).all() if user.role != 'admin' else []
    return render_template('dashboard.html', user=user, enrolled_courses=enrolled_courses)


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500


@app.errorhandler(429)
def ratelimit_handler(e):
    flash('Too many requests. Please try again later.', 'warning')
    return redirect(request.referrer or url_for('index'))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() in {'1', 'true', 'yes'}
    app.run(host='0.0.0.0', port=port, debug=debug)
