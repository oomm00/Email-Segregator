"""Railway deployment FastAPI app — synchronous extraction + matching, PostgreSQL only."""

import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# ── inline safe config (no es/redis/minio/rabbitmq deps) ──
_DATABASE_URL = "postgresql://shipping:shipping_secret@localhost:5432/shipping_email"

# ── schemas ────────────────────────────────────────────────

class ExtractRequest(BaseModel):
    body_text: str
    subject: Optional[str] = None
    run_matching: bool = True

class FieldOut(BaseModel):
    value: str
    confidence: float
    method: str

class VesselOut(BaseModel):
    vessel_name: Optional[FieldOut] = None
    account_name: Optional[FieldOut] = None
    open_port: Optional[FieldOut] = None
    open_date: Optional[FieldOut] = None
    vessel_type: Optional[FieldOut] = None
    vessel_size_dwt: Optional[FieldOut] = None

class CargoOut(BaseModel):
    account_name: Optional[FieldOut] = None
    cargo_name: Optional[FieldOut] = None
    loading_port: Optional[FieldOut] = None
    discharge_port: Optional[FieldOut] = None
    laycan: Optional[FieldOut] = None
    cargo_type: Optional[FieldOut] = None
    quantity_min_mt: Optional[FieldOut] = None
    quantity_max_mt: Optional[FieldOut] = None
    load_rate: Optional[FieldOut] = None
    discharge_rate: Optional[FieldOut] = None
    commission_pct: Optional[FieldOut] = None

class TcOut(BaseModel):
    account_name: Optional[FieldOut] = None
    vessel_name: Optional[FieldOut] = None
    delivery_port: Optional[FieldOut] = None
    delivery_date: Optional[FieldOut] = None
    redelivery_port: Optional[FieldOut] = None
    redelivery_date: Optional[FieldOut] = None
    charter_period: Optional[FieldOut] = None
    hire_rate: Optional[FieldOut] = None
    commission_pct: Optional[FieldOut] = None
    intended_cargo: Optional[FieldOut] = None
    vessel_dwt: Optional[FieldOut] = None

class MatchOut(BaseModel):
    label: str
    score: float
    source_type: str
    source_ref: str
    target_type: str
    target_ref: str
    details: dict

class ExtractResponse(BaseModel):
    request_id: str
    classification: str
    vessels: list[VesselOut]
    cargoes: list[CargoOut]
    tc_fixtures: list[TcOut]
    matches: list[MatchOut]


# ── classification helper ──────────────────────────────────

def _classify(text: str) -> str:
    t = text.upper()
    vc_kw = {"CARGO", "LOAD", "DISCH", "POL", "POD", "LAYCAN", "MTS", "MT", "QUANTITY", "QTY"}
    tc_kw = {"DELIVERY", "REDELIVERY", "TC", "TCT", "DURATION", "HIRE", "COM", "ADDCOM", "ADDOM"}
    ton_kw = {"OPEN", "DWT", "VESSEL", "MV ", "M/V", "VSL", "BUILT", "FLAG"}
    vc = sum(1 for k in vc_kw if k in t)
    tc = sum(1 for k in tc_kw if k in t)
    ton = sum(1 for k in ton_kw if k in t)
    scores = {"TONNAGE": ton, "CARGO_VC": vc, "CARGO_TC": tc}
    return max(scores, key=scores.get) or "UNKNOWN"


# ── build app ──────────────────────────────────────────────

app = FastAPI(title="Shipping Email Demo (Railway)", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {
        "service": "Shipping Email Demo",
        "endpoints": {
            "POST /extract": "Run extraction (and optionally matching) on email text",
            "GET /health": "Health check",
        },
    }


@app.post("/extract", response_model=ExtractResponse)
async def extract(req: ExtractRequest):
    rid = str(uuid.uuid4())
    body = req.body_text or ""
    if not body.strip():
        raise HTTPException(400, "body_text is required")

    category = _classify(body)

    from src.extraction.pipeline import run_tonnage_pipeline
    from src.extraction_cargo.pipeline import run_cargo_vc_pipeline
    from src.extraction_tc.pipeline import run_tc_pipeline

    vessels_raw = run_tonnage_pipeline(rid, body, req.subject or "")
    cargoes_raw = run_cargo_vc_pipeline(rid, body, req.subject or "")
    tc_raw = run_tc_pipeline(rid, body, req.subject or "")

    def _to_out(f):
        return FieldOut(value=f.value, confidence=f.confidence, method=f.method) if f else None

    vessels = [VesselOut(**{k: _to_out(getattr(v, k)) for k in VesselOut.model_fields}) for v in vessels_raw]
    cargoes = [CargoOut(**{k: _to_out(getattr(c, k)) for k in CargoOut.model_fields}) for c in cargoes_raw]
    tc_fixtures = [TcOut(**{k: _to_out(getattr(t, k)) for k in TcOut.model_fields}) for t in tc_raw]

    matches = []
    if req.run_matching:
        from src.matching.main import MatchingEngine
        engine = MatchingEngine()
        raw_matches = engine.match_all(vessels_raw, cargoes_raw, tc_raw)
        matches = [
            MatchOut(
                label=m.label, score=round(m.score, 1),
                source_type=m.source_type, source_ref=m.source_ref,
                target_type=m.target_type, target_ref=m.target_ref,
                details=m.details,
            )
            for m in raw_matches
        ]

    return ExtractResponse(
        request_id=rid,
        classification=category,
        vessels=vessels,
        cargoes=cargoes,
        tc_fixtures=tc_fixtures,
        matches=matches[:20],
    )
