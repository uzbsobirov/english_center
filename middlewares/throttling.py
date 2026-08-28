import time
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

logger = logging.getLogger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    """
    Spam va flood hujumlaridan himoya qiluvchi middleware (TZ 18).
    """
    def __init__(self, rate_limit: float = 0.5):
        self.rate_limit = rate_limit
        self.user_timestamps: Dict[int, float] = {}
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if not user:
            return await handler(event, data)

        now = time.time()
        last_time = self.user_timestamps.get(user.id, 0.0)

        if now - last_time < self.rate_limit:
            logger.warning(f"⛔️ Throttled: {user.id} - too many requests")
            return

        self.user_timestamps[user.id] = now
        return await handler(event, data)

