from typing import Dict, Any

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    ValidationError,
    model_validator,
    ConfigDict,
)


# --- 自定义错误消息类 ---
class ValidationResult:
    def __init__(self, is_valid: bool, errors: Dict[str, str] = None, data: Any = None):
        self.is_valid = is_valid
        self.errors = errors or {}
        self.data = data


# --- 错误消息映射 ---
PYDANTIC_ERROR_MAPPING = {
    "value is not a valid email address": "请输入有效的邮箱地址",
    "string should have at least": "字符数不足",
    "string should have at most": "字符数超出限制",
    "string should have at least 1 character": "密码不能为空",
    "string should have at least 4 characters": "用户名至少需要4个字符",
    "string should have at least 8 characters": "密码至少需要8个字符",
}


def _translate_error(msg: str) -> str:
    """将 Pydantic 英文错误消息转换为中文"""
    msg_lower = msg.lower()
    for eng, chi in PYDANTIC_ERROR_MAPPING.items():
        if eng in msg_lower:
            if "email" in msg_lower:
                return "请输入有效的邮箱地址"
            if "username" in msg_lower or "at least 4" in msg_lower:
                return "用户名至少需要4个字符"
            if "password" in msg_lower:
                if "at least 1" in msg_lower:
                    return "密码不能为空"
                if "at least 8" in msg_lower:
                    return "密码至少需要8个字符"
            return chi
    return msg.replace("Value error, ", "")


# --- Pydantic 模型定义 ---
class UserRegisterSchema(BaseModel):
    """
    用户注册验证模型。
    使用 Pydantic 内置的 EmailStr 和 Field 约束。
    """

    username: str = Field(
        ...,
        min_length=4,
        max_length=20,
        description="用户名长度必须在 4-20 字符之间",
        frozen=True,
    )
    email: EmailStr = Field(
        ...,
        description="必须是有效的邮件地址",
        frozen=True,
    )
    password: str = Field(
        ...,
        min_length=8,
        description="密码至少8位",
        frozen=True,
    )
    confirm_password: str = Field(
        ...,
        description="确认密码",
        frozen=True,
    )

    model_config = ConfigDict(frozen=True)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("用户名只能包含字母、数字、下划线或连字符")
        return v

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if not any(char.isdigit() for char in v):
            raise ValueError("密码必须包含至少一个数字")
        if not any(char.isupper() for char in v):
            raise ValueError("密码必须包含至少一个大写字母")
        return v

    @model_validator(mode="after")
    def check_passwords_match(self) -> "UserRegisterSchema":
        if self.password != self.confirm_password:
            raise ValueError("两次输入的密码不一致")
        return self


class UserLoginSchema(BaseModel):
    """
    用户登录验证模型。
    """

    email: EmailStr = Field(
        ...,
        description="必须是有效的邮件地址",
        frozen=True,
    )
    password: str = Field(
        ...,
        min_length=1,
        description="密码不能为空",
        frozen=True,
    )

    model_config = ConfigDict(frozen=True)

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("密码不能为空")
        return v


# --- 验证器工厂/工具函数 ---
class AuthValidator:
    """生产级验证器封装"""

    @staticmethod
    def validate_registration(data: Dict[str, Any]) -> ValidationResult:
        try:
            user = UserRegisterSchema(**data)
            return ValidationResult(is_valid=True, data=user)
        except ValidationError as e:
            friendly_errors = {
                err["loc"][0]: _translate_error(err["msg"]) for err in e.errors()
            }
            return ValidationResult(is_valid=False, errors=friendly_errors)

    @staticmethod
    def validate_login(data: Dict[str, Any]) -> ValidationResult:
        try:
            login_data = UserLoginSchema(**data)
            return ValidationResult(is_valid=True, data=login_data)
        except ValidationError as e:
            friendly_errors = {
                err["loc"][0]: _translate_error(err["msg"]) for err in e.errors()
            }
            return ValidationResult(is_valid=False, errors=friendly_errors)
