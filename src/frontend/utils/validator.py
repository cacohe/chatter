from typing import Dict, Any

from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationError, model_validator


# --- 自定义错误消息类 ---
class ValidationResult:
    def __init__(self, is_valid: bool, errors: Dict[str, str] = None, data: Any = None):
        self.is_valid = is_valid
        self.errors = errors or {}
        self.data = data


# --- Pydantic 模型定义 ---
class UserRegisterSchema(BaseModel):
    """
    用户注册验证模型。
    使用 Pydantic 内置的 EmailStr 和 Field 约束。
    """
    username: str = Field(
        ..., min_length=4, max_length=20,
        description="用户名长度必须在 4-20 字符之间"
    )
    email: EmailStr = Field(..., description="必须是有效的邮件地址")
    password: str = Field(..., min_length=8, description="密码至少8位")
    confirm_password: str = Field(...)

    # --- 自定义逻辑验证 ---
    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v

    @field_validator('password')
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if not any(char.isdigit() for char in v):
            raise ValueError('密码必须包含至少一个数字')
        if not any(char.isupper() for char in v):
            raise ValueError('密码必须包含至少一个大写字母')
        return v

    # --- 跨字段验证 (Root Validator) ---
    @model_validator(mode='after')
    def check_passwords_match(self) -> 'UserRegisterSchema':
        if self.password != self.confirm_password:
            raise ValueError("两次输入的密码不一致")
        return self


# --- 验证器工厂/工具函数 ---
class AuthValidator:
    """生产级验证器封装"""

    @staticmethod
    def validate_registration(data: Dict[str, Any]) -> ValidationResult:
        try:
            user = UserRegisterSchema(**data)
            return ValidationResult(is_valid=True, data=user)
        except ValidationError as e:
            # 转换 Pydantic 的错误格式为简单的 Dict[字段名, 错误信息]
            friendly_errors = {
                err['loc'][0]: err['msg'].replace("Value error, ", "")
                for err in e.errors()
            }
            return ValidationResult(is_valid=False, errors=friendly_errors)