"""FastAPI Depends 工厂：每个路由注入对应的应用层用例。"""

from app.services.chat.get_history import GetChatHistory
from app.services.chat.start_new_chat import StartNewChat
from app.services.chat.stream import StreamChat
from app.services.knowledge.delete_document import DeleteDocument
from app.services.knowledge.get_summary import GetSummary
from app.services.knowledge.ingest_web import IngestWeb
from app.services.knowledge.list_chunks import ListChunks
from app.services.knowledge.sync_database import SyncDatabase
from app.services.knowledge.upload_files import UploadFiles


def get_stream_chat() -> StreamChat:
    return StreamChat()


def get_start_new_chat() -> StartNewChat:
    return StartNewChat()


def get_chat_history() -> GetChatHistory:
    return GetChatHistory()


def get_knowledge_summary() -> GetSummary:
    return GetSummary()


def get_upload_files() -> UploadFiles:
    return UploadFiles()


def get_sync_database() -> SyncDatabase:
    return SyncDatabase()


def get_ingest_web() -> IngestWeb:
    return IngestWeb()


def get_delete_document() -> DeleteDocument:
    return DeleteDocument()


def get_list_chunks() -> ListChunks:
    return ListChunks()
