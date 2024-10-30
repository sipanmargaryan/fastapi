from pydantic import BaseModel


class DBTConfigSchema(BaseModel):
    domain: str
    source: str
    models: list[str]
