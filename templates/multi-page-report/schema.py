from typing import Optional, List
from pydantic import BaseModel, Field, model_validator


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
    executive_summary: Optional[str] = None
    summary: Optional[str] = None
    metrics: List[Metric] = Field(default_factory=list)
    financial_table: List[TableRow] = Field(default_factory=list)
    table_data: List[TableRow] = Field(default_factory=list)
    sections: List[Section] = Field(default_factory=list)

    @model_validator(mode="after")
    def sync_aliases(self) -> "Schema":
        if self.summary and not self.executive_summary:
            self.executive_summary = self.summary
        elif self.executive_summary and not self.summary:
            self.summary = self.executive_summary

        if self.table_data and not self.financial_table:
            self.financial_table = self.table_data
        elif self.financial_table and not self.table_data:
            self.table_data = self.financial_table

        if not self.executive_summary:
            self.executive_summary = ""
            self.summary = ""

        return self
