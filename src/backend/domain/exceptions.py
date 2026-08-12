class BusinessException(Exception):
    """所有业务异常的基类"""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
