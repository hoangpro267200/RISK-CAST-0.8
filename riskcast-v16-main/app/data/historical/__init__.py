"""
Historical Loss Data Module

Collects and stores REAL shipment outcomes to calibrate model weights.
"""

from app.data.historical.loss_data_repository import (
    HistoricalLossDataRepository,
    HistoricalShipment,
    ShipmentOutcome,
    ClaimStatus,
    CalibrationDataset,
)

__all__ = [
    "HistoricalLossDataRepository",
    "HistoricalShipment",
    "ShipmentOutcome",
    "ClaimStatus",
    "CalibrationDataset",
]
