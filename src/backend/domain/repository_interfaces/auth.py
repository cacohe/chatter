from abc import ABC, abstractmethod


class IAuthRepository(ABC):
    @abstractmethod
    def create_user(self, email, password, username):
        pass

    @abstractmethod
    def authenticate(self, email, password):
        pass

    @abstractmethod
    def get_user_by_token(self, token):
        pass

    @abstractmethod
    def sign_out(self):
        pass

    @abstractmethod
    def update_user(self, user_id: str, key: str, value: str):
        pass
