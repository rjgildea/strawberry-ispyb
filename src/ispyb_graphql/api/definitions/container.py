from __future__ import annotations

from typing import Optional

import strawberry

from ispyb_graphql import models


@strawberry.type
class Container:
    capacity: int
    code: str
    container_id: int
    container_type: str
    barcode: Optional[str]

    @classmethod
    def from_instance(cls, instance: models.Container):
        return cls(
            capacity=instance.capacity,
            barcode=instance.barcode,
            code=instance.code,
            container_id=instance.containerId,
            container_type=instance.containerType,
        )
