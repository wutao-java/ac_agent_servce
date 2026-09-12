import redis

from config.ConfigManager import config_manager


class RedisConfig:
    """Redis 客户端配置。"""

    def __init__(self):
        self._redis = redis.Redis(
            host=config_manager.get("redis.host", "127.0.0.1"),
            port=int(config_manager.get("redis.port", 6379)),
            password=config_manager.get("redis.password"),
            decode_responses=True,
        )

    def get_instance(self) -> redis.Redis:
        return self._redis


redis_config = RedisConfig()
