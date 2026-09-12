import random
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.orm import scoped_session

from config import config_manager, get_id, logger
from dao.BaseDAO import BaseDAO
from dao.pojo import ChatSession
from dao.vo.SessionVO import Example, SessionVO


@dataclass
class ChatSessionVO:
    """历史会话展示对象。"""

    session_id: str
    title: str
    update_time: datetime


TODAY = "当天"
LAST_30_DAYS = "最近30天"
LAST_YEAR = "最近1年"
MORE_THAN_YEAR = "1年以上"

SUCCESS_MESSAGE = {"status": "ok"}
NO_CHANGE_MESSAGE = {"status": "ok", "message": "No change"}


class ChatSessionDAO(BaseDAO):
    """
    ChatSession 数据访问对象（DAO）。

    提供功能：
    1. 创建聊天会话
    2. 查询历史会话并按时间分组
    3. 更新会话标题
    4. 删除历史会话
    """

    def create_session(self, num: int, agent_id: int, user_id: int) -> SessionVO:
        """
        创建新的聊天会话，并随机选取示例。

        Args:
            num (int): 随机选取的示例数量
            agent_id (int): 智能体 ID
            user_id (int): 用户 ID

        Returns:
            SessionVO: 会话数据对象，包括示例列表
        """
        logger.debug("开始创建新的 ChatSession（示例数量: %d）", num)

        def _create(session: scoped_session):
            # 创建并保存新的聊天会话
            chat_session = ChatSession(
                id=get_id(),  # 全局唯一ID
                session_id=uuid.uuid4().hex,  # 会话UUID
                user_id=user_id,
                agent_id=agent_id
            )
            session.add(chat_session)  # 添加到数据库 session
            logger.debug("ChatSession 已创建：id=%s, session_id=%s", chat_session.id, chat_session.session_id)

            # 构建 SessionVO 返回对象
            session_vo = SessionVO(
                sessionId=chat_session.session_id,
                title=config_manager.get(f"ai.{agent_id}.session.title"),
                describe=config_manager.get(f"ai.{agent_id}.session.describe"),
                examples=self.hot_examples(num, agent_id)
            ) # not

            logger.debug("ChatSession 创建成功，session_id=%s", chat_session.session_id)
            logger.info("聊天会话创建成功")
            return session_vo

        return self._execute(_create)

    def hot_examples(self, num: int = 3, agent_id: int = 1001):
        """
        获取随机示例。

        Args:
            num (int): 选取示例数量
            agent_id (int): 智能体ID，用于读取配置示例列表

        Returns:
            list[Example]: 随机选取的示例列表
        """
        examples = config_manager.get(f"ai.{agent_id}.session.examples", [])
        selected_examples = random.sample(examples, min(num, len(examples)))
        logger.info("获取随机示例成功")
        return [
            Example(title=e.get("title"), describe=e.get("describe"))

            for e in selected_examples
        ]

    def update_title(self, session_id: str, agent_id: int, title: str):
        """首次提问时设置标题，并刷新会话更新时间。"""

        def _update(session: scoped_session):
            stmt = (
                select(ChatSession)
                .where(ChatSession.session_id == session_id)  # type: ignore
                .where(ChatSession.agent_id == agent_id)
            )
            chat_session = session.execute(stmt).scalars().first()
            if chat_session is None:
                return NO_CHANGE_MESSAGE

            if not chat_session.title and title:
                chat_session.title = title[:100]

            chat_session.update_time = datetime.now()
            return SUCCESS_MESSAGE

        return self._execute(_update)

    def query_history_session(self, agent_id: int, user_id: int):
        """查询最近 30 条历史会话，并按更新时间分组。"""

        def _query(session: scoped_session):
            stmt = (
                select(ChatSession)
                .where(ChatSession.agent_id == agent_id)  # type: ignore
                .where(ChatSession.user_id == user_id)
                .where(ChatSession.title.isnot(None))
                .order_by(ChatSession.update_time.desc())
                .limit(30)
            )
            chat_sessions = session.execute(stmt).scalars().all()
            if not chat_sessions:
                return {}

            groups = defaultdict(list)
            today = date.today()
            for chat_session in chat_sessions:
                item = ChatSessionVO(
                    session_id=chat_session.session_id,
                    title=chat_session.title,
                    update_time=chat_session.update_time,
                )
                days = abs((today - item.update_time.date()).days)
                if days == 0:
                    key = TODAY
                elif days <= 30:
                    key = LAST_30_DAYS
                elif days <= 365:
                    key = LAST_YEAR
                else:
                    key = MORE_THAN_YEAR
                groups[key].append(item)

            order = [MORE_THAN_YEAR, LAST_YEAR, LAST_30_DAYS, TODAY]
            return {key: groups[key] for key in order if key in groups}

        return self._execute(_query)

    def delete_history_session(
        self,
        agent_id: int,
        user_id: int,
        session_id: str,
    ):
        """物理删除指定历史会话。"""

        def _delete(session: scoped_session):
            stmt = (
                delete(ChatSession)
                .where(ChatSession.agent_id == agent_id)  # type: ignore
                .where(ChatSession.user_id == user_id)
                .where(ChatSession.session_id == session_id)
            )
            result = session.execute(stmt)
            return (
                SUCCESS_MESSAGE
                if result.rowcount > 0
                else NO_CHANGE_MESSAGE
            )

        return self._execute(_delete)

    def update_history_session(
        self,
        agent_id: int,
        user_id: int,
        session_id: str,
        title: str,
    ):
        """更新指定历史会话标题。"""

        def _update(session: scoped_session):
            stmt = (
                update(ChatSession)
                .where(ChatSession.agent_id == agent_id)  # type: ignore
                .where(ChatSession.user_id == user_id)
                .where(ChatSession.session_id == session_id)
                .values(title=title[:100])
            )
            result = session.execute(stmt)
            return (
                SUCCESS_MESSAGE
                if result.rowcount > 0
                else NO_CHANGE_MESSAGE
            )

        return self._execute(_update)


# 全局 ChatSessionDAO 实例
chat_session_dao = ChatSessionDAO()
