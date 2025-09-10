"""
F1 Historical Driver Simulation Package
Advanced ML-powered F1 simulation system
"""

__version__ = "1.0.0"
__author__ = "F1 Simulation Team"

from .core import F1SimulationEngine
from .race_simulator import RaceSimulator
from .cli_interface import F1SimulatorCLI

__all__ = ['F1SimulationEngine', 'RaceSimulator', 'F1SimulatorCLI']
