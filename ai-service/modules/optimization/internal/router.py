"""
FastAPI routes for the optimization module.
- GET  /optimize/covariance: Step 1 diagnostic.
- POST /optimize: Step 2's single-point Markowitz endpoint.
- POST /optimize/frontier: Step 3's Efficient Frontier sweep.
"""
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from modules.optimization.internal.schemas import (
    CovarianceMatrixResponse,
    FrontierRequest,
    FrontierResponse,
    OptimizeRequest,
    OptimizeResponse,
)
from modules.optimization.internal.service import (
    compute_covariance_matrix,
    compute_efficient_frontier,
    compute_optimal_allocation,
)
from modules.optimization.internal.solver import OptimizationError
from shared.db.connection import get_database

router = APIRouter(prefix="/optimize", tags=["optimization"])


@router.get("/covariance", response_model=CovarianceMatrixResponse)
async def get_covariance_matrix(
    years: int = 5,
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> CovarianceMatrixResponse:
    return await compute_covariance_matrix(db, years=years)


@router.post("", response_model=OptimizeResponse)
async def optimize_portfolio(
    request: OptimizeRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> OptimizeResponse:
    try:
        return await compute_optimal_allocation(db, request.risk_lambda, request.years)
    except OptimizationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/frontier", response_model=FrontierResponse)
async def get_efficient_frontier(
    request: FrontierRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> FrontierResponse:
    try:
        return await compute_efficient_frontier(
            db, request.risk_lambda, request.years, request.num_points
        )
    except OptimizationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc