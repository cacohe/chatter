from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """基础Repository类，提供通用的CRUD操作"""

    def __init__(self, model: Type[ModelType], db: Session):
        """
        初始化Repository

        Args:
            model: SQLAlchemy模型类
            db: 数据库会话
        """
        self.model = model
        self.db = db

    def get_by_id(self, id: int) -> Optional[ModelType]:
        """根据ID获取对象"""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """获取所有对象（分页）"""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, **kwargs) -> ModelType:
        """创建新对象"""
        db_obj = self.model(**kwargs)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """更新对象"""
        db_obj = self.get_by_id(id)
        if db_obj:
            for key, value in kwargs.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> bool:
        """删除对象"""
        db_obj = self.get_by_id(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False

    def count(self) -> int:
        """统计对象数量"""
        return self.db.query(self.model).count()
