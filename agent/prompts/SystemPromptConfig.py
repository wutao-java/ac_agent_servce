import hashlib
import hmac
import threading
import time
from dataclasses import dataclass, field

from common import *
from config import config_manager, logger, nacos_config


def md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


@dataclass
class SystemPromptConfig:
    """从 Nacos 读取系统提示词，并通过轮询支持热更新。"""

    _values: dict = field(default_factory=lambda: {
        "chat_route_message": "",
        "chat_recommend_message": "",
        "chat_buy_message": "",
        "chat_consult_message": "",
        "chat_knowledge_message": "",
        "chat_unknown_message": "",
        "chat_text_message": "",
    })
    _config_map: dict = field(default_factory=lambda: {
        PROMPT_ROUTE_CHAT_DATA_ID: "chat_route_message",
        PROMPT_RECOMMEND_CHAT_DATA_ID: "chat_recommend_message",
        PROMPT_BUY_CHAT_DATA_ID: "chat_buy_message",
        PROMPT_CONSULT_CHAT_DATA_ID: "chat_consult_message",
        PROMPT_KNOWLEDGE_CHAT_DATA_ID: "chat_knowledge_message",
        PROMPT_UNKNOWN_CHAT_DATA_ID: "chat_unknown_message",
        PROMPT_TEXT_CHAT_DATA_ID: "chat_text_message",
    })
    _snapshots: dict = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _start_lock: threading.Lock = field(default_factory=threading.Lock)
    _started: bool = False

    def __post_init__(self):
        self.client = nacos_config.get_config_client()
        self.group = config_manager.get(NACOS_CONFIG_GROUP, "DEFAULT_GROUP")

    def start(self):
        with self._start_lock:
            if self._started:
                return

            self.load_all_configs()
            threading.Thread(target=self._watch_loop, daemon=True).start()
            self._started = True
            logger.info("[HOT-UPDATE] 系统提示词热更新线程已启动")

    def load_all_configs(self):
        for data_id_key, attr_name in self._config_map.items():
            data_id = config_manager.get(data_id_key)
            if not data_id:
                logger.warning("[INIT] 未配置系统提示词 data-id: %s", data_id_key)
                continue
            self._load_single(data_id, attr_name)

    def _load_single(self, data_id: str, attr_name: str):
        try:
            value = self.client.get_config(data_id, self.group, timeout=5) or ""
            with self._lock:
                self._values[attr_name] = value
                self._snapshots[data_id] = md5(value)
            logger.info("[INIT] 系统提示词加载成功: %s", data_id)
        except Exception as exc:
            logger.error("[INIT] 系统提示词加载失败 %s: %s", data_id, exc)

    def _watch_loop(self):
        while True:
            time.sleep(60)
            self._check_updates()

    def _check_updates(self):
        for data_id_key, attr_name in self._config_map.items():
            data_id = config_manager.get(data_id_key)
            if not data_id:
                continue

            try:
                new_value = self.client.get_config(data_id, self.group, timeout=5) or ""
                new_md5 = md5(new_value)
                if not hmac.compare_digest(self._snapshots.get(data_id, ""), new_md5):
                    with self._lock:
                        self._values[attr_name] = new_value
                        self._snapshots[data_id] = new_md5
                    logger.warning("[HOT-UPDATE] 系统提示词发现变更: %s -> %s", data_id, attr_name)
            except Exception as exc:
                logger.error("[HOT-UPDATE] 系统提示词检查失败 %s: %s", data_id, exc)

    def _get_message(self, attr_name: str) -> str:
        if not self._started:
            self.start()
        with self._lock:
            return self._values.get(attr_name, "")

    @property
    def chat_route_message(self) -> str:
        return self._get_message("chat_route_message")

    @property
    def chat_recommend_message(self) -> str:
        return self._get_message("chat_recommend_message")

    @property
    def chat_buy_message(self) -> str:
        return self._get_message("chat_buy_message")

    @property
    def chat_consult_message(self) -> str:
        return self._get_message("chat_consult_message")

    @property
    def chat_knowledge_message(self) -> str:
        return self._get_message("chat_knowledge_message")

    @property
    def chat_unknown_message(self) -> str:
        return self._get_message("chat_unknown_message")

    @property
    def chat_text_message(self) -> str:
        return self._get_message("chat_text_message")


system_prompt_config = SystemPromptConfig()
