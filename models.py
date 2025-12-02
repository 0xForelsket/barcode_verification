from typing import List, Optional
from datetime import datetime, date as dt_date, timedelta
from sqlmodel import Field, Relationship, SQLModel, select

# ============================================================
# DATABASE TABLES
# ============================================================

class Job(SQLModel, table=True):
    __tablename__ = "jobs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(max_length=100)
    expected_barcode: str = Field(max_length=200)
    pieces_per_shipper: int = Field(default=1)
    target_quantity: int = Field(default=0)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=True)
    
    scans: List["Scan"] = Relationship(back_populates="job")

    @property
    def pass_count(self) -> int:
        return len([s for s in self.scans if s.status == 'PASS'])
    
    @property
    def fail_count(self) -> int:
        return len([s for s in self.scans if s.status == 'FAIL'])
    
    @property
    def total_scans(self) -> int:
        return len(self.scans)
    
    @property
    def total_pieces(self) -> int:
        return self.pass_count * self.pieces_per_shipper
    
    @property
    def pass_rate(self) -> float:
        if self.total_scans == 0:
            return 100.0
        return (self.pass_count / self.total_scans) * 100
    
    @property
    def elapsed_seconds(self) -> int:
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds())
        return int((datetime.now() - self.start_time).total_seconds())
    
    @property
    def elapsed_formatted(self) -> str:
        seconds = self.elapsed_seconds
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}"

    def scans_in_hour(self, target_hour: int) -> int:
        # This is a bit inefficient in Python memory but simplest for migration without complex queries
        # For a real app with millions of rows, we'd do this in SQL
        today = datetime.now().date()
        start_dt = datetime.combine(today, datetime.min.time().replace(hour=target_hour))
        end_dt = start_dt + timedelta(hours=1)
        
        count = 0
        for s in self.scans:
            if s.status == 'PASS' and start_dt <= s.timestamp < end_dt:
                count += 1
        return count
    
    @property
    def scans_this_hour(self) -> int:
        return self.scans_in_hour(datetime.now().hour)
        
    @property
    def scans_prev_hour(self) -> int:
        prev_hour = datetime.now().hour - 1
        if prev_hour < 0: return 0
        return self.scans_in_hour(prev_hour)
    
    def recent_scans(self, limit=10):
        # Sort by timestamp desc
        sorted_scans = sorted(self.scans, key=lambda x: x.timestamp, reverse=True)
        return sorted_scans[:limit]


class Scan(SQLModel, table=True):
    __tablename__ = "scans"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="jobs.id")
    barcode: str = Field(max_length=200)
    expected: str = Field(max_length=200)
    status: str = Field(max_length=10)  # PASS or FAIL
    timestamp: datetime = Field(default_factory=datetime.now)
    
    job: Job = Relationship(back_populates="scans")


class ShiftStats(SQLModel, table=True):
    __tablename__ = "shift_stats"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    date: dt_date = Field(default_factory=lambda: datetime.now().date(), sa_column_kwargs={"unique": True})
    total_shippers: int = Field(default=0)
    total_pieces: int = Field(default=0)
    total_pass: int = Field(default=0)
    total_fail: int = Field(default=0)
    jobs_completed: int = Field(default=0)


# ============================================================
# API SCHEMAS (Read Models)
# ============================================================

class ScanRead(SQLModel):
    id: int
    barcode: str
    expected: str
    status: str
    timestamp: str 

    @classmethod
    def from_scan(cls, scan: Scan):
        return cls(
            id=scan.id,
            barcode=scan.barcode,
            expected=scan.expected,
            status=scan.status,
            timestamp=scan.timestamp.strftime('%H:%M:%S')
        )

class JobRead(SQLModel):
    id: int
    job_id: str
    expected_barcode: str
    pieces_per_shipper: int
    target_quantity: int
    start_time: str
    start_time_iso: str
    is_active: bool
    pass_count: int
    fail_count: int
    total_scans: int
    total_pieces: int
    pass_rate: float
    elapsed: str
    scans_this_hour: int
    pieces_this_hour: int
    scans_prev_hour: int
    pieces_prev_hour: int

    @classmethod
    def from_job(cls, job: Job):
        return cls(
            id=job.id,
            job_id=job.job_id,
            expected_barcode=job.expected_barcode,
            pieces_per_shipper=job.pieces_per_shipper,
            target_quantity=job.target_quantity,
            start_time=job.start_time.strftime('%H:%M'),
            start_time_iso=job.start_time.isoformat(),
            is_active=job.is_active,
            pass_count=job.pass_count,
            fail_count=job.fail_count,
            total_scans=job.total_scans,
            total_pieces=job.total_pieces,
            pass_rate=round(job.pass_rate, 1),
            elapsed=job.elapsed_formatted,
            scans_this_hour=job.scans_this_hour,
            pieces_this_hour=job.scans_this_hour * job.pieces_per_shipper,
            scans_prev_hour=job.scans_prev_hour,
            pieces_prev_hour=job.scans_prev_hour * job.pieces_per_shipper
        )

class ShiftStatsRead(SQLModel):
    total_shippers: int
    total_pieces: int
    total_pass: int
    total_fail: int
    jobs_completed: int

class StatusResponse(SQLModel):
    active_job: Optional[JobRead]
    shift: ShiftStatsRead
    gpio_enabled: bool
    server_time: str

class JobStartRequest(SQLModel):
    job_id: Optional[str] = None
    expected_barcode: str
    pieces_per_shipper: int = 1
    target_quantity: int = 0

class JobEndRequest(SQLModel):
    pin: str

class JobSummary(SQLModel):
    job_id: str
    total_scans: int
    total_pieces: int
    pass_count: int
    fail_count: int
    pass_rate: float
    elapsed: str

class JobEndResponse(SQLModel):
    success: bool
    summary: JobSummary

class ScanRequest(SQLModel):
    barcode: str

class ScanResultResponse(SQLModel):
    scan: ScanRead
    job: JobRead
    recent_scans: List[ScanRead]
