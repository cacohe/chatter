from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from src.config import settings
from src.backend.models.user import Base as UserBase

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,  # 连接池检查
    pool_size=5,
    max_overflow=10
)

# 创建Session工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖注入函数

    使用方式:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库表"""
    # 导入所有模型以确保它们被注册到Base.metadata中
    from src.backend.models.user import User
    from src.backend.models.session import ChatSession
    from src.backend.models.message import Message

    # 创建所有表
    UserBase.metadata.create_all(bind=engine)
    print("数据库表创建成功")


def drop_db():
    """删除所有数据库表（谨慎使用）"""
    from src.backend.models.user import User
    from src.backend.models.session import ChatSession
    from src.backend.models.message import Message

    UserBase.metadata.drop_all(bind=engine)
    print("数据库表已删除")
