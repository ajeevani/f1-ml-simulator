"""
F1 Simulation Configuration
Centralized configuration for the simulation system
"""

from pathlib import Path
import os

class SimulationConfig:
    """Configuration settings for F1 simulation"""

    def __init__(self):
        self.PROJECT_ROOT = Path(__file__).parent.parent
        self.DATA_DIR = self.PROJECT_ROOT / "data"
        self.ENHANCED_DIR = self.DATA_DIR / "enhanced"
        self.ML_READY_DIR = self.DATA_DIR / "ml_ready"

        self.TRACKS_FILE = self.ENHANCED_DIR / "enhanced_tracks.parquet"
        self.CARS_FILE = self.ENHANCED_DIR / "enhanced_cars_2025.parquet"
        self.DRIVERS_FILE = self.ML_READY_DIR / "full_enhanced_dataset.parquet"

        self.MODELS_DIR = self.PROJECT_ROOT / "models" / "trained"
        self.PRIMARY_MODEL = "gradient_boosting_model.pkl"
        self.ENSEMBLE_MODEL = "ensemble_model.pkl"
        self.USE_ENSEMBLE = True

        # ... rest unchanged ...
        self.DEFAULT_RACE_LAPS = 50
        self.DEFAULT_WEATHER = "dry"
        self.RANDOM_SEED = None
        self.CLI_COLORS = True
        self.VERBOSE_OUTPUT = False
        self.CACHE_PREDICTIONS = True
        self.CACHE_DIR = self.PROJECT_ROOT / ".cache"
        self._validate_paths()

    def _validate_paths(self):
        required_paths = [
            self.ENHANCED_DIR,
            self.ML_READY_DIR,
            self.MODELS_DIR,
            self.TRACKS_FILE,
            self.CARS_FILE,
            self.DRIVERS_FILE
        ]
        for path in required_paths:
            if not path.exists():
                print(f"⚠️ Warning: Required path does not exist: {path}")

    def get_model_path(self, model_name: str) -> Path:
        return self.MODELS_DIR / model_name

    def get_tracks_path(self) -> Path:
        return self.TRACKS_FILE

    def get_cars_path(self) -> Path:
        return self.CARS_FILE

    def get_drivers_path(self) -> Path:
        return self.DRIVERS_FILE