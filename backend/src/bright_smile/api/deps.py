"""FastAPI dependencies shared across routers."""

from typing import Annotated, cast

from fastapi import Depends, Request

from bright_smile.agent.graph import Agent
from bright_smile.core.config import Settings
from bright_smile.db.mongo import MongoClient


def get_app_settings(request: Request) -> Settings:
    return cast("Settings", request.app.state.settings)


def get_mongo_client(request: Request) -> MongoClient:
    return cast("MongoClient", request.app.state.mongo_client)


def get_agent(request: Request) -> Agent:
    return cast("Agent", request.app.state.agent)


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
MongoClientDep = Annotated[MongoClient, Depends(get_mongo_client)]
AgentDep = Annotated[Agent, Depends(get_agent)]
