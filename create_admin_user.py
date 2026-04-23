from app.core.security import hash_password
from app.db.session import SessionLocal, init_db
from app.db.models import User

# 初始化数据库
init_db()

# 创建数据库会话
db = SessionLocal()

try:
    # 检查是否已存在admin用户
    existing_user = db.query(User).filter(User.username == "admin").first()
    if existing_user:
        print("Admin user already exists")
    else:
        # 创建新的admin用户
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=hash_password("admin123")
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print("Admin user created successfully")
finally:
    db.close()
