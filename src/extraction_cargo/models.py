from typing import Any, Optional

from pydantic import BaseModel


class ExtractedField(BaseModel):
    value: str
    confidence: float
    method: str


class CargoVcExtraction(BaseModel):
    account_name: Optional[ExtractedField] = None
    cargo_name: Optional[ExtractedField] = None
    loading_port: Optional[ExtractedField] = None
    discharge_port: Optional[ExtractedField] = None
    laycan: Optional[ExtractedField] = None
    cargo_type: Optional[ExtractedField] = None
    quantity_min_mt: Optional[ExtractedField] = None
    quantity_max_mt: Optional[ExtractedField] = None
    load_rate: Optional[ExtractedField] = None
    discharge_rate: Optional[ExtractedField] = None
    commission_pct: Optional[ExtractedField] = None

    raw_text: str = ""
    segmentation_confidence: float = 1.0
    segment_index: int = 0

    def to_record_dict(self) -> dict[str, Any]:
        data = {}
        for field in (
            "account_name", "cargo_name", "loading_port", "discharge_port",
            "laycan", "cargo_type", "quantity_min_mt", "quantity_max_mt",
            "load_rate", "discharge_rate", "commission_pct",
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
                self.account_name, self.cargo_name, self.loading_port,
                self.discharge_port, self.laycan, self.cargo_type,
                self.quantity_min_mt, self.quantity_max_mt,
                self.load_rate, self.discharge_rate, self.commission_pct,
            ] if f and f.value
        ]
        if not scores:
            return 0.0
        return sum(scores) / len(scores) * self.segmentation_confidence
