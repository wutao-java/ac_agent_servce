import random
import uuid

from sqlalchemy.orm import scoped_session

from config import config_manager, get_id, logger
from dao.BaseDAO import BaseDAO
from dao.pojo import ChatSession
from dao.vo.SessionVO import Example, SessionVO


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


# 全局 ChatSessionDAO 实例
chat_session_dao = ChatSessionDAO()
