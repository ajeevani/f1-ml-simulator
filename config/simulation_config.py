"""
F1 Simulation Configuration
Centralized configuration for the simulation system
"""

from pathlib import Path
import os

class SimulationConfig:
    """Configuration settings for F1 simulation"""

    def __init__(self):
        # Project paths
        self.PROJECT_ROOT = Path(__file__).parent.parent
        self.DATA_DIR = self.PROJECT_ROOT / "data"
        self.MODELS_DIR = self.PROJECT_ROOT / "models" / "trained"      # <-- FIXED!

        # ML Model settings
        self.PRIMARY_MODEL = "gradient_boosting_model.pkl"
        self.ENSEMBLE_MODEL = "ensemble_model.pkl"
        self.USE_ENSEMBLE = True

        # Simulation settings
        self.DEFAULT_RACE_LAPS = 50
        self.DEFAULT_WEATHER = "dry"
        self.RANDOM_SEED = None  # Set for reproducible results

        # CLI settings
        self.CLI_COLORS = True
        self.VERBOSE_OUTPUT = False

        # Cache settings
        self.CACHE_PREDICTIONS = True
        self.CACHE_DIR = self.PROJECT_ROOT / ".cache"

        # Validation
        self._validate_paths()

    def _validate_paths(self):
        """Validate that required paths exist"""
        required_paths = [
            self.DATA_DIR,
            self.MODELS_DIR
        ]
        for path in required_paths:
            if not path.exists():
                print(f"⚠️ Warning: Required path does not exist: {path}")

    @property
    def model_files(self):
        """Get list of required model files"""
        return [
            self.PRIMARY_MODEL,
            self.ENSEMBLE_MODEL,
            "enhanced_scalers.pkl",
            "enhanced_encoders.pkl",
            "enhanced_feature_names.json"
        ]

    def get_model_path(self, model_name: str) -> Path:
        """Get full path to model file"""
        return self.MODELS_DIR / model_name

    def get_data_path(self, data_file: str) -> Path:
        """Get full path to data file"""
        return self.DATA_DIR / data_file