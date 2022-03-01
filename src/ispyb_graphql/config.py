from __future__ import annotations

import pathlib
from functools import lru_cache

from pydantic import AnyUrl, BaseSettings


class Settings(BaseSettings):
    cas_server_url: AnyUrl
    ispyb_credentials: pathlib.Path


@lru_cache()
def get_settings():
    return Settings()
