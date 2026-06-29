import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple
from uuid import UUID


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class Job:
    id: str
    name: str
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    errors: List[str] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "progress": self.progress,
            "total_items": self.total_items,
            "completed_items": self.completed_items,
            "failed_items": self.failed_items,
            "errors": self.errors[-5:],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class BatchProcessor:
    def __init__(self, max_workers: int = 4):
        self.jobs: Dict[str, Job] = {}
        self.max_workers = max_workers

    def create_job(
        self, name: str, total_items: int = 0
    ) -> Job:
        job = Job(
            id=str(uuid.uuid4()),
            name=name,
            total_items=total_items,
        )
        self.jobs[job.id] = job
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        return self.jobs.get(job_id)

    def list_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        sorted_jobs = sorted(
            self.jobs.values(),
            key=lambda j: j.created_at,
            reverse=True,
        )
        return [j.to_dict() for j in sorted_jobs[:limit]]

    async def run_batch(
        self,
        job: Job,
        items: List[Any],
        worker_fn: Callable[[Any, int], Awaitable[Tuple[bool, Optional[str]]]],
        name: str = "batch",
    ) -> Job:
        job.update(status=JobStatus.RUNNING, total_items=len(items))

        semaphore = asyncio.Semaphore(self.max_workers)

        async def worker(item, idx):
            async with semaphore:
                try:
                    success, error = await worker_fn(item, idx)
                    if success:
                        job.completed_items += 1
                    else:
                        job.failed_items += 1
                        if error:
                            job.errors.append(f"[{idx}] {error}")
                except Exception as e:
                    job.failed_items += 1
                    job.errors.append(f"[{idx}] {str(e)}")
                finally:
                    if job.total_items > 0:
                        job.progress = (
                            (job.completed_items + job.failed_items)
                            / job.total_items
                        ) * 100
                    job.updated_at = time.time()

        tasks = [worker(item, i) for i, item in enumerate(items)]
        await asyncio.gather(*tasks)

        if job.failed_items == 0:
            job.update(status=JobStatus.COMPLETED, progress=100.0)
        elif job.completed_items > 0:
            job.update(status=JobStatus.PARTIAL)
        else:
            job.update(status=JobStatus.FAILED)

        return job

    async def run_incremental(
        self,
        job: Job,
        existing_items: List[Any],
        new_items: List[Any],
        worker_fn: Callable[[Any, int], Awaitable[Tuple[bool, Optional[str]]]],
        batch_name: str = "incremental",
    ) -> Job:
        existing_ids = {id(item) for item in existing_items}
        truly_new = [
            item for item in new_items
            if id(item) not in existing_ids
        ]
        return await self.run_batch(job, truly_new, worker_fn, batch_name)


_internal_processor: Optional[BatchProcessor] = None


def get_processor() -> BatchProcessor:
    global _internal_processor
    if _internal_processor is None:
        _internal_processor = BatchProcessor()
    return _internal_processor
