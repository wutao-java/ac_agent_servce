"""集中定义 application.yml 使用的配置键路径。"""

# 服务配置
SERVER_PORT = "server.port"
SERVER_HOST = "server.host"
SERVER_LOGGER_FILE = "server.logger.file"
SERVER_LOGGER_LEVEL = "server.logger.level"

# 模型配置
AI_OPENAI_MODEL = "ai.openai.model"
AI_OPENAI_API_KEY = "ai.openai.api-key"
AI_OPENAI_BASE_URL = "ai.openai.base-url"
AI_OPENAI_TEMPERATURE = "ai.openai.temperature"
AI_OPENAI_TIMEOUT = "ai.openai.timeout"

# LangGraph 检查点配置
AI_AGENT_CHECKPOINTER_POSTGRES_MIN = "ai.agent.checkpointer.postgres.min"
AI_AGENT_CHECKPOINTER_POSTGRES_MAX = "ai.agent.checkpointer.postgres.max"
AI_AGENT_CHECKPOINTER_POSTGRES_URL = "ai.agent.checkpointer.postgres.url"

# 电商后端配置
ECOMMERCE_BASE_URL = "ecommerce.base-url"
ECOMMERCE_SERVICE_TOKEN = "ecommerce.service-token"
ECOMMERCE_CONNECT_TIMEOUT = "ecommerce.connect-timeout"
ECOMMERCE_READ_TIMEOUT = "ecommerce.read-timeout"

# 网关接入前，Nacos 配置保持隔离，不参与服务启动。
NACOS_SERVER_ADDR = "nacos.server-addr"
NACOS_USERNAME = "nacos.username"
NACOS_PASSWORD = "nacos.password"
NACOS_CONFIG_NAMESPACE = "nacos.config.namespace"
NACOS_CONFIG_GROUP = "nacos.config.group"
NACOS_DISCOVERY_NAME = "nacos.discovery.name"
NACOS_DISCOVERY_NAMESPACE = "nacos.discovery.namespace"
NACOS_DISCOVERY_IP = "nacos.discovery.ip"
