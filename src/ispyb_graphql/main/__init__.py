import functools
import typing

from fastapi import FastAPI
from strawberry.dataloader import DataLoader
from strawberry.fastapi import GraphQLRouter

from api import definitions
from api.schema import schema

from . import models
from .database import SessionLocal


async def get_context(
    # custom_value=Depends(custom_context_dependency),
):
    db = SessionLocal()
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
                definitions.load_data_collections_for_samples,
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
