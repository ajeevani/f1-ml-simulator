"""
F1 Race Simulator
Simulates complete F1 races using driver skill predictions
"""

import random
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class RaceResult:
    """Race result data structure"""
    position: int
    driver: str
    constructor: str
    time: str
    laps_completed: int
    status: str
    fastest_lap: Optional[str] = None
    
@dataclass 
class RaceSession:
    """Race session configuration"""
    track_id: str
    track_name: str
    year: int
    weather: str
    total_laps: int
    grid: List[Dict[str, str]]

class RaceSimulator:
    """Advanced F1 race simulator"""
    
    def __init__(self, engine):
        self.engine = engine
        self.random_seed = None
    
    def simulate_race(self, 
                     track_id: str,
                     year: int = 2023,
                     drivers: Optional[List[str]] = None,
                     weather: str = "dry",
                     laps: int = 50) -> Dict:
        """Simulate a complete F1 race"""
        
        try:
            # Set random seed for reproducible results
            if self.random_seed:
                random.seed(self.random_seed)
                np.random.seed(self.random_seed)
            
            # Get track information
            track_info = self.engine.get_track_info(track_id)
            if not track_info:
                return {"error": f"Track '{track_id}' not found"}
            
            # Setup race grid
            race_grid = self._setup_race_grid(drivers, year)
            if not race_grid:
                return {"error": "Could not setup race grid"}
            
            # Create race session
            session = RaceSession(
                track_id=track_id,
                track_name=track_info['name'],
                year=year,
                weather=weather,
                total_laps=laps,
                grid=race_grid
            )
            
            # Run qualifying simulation
            qualifying_results = self._simulate_qualifying(session)
            
            # Run race simulation
            race_results = self._simulate_race_main(session, qualifying_results)
            
            # Calculate race statistics
            race_stats = self._calculate_race_statistics(session, race_results)
            
            return {
                'track': track_info['name'],
                'year': year,
                'weather': weather,
                'laps': laps,
                'qualifying': qualifying_results,
                'results': race_results,
                'statistics': race_stats,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Race simulation error: {e}")
            return {"error": str(e), "success": False}
    
    def _setup_race_grid(self, drivers: Optional[List[str]], year: int) -> List[Dict]:
        """Setup the race grid with drivers and constructors"""
        
        available_drivers = list(self.engine.drivers_database.keys())
        available_constructors = list(self.engine.cars_data.keys())
        
        if not drivers:
            # Use top drivers from the database
            drivers = available_drivers[:20]  # Top 20 drivers
        
        race_grid = []
        
        for i, driver in enumerate(drivers[:20]):  # Max 20 drivers
            # Get constructor (cycle through available ones)
            constructor = available_constructors[i % len(available_constructors)]
            
            # Get driver historical data
            driver_data = self.engine.get_driver_historical_data(driver, year)
            
            if not driver_data:
                # Use latest available year
                all_driver_data = self.engine.get_driver_historical_data(driver)
                if all_driver_data:
                    latest_year = max(all_driver_data.keys())
                    driver_data = all_driver_data[latest_year]
                else:
                    # Default data
                    driver_data = {
                        'skill_rating': 60 + random.randint(-10, 10),
                        'constructor_id': constructor
                    }
            
            race_grid.append({
                'driver': driver,
                'constructor': driver_data.get('constructor_id', constructor),
                'skill_rating': driver_data.get('skill_rating', 60),
                'grid_position': i + 1
            })
        
        return race_grid
    
    def _simulate_qualifying(self, session: RaceSession) -> List[Dict]:
        """Simulate qualifying session"""
        
        qualifying_results = []
        
        for entry in session.grid:
            # Calculate qualifying performance
            driver_skill = entry['skill_rating']
            car_info = self.engine.get_car_info(entry['constructor'])
            track_info = self.engine.get_track_info(session.track_id)
            
            # Base qualifying time (in seconds, relative to track)
            base_time = 80 + random.uniform(-5, 5)  # Base lap time ~80s
            
            # Performance adjustments
            skill_factor = (100 - driver_skill) / 100 * 3  # Better skill = faster time
            car_factor = (100 - car_info.get('speed_rating', 70)) / 100 * 2
            
            # Weather impact
            weather_impact = 0
            if session.weather == "wet":
                weather_impact = random.uniform(0, 3) - (driver_skill / 100) * 2
            
            # Calculate final qualifying time
            qualifying_time = base_time + skill_factor + car_factor + weather_impact + random.uniform(-0.5, 0.5)
            
            qualifying_results.append({
                'driver': entry['driver'],
                'constructor': entry['constructor'],
                'time': qualifying_time,
                'time_formatted': self._format_lap_time(qualifying_time),
                'skill_rating': driver_skill
            })
        
        # Sort by qualifying time
        qualifying_results.sort(key=lambda x: x['time'])
        
        # Add grid positions
        for i, result in enumerate(qualifying_results):
            result['grid_position'] = i + 1
        
        return qualifying_results
    
    def _simulate_race_main(self, session: RaceSession, grid: List[Dict]) -> List[RaceResult]:
        """Simulate the main race"""
        
        track_info = self.engine.get_track_info(session.track_id)
        
        # Initialize race state
        race_state = []
        for entry in grid:
            performance_factors = self.engine.calculate_race_performance_factors(
                entry['skill_rating'],
                session.track_id,
                entry['constructor'],
                session.weather
            )
            
            race_state.append({
                'driver': entry['driver'],
                'constructor': entry['constructor'],
                'position': entry['grid_position'],
                'laps_completed': 0,
                'total_time': 0,
                'performance': performance_factors['final_performance'],
                'reliability': performance_factors['reliability_factor'],
                'status': 'running',
                'fastest_lap_time': None,
                'pit_stops': 0
            })
        
        # Simulate each lap
        for lap in range(1, session.total_laps + 1):
            self._simulate_lap(race_state, lap, track_info, session)
        
        # Convert to race results
        race_results = []
        running_drivers = [d for d in race_state if d['status'] == 'finished' or d['laps_completed'] > 0]
        
        # Sort by laps completed (desc) then by total time
        running_drivers.sort(key=lambda x: (-x['laps_completed'], x['total_time']))
        
        for i, driver_state in enumerate(running_drivers):
            race_results.append(RaceResult(
                position=i + 1,
                driver=driver_state['driver'],
                constructor=driver_state['constructor'],
                time=self._format_race_time(driver_state['total_time']) if i == 0 else f"+{self._format_gap_time(driver_state['total_time'] - running_drivers[0]['total_time'])}",
                laps_completed=driver_state['laps_completed'],
                status='Finished' if driver_state['status'] == 'finished' else driver_state['status'].title(),
                fastest_lap=self._format_lap_time(driver_state['fastest_lap_time']) if driver_state['fastest_lap_time'] else None
            ))
        
        return race_results
    
    def _simulate_lap(self, race_state: List[Dict], lap: int, track_info: Dict, session: RaceSession):
        """Simulate a single lap for all drivers"""
        
        for driver_state in race_state:
            if driver_state['status'] != 'running':
                continue
            
            # Reliability check
            reliability_factor = driver_state['reliability']
            if random.random() > reliability_factor and lap > 5:
                # DNF
                failure_types = ['Engine', 'Gearbox', 'Suspension', 'Collision', 'Spin']
                driver_state['status'] = random.choice(failure_types)
                continue
            
            # Calculate lap time
            base_lap_time = 85 + random.uniform(-2, 2)  # Base lap time
            performance_modifier = (100 - driver_state['performance']) / 100 * 3
            
            # Weather effect
            weather_modifier = 0
            if session.weather == "wet":
                weather_modifier = random.uniform(2, 8)
            elif session.weather == "mixed":
                weather_modifier = random.uniform(1, 4)
            
            # Tyre degradation (simplified)
            tyre_deg = (lap / session.total_laps) * 0.5
            
            # Traffic effect (based on position)
            traffic_effect = max(0, (driver_state['position'] - 1) * 0.1)
            
            # Calculate final lap time
            lap_time = base_lap_time + performance_modifier + weather_modifier + tyre_deg + traffic_effect + random.uniform(-0.5, 0.5)
            
            # Update driver state
            driver_state['total_time'] += lap_time
            driver_state['laps_completed'] += 1
            
            # Track fastest lap
            if driver_state['fastest_lap_time'] is None or lap_time < driver_state['fastest_lap_time']:
                driver_state['fastest_lap_time'] = lap_time
            
            # Pit stop logic (simplified)
            if lap in [15, 35] and driver_state['pit_stops'] < 2:  # Mandatory pit stops
                driver_state['total_time'] += 25  # Pit stop time
                driver_state['pit_stops'] += 1
        
        # Update positions based on total time
        running_drivers = [d for d in race_state if d['status'] == 'running']
        running_drivers.sort(key=lambda x: x['total_time'])
        
        for i, driver_state in enumerate(running_drivers):
            driver_state['position'] = i + 1
        
        # Mark completed race
        if lap == session.total_laps:
            for driver_state in race_state:
                if driver_state['status'] == 'running':
                    driver_state['status'] = 'finished'
    
    def _calculate_race_statistics(self, session: RaceSession, results: List[RaceResult]) -> Dict:
        """Calculate race statistics"""
        
        if not results:
            return {}
        
        # Find fastest lap
        fastest_lap_driver = None
        fastest_lap_time = None
        
        for result in results:
            if result.fastest_lap:
                lap_time = self._parse_lap_time(result.fastest_lap)
                if fastest_lap_time is None or lap_time < fastest_lap_time:
                    fastest_lap_time = lap_time
                    fastest_lap_driver = result.driver
        
        # Calculate other statistics
        finishers = len([r for r in results if r.status == 'Finished'])
        dnfs = len(results) - finishers
        
        return {
            'pole_sitter': results[0].driver if results else None,
            'winner': results[0].driver if results else None,
            'fastest_lap_driver': fastest_lap_driver,
            'fastest_lap_time': self._format_lap_time(fastest_lap_time) if fastest_lap_time else None,
            'finishers': finishers,
            'dnfs': dnfs,
            'completion_rate': finishers / len(results) if results else 0,
            'safety_cars': random.randint(0, 2),  # Simplified
            'total_laps': session.total_laps
        }
    
    def _format_lap_time(self, seconds: float) -> str:
        """Format lap time as MM:SS.mmm"""
        if seconds is None:
            return "N/A"
        
        minutes = int(seconds // 60)
        seconds = seconds % 60
        return f"{minutes}:{seconds:06.3f}"
    
    def _format_race_time(self, seconds: float) -> str:
        """Format race time as H:MM:SS.mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:06.3f}"
        else:
            return f"{minutes}:{seconds:06.3f}"
    
    def _format_gap_time(self, gap_seconds: float) -> str:
        """Format gap time"""
        if gap_seconds < 60:
            return f"{gap_seconds:.3f}s"
        else:
            minutes = int(gap_seconds // 60)
            seconds = gap_seconds % 60
            return f"{minutes}:{seconds:06.3f}"
    
    def _parse_lap_time(self, time_str: str) -> float:
        """Parse lap time string to seconds"""
        try:
            if ":" in time_str:
                parts = time_str.split(":")
                return float(parts[0]) * 60 + float(parts[1])
            else:
                return float(time_str.replace("s", ""))
        except:
            return 90.0  # Default
