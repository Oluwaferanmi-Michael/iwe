from typing import Optional, List
from pydantic import BaseModel, Field


class Metric(BaseModel):
    title: str
    value: str
    change: Optional[str] = None
    is_positive: Optional[bool] = None


class TableRow(BaseModel):
    period: str
    revenue: float
    expenses: float
    net_income: float
    margin: str


class Section(BaseModel):
    title: str
    content: str
    highlights: Optional[List[str]] = None


class Schema(BaseModel):
    report_title: str
    subtitle: str
    company_name: str
    prepared_for: str
    prepared_by: str
    date: str
    executive_summary: str
    metrics: List[Metric] = Field(default_factory=list)
    financial_table: List[TableRow] = Field(default_factory=list)
    sections: List[Section] = Field(default_factory=list)
