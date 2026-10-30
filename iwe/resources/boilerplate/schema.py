"""Validation schema for template bundle."""

from pydantic import BaseModel, Field


class Schema(BaseModel):
    """Pydantic model defining required and optional fields for this bundle."""

    title: str = Field(..., description="Document title")
    content: str = Field(default="", description="Main body content")
