from fastapi import APIRouter
from pydantic import BaseModel
from dao import app_dao
from config import logger

auth_router = APIRouter()


class AppKeyandAppSecret(BaseModel):
    app_key: str
    app_secret: str


@auth_router.post("/token")
async def create_token(req:AppKeyandAppSecret):
    try:
        new_token = app_dao.create_token(req.app_key, req.app_secret)
        logger.info("token生成成功")
        return new_token
    except Exception as err:
        logger.info(f"token生成失败{err}")
