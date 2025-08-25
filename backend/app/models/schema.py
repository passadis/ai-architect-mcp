from pydantic import BaseModel
from typing import Optional


class ArchitectureRequest(BaseModel):
    input: str


class ArchitectureResponse(BaseModel):
    design_document: str
    diagram_url: str
