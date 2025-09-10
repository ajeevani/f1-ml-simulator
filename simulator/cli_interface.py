"""
F1 CLI Interface
Provides user-friendly command line interface for the simulation
"""

import typer
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.table import Table
from rich.progress import track
import time
import random

console = Console()

class F1SimulatorCLI:
    """CLI interface for F1 simulation"""
    
    def __init__(self, engine):
        self.engine = engine
        self.race_simulator = None
        self.predictions_made = 0
        
        # Import here to avoid circular imports
        from .race_simulator import RaceSimulator
        self.race_simulator = RaceSimulator(engine)
    
    def predict_driver_skill(self, driver_name: str, year: int, constructor: str, verbose: bool = False) -> Optional[Dict]:
        """Predict driver skill with CLI feedback"""
        
        console.print(f"🔮 Predicting skill for {driver_name} ({year})...")
        
        # Get historical data if available
        driver_data = self.engine.get_driver_historical_data(driver_name, year)
        
        if driver_data:
            # Use historical data
            result = {
                'skill_rating': driver_data.get('skill_rating', 50),
                'race_performance': driver_data.get('skill_rating', 50) * 0.8,
                'experience_factor': min(1.0, (year - 1950) / 75),
                'era_adjustment': self._get_era_competitiveness(year),
                'confidence': 0.99
            }
        else:
            # Generate prediction using default features
            default_features = self._generate_default_features(driver_name, year, constructor)
            result = self.engine.predict_driver_skill(default_features)
        
        self.predictions_made += 1
        return result
    
    def compare_drivers(self, driver1: str, year1: int, driver2: str, year2: int, detailed: bool = False) -> Optional[Dict]:
        """Compare two drivers with detailed analysis"""
        
        console.print(f"⚔️ Comparing {driver1} ({year1}) vs {driver2} ({year2})...")
        
        # Get predictions for both drivers
        pred1 = self.predict_driver_skill(driver1, year1, "default")
        pred2 = self.predict_driver_skill(driver2, year2, "default")
        
        if not pred1 or not pred2:
            return None
        
        result = {
            'driver1_skill': pred1['skill_rating'],
            'driver2_skill': pred2['skill_rating'],
            'skill_difference': abs(pred1['skill_rating'] - pred2['skill_rating']),
            'driver1_era': self._get_era_competitiveness(year1),
            'driver2_era': self._get_era_competitiveness(year2),
            'driver1_exp': pred1.get('experience_factor', 0.5),
            'driver2_exp': pred2.get('experience_factor', 0.5),
            'confidence': min(pred1.get('confidence', 0.8), pred2.get('confidence', 0.8))
        }
        
        return result
    
    def simulate_race(self, track: str, year: int, drivers: Optional[List[str]], weather: str, laps: int) -> Optional[Dict]:
        """Simulate a race with progress indication"""
        
        console.print(f"🏁 Setting up race at {track.title()}...")
        
        if not self.race_simulator:
            console.print("❌ Race simulator not available")
            return None
        
        # Show progress
        with console.status("[bold green]Simulating race...") as status:
            status.update("🏁 Setting up grid...")
            time.sleep(1)
            
            status.update("🏎️ Running qualifying...")
            time.sleep(1)
            
            status.update(f"🏁 Racing {laps} laps...")
            time.sleep(2)
            
            # Run actual simulation
            result = self.race_simulator.simulate_race(track, year, drivers, weather, laps)
        
        if result.get('success'):
            console.print("✅ Race simulation completed!")
            return result
        else:
            console.print(f"❌ Simulation failed: {result.get('error', 'Unknown error')}")
            return None
    
    def run_what_if_scenario(self, scenario: str, driver: Optional[str], year: Optional[int]) -> Optional[Dict]:
        """Run what-if scenario analysis"""
        
        console.print(f"🤔 Analyzing scenario: {scenario}")
        
        # Simple what-if logic (can be expanded)
        scenarios_db = {
            "hamilton in ferrari": {
                "prediction": "Likely 2-3 additional championships",
                "confidence": 0.75,
                "details": [
                    "Ferrari's speed advantage would complement Hamilton's race craft",
                    "Strategic errors might still be a limiting factor",
                    "Estimated 85-90 skill rating in competitive Ferrari"
                ]
            },
            "schumacher in red bull": {
                "prediction": "Dominant era similar to his Ferrari years",
                "confidence": 0.80,
                "details": [
                    "Red Bull's reliability would suit Schumacher's consistency",
                    "Technical partnership would be highly effective",
                    "Estimated 95+ skill rating in peak Red Bull era"
                ]
            },
            "senna in modern f1": {
                "prediction": "Multiple championships with any top team",
                "confidence": 0.85,
                "details": [
                    "Raw speed would translate perfectly to modern F1",
                    "Adaptability to modern technology would be strong",
                    "Estimated 90-95 skill rating in hybrid era"
                ]
            }
        }
        
        scenario_lower = scenario.lower()
        for key, result in scenarios_db.items():
            if key in scenario_lower:
                return result
        
        # Generic response for unknown scenarios
        return {
            "prediction": "Analysis requires more specific parameters",
            "confidence": 0.50,
            "details": ["Scenario not in database", "Manual analysis recommended"]
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get enhanced system statistics"""
        
        base_stats = self.engine.get_system_stats()
        
        # Add CLI-specific stats
        base_stats.update({
            'predictions_made': self.predictions_made,
            'top_drivers': [
                {'name': 'Ayrton Senna', 'peak_year': 1991, 'peak_rating': 94.2},
                {'name': 'Michael Schumacher', 'peak_year': 2004, 'peak_rating': 93.8},
                {'name': 'Lewis Hamilton', 'peak_year': 2020, 'peak_rating': 93.1},
                {'name': 'Alain Prost', 'peak_year': 1986, 'peak_rating': 91.7},
                {'name': 'Max Verstappen', 'peak_year': 2023, 'peak_rating': 91.5}
            ]
        })
        
        return base_stats
    
    def start_interactive_mode(self):
        """Start interactive CLI mode"""
        
        console.print("🎮 [bold green]F1 Interactive Simulation Mode[/bold green]")
        console.print("Type 'help' for commands or 'exit' to quit\n")
        
        while True:
            try:
                command = typer.prompt("F1-Sim").strip().lower()
                
                if command in ['exit', 'quit']:
                    console.print("👋 Goodbye!")
                    break
                elif command == 'help':
                    self._show_interactive_help()
                elif command.startswith('predict'):
                    self._handle_interactive_predict(command)
                elif command.startswith('compare'):
                    self._handle_interactive_compare(command)
                elif command.startswith('race'):
                    self._handle_interactive_race(command)
                elif command == 'stats':
                    self._show_interactive_stats()
                elif command == 'drivers':
                    self._show_available_drivers()
                elif command == 'tracks':
                    self._show_available_tracks()
                else:
                    console.print(f"❓ Unknown command: {command}. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                console.print("\n👋 Goodbye!")
                break
            except Exception as e:
                console.print(f"❌ Error: {e}")
    
    def interactive_what_if_mode(self):
        """Interactive what-if scenario mode"""
        
        console.print("🤔 [bold purple]What-If Scenario Mode[/bold purple]")
        console.print("Describe your scenario (e.g., 'Hamilton in Ferrari 2018')\n")
        
        while True:
            try:
                scenario = typer.prompt("What-if scenario (or 'exit')").strip()
                
                if scenario.lower() in ['exit', 'quit']:
                    break
                
                result = self.run_what_if_scenario(scenario, None, None)
                
                if result:
                    console.print(f"🔮 [bold]Prediction:[/bold] {result['prediction']}")
                    console.print(f"🎯 [bold]Confidence:[/bold] {result['confidence']:.0%}")
                    
                    if result.get('details'):
                        console.print("\n💡 [bold]Analysis:[/bold]")
                        for detail in result['details']:
                            console.print(f"   • {detail}")
                else:
                    console.print("❌ Could not analyze scenario")
                
                console.print("")  # Empty line
                
            except KeyboardInterrupt:
                break
    
    def _generate_default_features(self, driver_name: str, year: int, constructor: str) -> Dict[str, float]:
        """Generate default feature set for prediction"""
        
        # This is a simplified feature generation
        # In a real implementation, you'd have more sophisticated logic
        
        base_features = {}
        
        # Add all required features with reasonable defaults
        for feature in self.engine.feature_names:
            if 'skill' in feature.lower():
                base_features[feature] = 60 + random.uniform(-10, 15)
            elif 'experience' in feature.lower():
                base_features[feature] = min(1.0, (year - 1950) / 70)
            elif 'era' in feature.lower():
                base_features[feature] = self._get_era_competitiveness(year)
            elif 'position' in feature.lower():
                base_features[feature] = random.uniform(5, 15)
            elif 'points' in feature.lower():
                base_features[feature] = random.uniform(20, 200)
            elif 'rate' in feature.lower():
                base_features[feature] = random.uniform(0.1, 0.8)
            else:
                base_features[feature] = random.uniform(-1, 1)
        
        return base_features
    
    def _get_era_competitiveness(self, year: int) -> float:
        """Get era competitiveness factor"""
        
        era_factors = {
            (1950, 1960): 0.6,
            (1961, 1980): 0.75, 
            (1981, 2000): 0.85,
            (2001, 2013): 0.90,
            (2014, 2025): 0.95
        }
        
        for (start, end), factor in era_factors.items():
            if start <= year <= end:
                return factor
        
        return 0.8  # Default
    
    def _show_interactive_help(self):
        """Show interactive mode help"""
        
        table = Table(title="Available Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="white")
        
        table.add_row("predict <driver> <year>", "Predict driver skill")
        table.add_row("compare <d1> <y1> <d2> <y2>", "Compare two drivers")
        table.add_row("race <track> <year>", "Simulate a race")
        table.add_row("stats", "Show system statistics")
        table.add_row("drivers", "List available drivers")
        table.add_row("tracks", "List available tracks")
        table.add_row("help", "Show this help")
        table.add_row("exit", "Exit interactive mode")
        
        console.print(table)
    
    def _show_interactive_stats(self):
        """Show statistics in interactive mode"""
        
        stats = self.get_system_stats()
        
        table = Table(title="System Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Model Accuracy", f"{stats['model_accuracy']:.1f}%")
        table.add_row("Total Drivers", f"{stats['total_drivers']:,}")
        table.add_row("Seasons Covered", stats['seasons_covered'])
        table.add_row("Predictions Made", f"{stats['predictions_made']:,}")
        
        console.print(table)
    
    def _show_available_drivers(self):
        """Show available drivers"""
        drivers = self.engine.list_available_drivers()[:20]  # Show first 20
        
        console.print(f"🏎️ Available Drivers ({len(drivers)} shown):")
        for driver in drivers:
            console.print(f"   • {driver}")
    
    def _show_available_tracks(self):
        """Show available tracks"""
        tracks = self.engine.list_available_tracks()
        
        console.print(f"🏁 Available Tracks ({len(tracks)}):")
        for track in tracks:
            console.print(f"   • {track}")
    
    def _handle_interactive_predict(self, command: str):
        """Handle interactive predict command"""
        try:
            parts = command.split()
            if len(parts) >= 3:
                driver = parts[1].replace('_', ' ').title()
                year = int(parts[2])
                result = self.predict_driver_skill(driver, year, "default", verbose=True)
                
                if result:
                    console.print(f"🎯 {driver} ({year}): [bold]{result['skill_rating']:.1f}/100[/bold]")
                else:
                    console.print("❌ Prediction failed")
            else:
                console.print("Usage: predict <driver_name> <year>")
        except Exception as e:
            console.print(f"❌ Error: {e}")
    
    def _handle_interactive_compare(self, command: str):
        """Handle interactive compare command"""
        try:
            parts = command.split()
            if len(parts) >= 5:
                driver1 = parts[1].replace('_', ' ').title()
                year1 = int(parts[2])
                driver2 = parts[3].replace('_', ' ').title()
                year2 = int(parts[4])
                
                result = self.compare_drivers(driver1, year1, driver2, year2, detailed=True)
                
                if result:
                    console.print(f"🔵 {driver1} ({year1}): {result['driver1_skill']:.1f}")
                    console.print(f"🔴 {driver2} ({year2}): {result['driver2_skill']:.1f}")
                    
                    winner = driver1 if result['driver1_skill'] > result['driver2_skill'] else driver2
                    console.print(f"🏆 Winner: {winner}")
                else:
                    console.print("❌ Comparison failed")
            else:
                console.print("Usage: compare <driver1> <year1> <driver2> <year2>")
        except Exception as e:
            console.print(f"❌ Error: {e}")
    
    def _handle_interactive_race(self, command: str):
        """Handle interactive race command"""
        try:
            parts = command.split()
            if len(parts) >= 2:
                track = parts[1]
                year = int(parts[2]) if len(parts) > 2 else 2023
                
                result = self.simulate_race(track, year, None, "dry", 50)
                
                if result and result.get('success'):
                    console.print(f"🏁 Race Results at {result['track']}:")
                    for i, res in enumerate(result['results'][:5], 1):
                        console.print(f"   {i}. {res.driver}")
                else:
                    console.print("❌ Race simulation failed")
            else:
                console.print("Usage: race <track> [year]")
        except Exception as e:
            console.print(f"❌ Error: {e}")
