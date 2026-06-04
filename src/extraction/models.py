from typing import Any, Optional

from pydantic import BaseModel, Field


class ExtractedField(BaseModel):
    value: str
    confidence: float
    method: str


class VesselExtraction(BaseModel):
    vessel_name: Optional[ExtractedField] = None
    account_name: Optional[ExtractedField] = None
    open_port: Optional[ExtractedField] = None
    open_date: Optional[ExtractedField] = None
    vessel_type: Optional[ExtractedField] = None
    vessel_size_dwt: Optional[ExtractedField] = None

    raw_text: str = ""
    segmentation_confidence: float = 1.0
    segment_index: int = 0

    def to_record_dict(self) -> dict[str, Any]:
        data = {}
        for field in ("vessel_name", "account_name", "open_port", "open_date", "vessel_type", "vessel_size_dwt"):
            f = getattr(self, field)
            if f and f.value:
                data[field] = {"value": f.value, "confidence": f.confidence, "method": f.method}
        data["_segment_index"] = self.segment_index
        data["_segmentation_confidence"] = self.segmentation_confidence
        return data

    @property
    def overall_confidence(self) -> float:
        scores = [f.confidence for f in [self.vessel_name, self.account_name, self.open_port,
                                          self.open_date, self.vessel_type, self.vessel_size_dwt]
                  if f and f.value]
        if not scores:
            return 0.0
        return sum(scores) / len(scores) * self.segmentation_confidence
