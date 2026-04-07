from pydantic import BaseModel


class CreateOutboxEvent(BaseModel):
    payload: dict