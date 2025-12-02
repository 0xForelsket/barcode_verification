from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ScanBase(BaseModel):
    barcode: str

class ScanCreate(ScanBase):
    pass

class ScanResponse(ScanBase):
    id: int
    expected: str
    status: str
    timestamp: str  # Formatted as HH:MM:SS

    class Config:
        from_attributes = True

class JobBase(BaseModel):
    expected_barcode: str
    pieces_per_shipper: int = 1
    target_quantity: int = 0
    job_id: Optional[str] = None

class JobCreate(JobBase):
    pass

class JobResponse(JobBase):
    id: int
    job_id: str
    start_time: str # HH:MM
    start_time_iso: str
    is_active: bool
    pass_count: int
    fail_count: int
    total_scans: int
    total_pieces: int
    pass_rate: float
    elapsed: str # HH:MM
    scans_this_hour: int
    pieces_this_hour: int
    scans_prev_hour: int
    pieces_prev_hour: int

    class Config:
        from_attributes = True

class ShiftStatsResponse(BaseModel):
    total_shippers: int
    total_pieces: int
    total_pass: int
    total_fail: int
    jobs_completed: int

    class Config:
        from_attributes = True

class StatusResponse(BaseModel):
    active_job: Optional[JobResponse]
    shift: ShiftStatsResponse
    gpio_enabled: bool
    server_time: str

class JobEndRequest(BaseModel):
    pin: str

class JobSummary(BaseModel):
    job_id: str
    total_scans: int
    total_pieces: int
    pass_count: int
    fail_count: int
    pass_rate: float
    elapsed: str

class JobEndResponse(BaseModel):
    success: bool
    summary: JobSummary

class ScanResultResponse(BaseModel):
    scan: ScanResponse
    job: JobResponse
    recent_scans: List[ScanResponse]
