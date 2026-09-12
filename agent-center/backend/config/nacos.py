"""封装 Nacos 配置中心和服务发现客户端。"""

from nacos import NacosClient

from backend.config.settings import (
    NACOS_CONFIG_GROUP,
    NACOS_CONFIG_NAMESPACE,
    NACOS_DISCOVERY_IP,
    NACOS_DISCOVERY_NAME,
    NACOS_DISCOVERY_NAMESPACE,
    NACOS_PASSWORD,
    NACOS_SERVER_ADDR,
    NACOS_USERNAME,
    config_manager,
)


class NacosConfig:
    """管理 Nacos 配置中心和服务发现客户端。"""

    def __init__(self):
        """根据应用配置初始化配置中心与服务发现客户端。"""

        self._server_addr = config_manager.get(NACOS_SERVER_ADDR)
        self._config_group = config_manager.get(NACOS_CONFIG_GROUP, "DEFAULT_GROUP")
        self._discovery_group = config_manager.get("nacos.discovery.group", "DEFAULT_GROUP")
        self._discovery_ip = config_manager.get(NACOS_DISCOVERY_IP, "127.0.0.1")
        self._discovery_name = config_manager.get(NACOS_DISCOVERY_NAME, "default_server_name")

        client_options = {
            "server_addresses": "http://" + self._server_addr,
            "username": config_manager.get(NACOS_USERNAME, "nacos"),
            "password": config_manager.get(NACOS_PASSWORD, "nacos"),
            "logDir": "logs/",
        }
        # 配置中心与服务发现可使用不同命名空间，因此分别维护客户端。
        self._config_client = NacosClient(
            namespace=config_manager.get(NACOS_CONFIG_NAMESPACE, "public"),
            **client_options,
        )
        self._discovery_client = NacosClient(
            namespace=config_manager.get(NACOS_DISCOVERY_NAMESPACE, "public"),
            **client_options,
        )
        # 禁用本地快照，确保读取结果直接来自当前 Nacos 服务。
        self._config_client.no_snapshot = True
        self._discovery_client.no_snapshot = True

    def load_config(self, data_id: str) -> str:
        """读取指定配置。"""

        return self._config_client.get_config(
            data_id=data_id,
            group=self._config_group,
            timeout=10,
        )

    def get_config_client(self) -> NacosClient:
        """返回配置中心客户端。"""

        return self._config_client

    def get_discovery_client(self) -> NacosClient:
        """返回服务发现客户端。"""

        return self._discovery_client

    def get_discovery_ip(self) -> str:
        """返回当前服务注册使用的 IP。"""

        return self._discovery_ip

    def get_discovery_name(self) -> str:
        """返回当前服务注册使用的服务名。"""

        return self._discovery_name

    def get_discovery_group(self) -> str:
        """返回当前服务注册使用的分组。"""

        return self._discovery_group


# 模块内共享同一组 Nacos 客户端配置。
nacos_config = NacosConfig()
