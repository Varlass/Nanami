from .render_factory import Message


class MessageManager:
    def __init__(self, message: Message):
        self.message: Message = message
        self.pages: list[dict] = []