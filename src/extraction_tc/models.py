from typing import Any, Optional

from pydantic import BaseModel


class ExtractedField(BaseModel):
    value: str
    confidence: float
    method: str


class TcExtraction(BaseModel):
    account_name: Optional[ExtractedField] = None
    vessel_name: Optional[ExtractedField] = None
    delivery_port: Optional[ExtractedField] = None
    delivery_date: Optional[ExtractedField] = None
    redelivery_port: Optional[ExtractedField] = None
    redelivery_date: Optional[ExtractedField] = None
    charter_period: Optional[ExtractedField] = None
    hire_rate: Optional[ExtractedField] = None
    commission_pct: Optional[ExtractedField] = None
    intended_cargo: Optional[ExtractedField] = None
    vessel_dwt: Optional[ExtractedField] = None

    raw_text: str = ""
    segmentation_confidence: float = 1.0
    segment_index: int = 0

    def to_record_dict(self) -> dict[str, Any]:
        data = {}
        for field in (
            "account_name", "vessel_name", "delivery_port", "delivery_date",
            "redelivery_port", "redelivery_date", "charter_period",
            "hire_rate", "commission_pct", "intended_cargo", "vessel_dwt",
        ):
            f = getattr(self, field)
            if f and f.value:
                data[field] = {"value": f.value, "confidence": f.confidence, "method": f.method}
        data["_segment_index"] = self.segment_index
        data["_segmentation_confidence"] = self.segmentation_confidence
        return data

    @property
    def overall_confidence(self) -> float:
        scores = [
            f.confidence for f in [
                self.account_name, self.vessel_name, self.delivery_port,
                self.delivery_date, self.redelivery_port, self.redelivery_date,
                self.charter_period, self.hire_rate, self.commission_pct,
                self.intended_cargo, self.vessel_dwt,
            ] if f and f.value
        ]
        if not scores:
            return 0.0
        return sum(scores) / len(scores) * self.segmentation_confidence
