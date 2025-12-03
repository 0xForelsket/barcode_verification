from typing import List, Optional
from datetime import datetime, date as dt_date, timedelta
from sqlmodel import Field, Relationship, SQLModel, select
from pydantic import field_validator
import re

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
    
    # NEW: Cached counts for performance
    cached_pass_count: int = Field(default=0)
    cached_fail_count: int = Field(default=0)
    cached_total_scans: int = Field(default=0)
    
    scans: List["Scan"] = Relationship(back_populates="job")

    @property
    def pass_count(self) -> int:
        """Use cached count for performance"""
        return self.cached_pass_count
    
    @property
    def fail_count(self) -> int:
        """Use cached count for performance"""
        return self.cached_fail_count
    
    @property
    def total_scans(self) -> int:
        """Use cached count for performance"""
        return self.cached_total_scans
    
    @property
    def total_pieces(self) -> int:
        """Calculate from cached pass count"""
        return self.cached_pass_count * self.pieces_per_shipper
    
    @property
    def pass_rate(self) -> float:
        if self.total_scans == 0:
            return 0.0
        return (self.pass_count / self.total_scans) * 100

    @property
    def elapsed_time(self) -> timedelta:
        end = self.end_time or datetime.now()
        return end - self.start_time

    @property
    def elapsed_formatted(self) -> str:
        total_seconds = int(self.elapsed_time.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def scans_in_hour(self, target_hour: int, session=None) -> int:
        """Count scans in a specific hour using database query for performance"""
        if not session:
            # Fallback to memory scan if no session provided
            today = datetime.now().date()
            start_dt = datetime.combine(today, datetime.min.time().replace(hour=target_hour))
            end_dt = start_dt + timedelta(hours=1)
            return len([s for s in self.scans if s.status == 'PASS' and start_dt <= s.timestamp < end_dt])
        
        # Use database query (much faster)
        from sqlmodel import select, func
        today = datetime.now().date()
        start_dt = datetime.combine(today, datetime.min.time().replace(hour=target_hour))
        end_dt = start_dt + timedelta(hours=1)
        
        count = session.exec(
            select(func.count(Scan.id))
            .where(Scan.job_id == self.id)
            .where(Scan.status == 'PASS')
            .where(Scan.timestamp >= start_dt)
            .where(Scan.timestamp < end_dt)
        ).one()
        
        return count or 0
    
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
    job_id: int = Field(foreign_key="jobs.id", index=True)
    barcode: str = Field(max_length=200)
    expected: str = Field(max_length=200)
    status: str = Field(max_length=10)  # PASS or FAIL
    timestamp: datetime = Field(default_factory=datetime.now, index=True)
    
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
    
    @field_validator('job_id')
    @classmethod
    def validate_job_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate job ID format and content"""
        if v is None:
            return None
        
        v = v.strip()
        if not v:
            return None
        
        # Length check
        if len(v) > 100:
            raise ValueError('Job ID must be 100 characters or less')
        
        # Prevent XSS and SQL injection attempts
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '\\', '/', '\x00']
        if any(char in v for char in dangerous_chars):
            raise ValueError('Job ID contains invalid characters')
        
        # Prevent control characters
        if any(ord(char) < 32 for char in v):
            raise ValueError('Job ID contains control characters')
        
        return v
    
    @field_validator('expected_barcode')
    @classmethod
    def validate_barcode(cls, v: str) -> str:
        """Validate barcode format and content"""
        if not v:
            raise ValueError('Barcode is required')
        
        v = v.strip()
        if not v:
            raise ValueError('Barcode cannot be empty')
        
        # Length check
        if len(v) > 200:
            raise ValueError('Barcode must be 200 characters or less')
        
        # Minimum length (most barcodes are at least 3 chars)
        if len(v) < 1:
            raise ValueError('Barcode is too short')
        
        # Prevent XSS and injection attacks
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '\\', '\x00']
        if any(char in v for char in dangerous_chars):
            raise ValueError('Barcode contains invalid characters')
        
        # Prevent control characters
        if any(ord(char) < 32 and char not in ['\t', '\n', '\r'] for char in v):
            raise ValueError('Barcode contains invalid control characters')
        
        return v
    
    @field_validator('pieces_per_shipper')
    @classmethod
    def validate_pieces(cls, v: int) -> int:
        """Validate pieces per shipper"""
        if v < 1:
            raise ValueError('Pieces per shipper must be at least 1')
        
        if v > 10000:
            raise ValueError('Pieces per shipper must be 10,000 or less')
        
        return v
    
    @field_validator('target_quantity')
    @classmethod
    def validate_target(cls, v: int) -> int:
        """Validate target quantity"""
        if v < 0:
            raise ValueError('Target quantity cannot be negative')
        
        if v > 1000000:
            raise ValueError('Target quantity must be 1,000,000 or less')
        
        return v


class JobEndRequest(SQLModel):
    pin: str
    
    @field_validator('pin')
    @classmethod
    def validate_pin(cls, v: str) -> str:
        """Validate PIN format"""
        if not v:
            raise ValueError('PIN is required')
        
        v = v.strip()
        
        # Length check
        if len(v) < 4:
            raise ValueError('PIN must be at least 4 characters')
        
        if len(v) > 20:
            raise ValueError('PIN must be 20 characters or less')
        
        # Only allow alphanumeric (some PINs might have letters)
        if not re.match(r'^[a-zA-Z0-9]+$', v):
            raise ValueError('PIN must contain only letters and numbers')
        
        return v

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
