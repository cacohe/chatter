import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime


# --- 基础模型（共享字段） ---
class UserBase(BaseModel):
    email: EmailStr = Field(..., description="用户的电子邮箱")
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="用户名",
        examples=["john_doe", "johnDoe123"],
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("用户名只能包含字母、数字、下划线或连字符")
        return v


# --- 注册相关 (Register) ---
class UserCreate(UserBase):
    """用户注册请求模型"""

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="密码至少8位，需包含数字和大小写字母",
        examples=["Password123"],
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含至少一个数字")
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not any(c.islower() for c in v):
            raise ValueError("密码必须包含至少一个小写字母")
        return v


# --- 个人信息 (User Profile) ---
class UserInfo(UserBase):
    """获取当前登录用户信息时的响应模型"""

    id: uuid.UUID
    avatar_url: Optional[str] = None
    role_level: int = 1
    created_at: datetime = datetime.utcnow()
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserRegisterResponse(BaseModel):
    """用户注册成功后的响应模型"""

    id: uuid.UUID
    email: EmailStr
    username: str | None
    created_at: datetime = datetime.utcnow()

    model_config = ConfigDict(
        from_attributes=True,  # 允许从 SQLAlchemy 模型直接转化
    )


# --- 登录相关 (Login) ---
class LoginRequest(BaseModel):
    """登录请求模型"""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user_info: Optional[UserInfo] = None


# --- 退出登录 (Logout) ---
class LogoutResponse(BaseModel):
    """退出登录后的统一响应格式"""

    message: str = "Successfully logged out"


# --- 更新用户信息 (Update User) ---
class UserUpdate(BaseModel):
    """用户更新请求模型"""

    key: str = Field(..., description="要更新的字段名")
    value: str = Field(..., description="要更新的值")
