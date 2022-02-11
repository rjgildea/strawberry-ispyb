from __future__ import annotations

import functools

from api import definitions
from api.schema import schema
from fastapi import Depends, FastAPI
from strawberry.dataloader import DataLoader
from strawberry.fastapi import GraphQLRouter

from .database import SessionLocal


async def get_session():
    async with SessionLocal() as session:
        yield session


async def get_context(db=Depends(get_session)):
    return {
        "db": db,
        "auto_processing_loader": DataLoader(
            functools.partial(
                definitions.load_auto_processings,
                db,
            )
        ),
        "data_collections_loader": DataLoader(
            functools.partial(
                definitions.load_data_collections,
                db,
            )
        ),
        "sample_loader": DataLoader(
            functools.partial(
                definitions.load_samples,
                db,
            )
        ),
    }


graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
)


app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
