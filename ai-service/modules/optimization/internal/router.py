"""
FastAPI routes for the optimization module.
Step 1: a single diagnostic GET endpoint to verify the covariance
pipeline independently before /optimize (Step 2) exists.
"""
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from modules.optimization.internal.schemas import CovarianceMatrixResponse
from modules.optimization.internal.service import compute_covariance_matrix
from shared.db.connection import get_database

router = APIRouter(prefix="/optimize", tags=["optimization"])


@router.get("/covariance", response_model=CovarianceMatrixResponse)
async def get_covariance_matrix(
    years: int = 5,
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> CovarianceMatrixResponse:
    return await compute_covariance_matrix(db, years=years)