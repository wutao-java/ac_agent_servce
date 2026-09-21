from agent.tianji.node.BaseNodeAgent import BaseNodeAgent
from agent.tianji.tools import query_course_by_id, query_recommend_data
from agent.prompts import system_prompt_config


class RecommendAgent(BaseNodeAgent):
    """
    课程推荐智能体
    """

    def system_prompt(self):
        return system_prompt_config.chat_recommend_message

    def tools(self):
        return [query_recommend_data, query_course_by_id]
