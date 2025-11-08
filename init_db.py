"""
Initialize database with secure password hashing
"""
from app_secure import app, db, User, Teacher, Course, bcrypt


def seed_data():
    """Seed database with initial data"""
    print("Creating tables...")
    db.create_all()

    print("Seeding data...")

    # Create admin user with hashed password
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='admin', is_active=True)
        admin.set_password('admin123')  # Change this password in production!
        db.session.add(admin)
        print("✓ Admin user created (username: admin, password: admin123)")

    # Create test student
    if not User.query.filter_by(username='student').first():
        student = User(username='student', role='student', is_active=True)
        student.set_password('student123')
        db.session.add(student)
        print("✓ Student user created (username: student, password: student123)")

    # Create teachers
    if Teacher.query.count() == 0:
        teachers = [
            Teacher(
                name='Dilshod Karimov',
                bio='Full-stack engineer with 10+ years of experience building scalable SaaS products across fintech and education.',
                specialty='Full-Stack Development',
                image_url='https://images.unsplash.com/photo-1544723795-3fb6469f5b39?auto=format&fit=crop&w=400&q=80'
            ),
            Teacher(
                name='Aziza Rakhmonova',
                bio='Data scientist focused on turning raw data into actionable insights using machine learning and visualization tools.',
                specialty='Data Science & AI',
                image_url='https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=400&q=80'
            ),
            Teacher(
                name='Timur Valiev',
                bio='Cloud solutions architect guiding teams to deploy resilient, secure infrastructure across AWS and Azure.',
                specialty='Cloud Engineering',
                image_url='https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=400&q=80'
            ),
        ]
        db.session.add_all(teachers)
        db.session.flush()
        print(f"✓ Created {len(teachers)} teachers")

        # Create courses
        courses = [
            Course(
                title='Full-Stack Web Development Bootcamp',
                description='Master HTML, CSS, JavaScript, and Python by building real-world applications with modern best practices.',
                duration='16 weeks',
                price=1299.00,
                image_url='https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=800&q=80',
                teacher_id=teachers[0].id
            ),
            Course(
                title='Data Science & Machine Learning',
                description='Learn data wrangling, visualization, and predictive modeling using Python, pandas, and scikit-learn.',
                duration='14 weeks',
                price=1499.00,
                image_url='https://images.unsplash.com/photo-1545239351-1141bd82e8a6?auto=format&fit=crop&w=800&q=80',
                teacher_id=teachers[1].id
            ),
            Course(
                title='Cloud Infrastructure Architect',
                description='Design, deploy, and maintain cloud-native infrastructure leveraging Infrastructure as Code and DevOps workflows.',
                duration='12 weeks',
                price=1599.00,
                image_url='https://images.unsplash.com/photo-1517430816045-df4b7de11d1d?auto=format&fit=crop&w=800&q=80',
                teacher_id=teachers[2].id
            ),
        ]
        db.session.add_all(courses)
        print(f"✓ Created {len(courses)} courses")

    db.session.commit()
    print("\n✅ Database initialized successfully!")
    print("\nDefault credentials:")
    print("  Admin:   username='admin'   password='admin123'")
    print("  Student: username='student' password='student123'")
    print("\n⚠️  IMPORTANT: Change these passwords in production!")


def init_db():
    """Initialize database"""
    with app.app_context():
        print("Dropping existing tables...")
        db.drop_all()
        seed_data()


if __name__ == '__main__':
    init_db()
