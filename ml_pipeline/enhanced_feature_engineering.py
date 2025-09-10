"""
Enhanced F1 Feature Engineering Pipeline - Production Grade
Processes enhanced F1 dataset for ML model training
Optimized for Historical F1 Driver Simulation with limited data
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler, LabelEncoder, RobustScaler
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.impute import SimpleImputer
import logging
import warnings
import json

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedF1FeatureEngineer:
    """
    Enhanced F1 feature engineering optimized for limited dataset scenarios
    Maximizes information extraction from available data
    """
    
    def __init__(self, data_dir='data/enhanced'):
        self.data_dir = Path(data_dir)
        self.processed_dir = Path('data/ml_ready')
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        self.scalers = {}
        self.encoders = {}
        self.imputers = {}
        
    def process_enhanced_dataset(self):
        """Process enhanced dataset with optimized feature engineering"""
        
        print("🔧 Enhanced F1 Feature Engineering Pipeline v2.0")
        print("📊 Optimized for limited data scenarios")
        print("="*70)
        
        # Load enhanced datasets
        print("📥 Loading enhanced datasets...")
        datasets = self._load_enhanced_data()
        
        # Create comprehensive feature matrix
        print("🛠️ Engineering comprehensive features...")
        feature_dataset = self._create_enhanced_features(datasets)
        
        # Advanced feature enrichment
        print("⚡ Advanced feature enrichment...")
        enriched_dataset = self._enrich_features_advanced(feature_dataset, datasets)
        
        # Prepare ML datasets with advanced techniques
        print("📋 Preparing optimized ML datasets...")
        ml_datasets = self._prepare_enhanced_ml_datasets(enriched_dataset)
        
        # Save processed datasets
        print("💾 Saving ML-ready datasets...")
        self._save_enhanced_ml_datasets(ml_datasets)
        
        print("✅ Enhanced feature engineering completed!")
        return ml_datasets
    
    def _load_enhanced_data(self):
        """Load all enhanced datasets with error handling"""
        
        datasets = {}
        
        data_files = {
            'race_results': 'enhanced_race_results.parquet',
            'driver_standings': 'enhanced_driver_standings.parquet',
            'constructor_standings': 'enhanced_constructor_standings.parquet',
            'qualifying_data': 'enhanced_qualifying_data.parquet',
            'driver_skills': 'enhanced_driver_skills_comprehensive.parquet',
            'fastf1_data': 'enhanced_fastf1_comprehensive.parquet',
            'weather_data': 'enhanced_weather_data.parquet',
            'laps_detailed': 'enhanced_laps_detailed.parquet',
            'circuits': 'enhanced_circuits.parquet',
            'drivers': 'enhanced_drivers.parquet',
            'constructors': 'enhanced_constructors.parquet',
            'cars_2025': 'enhanced_cars_2025.parquet',
            'tracks': 'enhanced_tracks.parquet'
        }
        
        for data_key, file_name in data_files.items():
            file_path = self.data_dir / file_name
            if file_path.exists():
                try:
                    datasets[data_key] = pd.read_parquet(file_path)
                    logger.info(f"Loaded {data_key}: {len(datasets[data_key]):,} records")
                except Exception as e:
                    logger.warning(f"Error loading {file_name}: {e}")
                    datasets[data_key] = pd.DataFrame()
            else:
                logger.warning(f"File not found: {file_path}")
                datasets[data_key] = pd.DataFrame()
        
        return datasets
    
    def _create_enhanced_features(self, datasets):
        """Create enhanced feature set from available data"""
        
        # Start with driver skills as base (target variable included)
        base_df = datasets.get('driver_skills', pd.DataFrame()).copy()
        
        if base_df.empty:
            raise ValueError("No driver skills data available - cannot proceed with feature engineering")
        
        print(f"   📊 Base dataset: {len(base_df):,} driver-seasons")
        
        # Add comprehensive race performance features
        base_df = self._add_enhanced_race_features(base_df, datasets.get('race_results', pd.DataFrame()))
        
        # Add constructor performance context
        base_df = self._add_enhanced_constructor_features(base_df, datasets.get('constructor_standings', pd.DataFrame()))
        
        # Add qualifying performance features
        base_df = self._add_enhanced_qualifying_features(base_df, datasets.get('qualifying_data', pd.DataFrame()))
        
        # Add career progression and experience features
        base_df = self._add_enhanced_career_features(base_df)
        
        # Add F1 era and regulation features
        base_df = self._add_enhanced_era_features(base_df)
        
        # Add circuit performance features
        base_df = self._add_circuit_performance_features(base_df, datasets.get('race_results', pd.DataFrame()), datasets.get('circuits', pd.DataFrame()))
        
        print(f"   📈 Engineered features: {base_df.shape[1]} columns")
        print(f"   📋 Dataset size: {len(base_df):,} samples")
        
        return base_df
    
    def _add_enhanced_race_features(self, base_df, race_results_df):
        """Add comprehensive race performance features"""
        
        if race_results_df.empty:
            logger.warning("No race results - using default race features")
            # Add default features
            base_df['races_entered'] = 16  # Average season length
            base_df['finish_rate'] = 0.75
            base_df['avg_finish_position'] = 12
            base_df['podium_rate'] = 0.1
            base_df['win_rate'] = 0.02
            base_df['dnf_rate'] = 0.25
            return base_df
        
        print("   🏁 Adding enhanced race performance features...")
        
        race_features = []
        
        for _, row in base_df.iterrows():
            driver_id = row['driver_id']
            season = row['season']
            
            # Get driver's season races
            driver_races = race_results_df[
                (race_results_df['driver_id'] == driver_id) & 
                (race_results_df['year'] == season)
            ]
            
            if not driver_races.empty:
                finished_races = driver_races[driver_races['finished'] == 1]
                
                # Core performance metrics
                stats = {
                    'races_entered': len(driver_races),
                    'races_finished': len(finished_races),
                    'finish_rate': len(finished_races) / len(driver_races) if len(driver_races) > 0 else 0,
                    'avg_finish_position': finished_races['finish_position'].mean() if len(finished_races) > 0 else 20,
                    'median_finish_position': finished_races['finish_position'].median() if len(finished_races) > 0 else 20,
                    'best_finish': finished_races['finish_position'].min() if len(finished_races) > 0 else 20,
                    'worst_finish': finished_races['finish_position'].max() if len(finished_races) > 0 else 20,
                    
                    # Podium and win metrics
                    'wins': (finished_races['finish_position'] == 1).sum(),
                    'win_rate': (finished_races['finish_position'] == 1).mean() if len(finished_races) > 0 else 0,
                    'podiums': (finished_races['finish_position'] <= 3).sum(),
                    'podium_rate': (finished_races['finish_position'] <= 3).mean() if len(finished_races) > 0 else 0,
                    'top_5_finishes': (finished_races['finish_position'] <= 5).sum(),
                    'top_5_rate': (finished_races['finish_position'] <= 5).mean() if len(finished_races) > 0 else 0,
                    'top_10_finishes': (finished_races['finish_position'] <= 10).sum(),
                    'top_10_rate': (finished_races['finish_position'] <= 10).mean() if len(finished_races) > 0 else 0,
                    
                    # Points and consistency
                    'total_points': driver_races['points'].sum(),
                    'avg_points_per_race': driver_races['points'].mean(),
                    'points_rate': (driver_races['points'] > 0).mean(),
                    'position_std': finished_races['finish_position'].std() if len(finished_races) > 1 else 5,
                    
                    # Grid and improvement metrics
                    'avg_grid_position': driver_races[driver_races['grid_position'] > 0]['grid_position'].mean() if (driver_races['grid_position'] > 0).any() else 15,
                    'grid_improvement': driver_races['grid_improvement'].mean() if 'grid_improvement' in driver_races.columns else 0,
                    
                    # DNF analysis
                    'dnf_count': (driver_races['finished'] == 0).sum(),
                    'dnf_rate': (driver_races['finished'] == 0).mean(),
                    
                    # Performance trend (within season)
                    'early_season_avg': finished_races[finished_races.index <= len(finished_races)//2]['finish_position'].mean() if len(finished_races) > 4 else 15,
                    'late_season_avg': finished_races[finished_races.index > len(finished_races)//2]['finish_position'].mean() if len(finished_races) > 4 else 15,
                }
                
                # Calculate improvement trend
                if len(finished_races) > 4:
                    stats['season_improvement'] = stats['early_season_avg'] - stats['late_season_avg']
                else:
                    stats['season_improvement'] = 0
                
            else:
                # Default values for drivers with no race data
                stats = {
                    'races_entered': 0, 'races_finished': 0, 'finish_rate': 0,
                    'avg_finish_position': 20, 'median_finish_position': 20,
                    'best_finish': 20, 'worst_finish': 20,
                    'wins': 0, 'win_rate': 0, 'podiums': 0, 'podium_rate': 0,
                    'top_5_finishes': 0, 'top_5_rate': 0, 'top_10_finishes': 0, 'top_10_rate': 0,
                    'total_points': 0, 'avg_points_per_race': 0, 'points_rate': 0,
                    'position_std': 5, 'avg_grid_position': 20, 'grid_improvement': 0,
                    'dnf_count': 0, 'dnf_rate': 0,
                    'early_season_avg': 20, 'late_season_avg': 20, 'season_improvement': 0
                }
            
            race_features.append(stats)
        
        # Add race features to dataframe
        race_features_df = pd.DataFrame(race_features)
        base_df = pd.concat([base_df.reset_index(drop=True), race_features_df.reset_index(drop=True)], axis=1)
        
        return base_df
    
    def _add_enhanced_constructor_features(self, base_df, constructor_standings_df):
        """Add enhanced constructor performance features"""
        
        if constructor_standings_df.empty:
            logger.warning("No constructor standings - using default constructor features")
            base_df['constructor_championship_position'] = 5
            base_df['constructor_competitiveness'] = 60
            base_df['constructor_dominance'] = 0.2
            return base_df
        
        print("   🏗️ Adding enhanced constructor features...")
        
        constructor_features = []
        
        for _, row in base_df.iterrows():
            constructor_id = row['constructor_id']
            season = row['season']
            
            constructor_season = constructor_standings_df[
                (constructor_standings_df['constructor_id'] == constructor_id) & 
                (constructor_standings_df['year'] == season)
            ]
            
            if not constructor_season.empty:
                constructor_data = constructor_season.iloc[0]
                
                stats = {
                    'constructor_championship_position': constructor_data['position'],
                    'constructor_championship_points': constructor_data['points'],
                    'constructor_wins': constructor_data['wins'],
                    'constructor_competitiveness': max(1, 11 - constructor_data['position']),  # 1-10 scale
                    'constructor_dominance': constructor_data['wins'] / 20 if constructor_data['wins'] > 0 else 0,  # Assuming ~20 races per season
                    'constructor_relative_performance': (11 - constructor_data['position']) / 10,  # 0-1 scale
                }
                
                # Historical constructor performance (if available)
                constructor_history = constructor_standings_df[
                    (constructor_standings_df['constructor_id'] == constructor_id) &
                    (constructor_standings_df['year'] < season) &
                    (constructor_standings_df['year'] >= season - 3)  # Last 3 years
                ]
                
                if not constructor_history.empty:
                    stats['constructor_avg_position_3yr'] = constructor_history['position'].mean()
                    stats['constructor_trend'] = constructor_history['position'].iloc[-1] - constructor_history['position'].iloc[0] if len(constructor_history) > 1 else 0
                else:
                    stats['constructor_avg_position_3yr'] = constructor_data['position']
                    stats['constructor_trend'] = 0
                
            else:
                # Default constructor values
                stats = {
                    'constructor_championship_position': 8,
                    'constructor_championship_points': 50,
                    'constructor_wins': 0,
                    'constructor_competitiveness': 3,
                    'constructor_dominance': 0,
                    'constructor_relative_performance': 0.3,
                    'constructor_avg_position_3yr': 8,
                    'constructor_trend': 0
                }
            
            constructor_features.append(stats)
        
        constructor_features_df = pd.DataFrame(constructor_features)
        base_df = pd.concat([base_df.reset_index(drop=True), constructor_features_df.reset_index(drop=True)], axis=1)
        
        return base_df
    
    def _add_enhanced_qualifying_features(self, base_df, qualifying_df):
        """Add enhanced qualifying performance features"""
        
        print("   🏁 Adding enhanced qualifying features...")
        
        qualifying_features = []
        
        for _, row in base_df.iterrows():
            driver_id = row['driver_id']
            season = row['season']
            
            driver_qualifying = qualifying_df[
                (qualifying_df['driver_id'] == driver_id) & 
                (qualifying_df['year'] == season)
            ] if not qualifying_df.empty else pd.DataFrame()
            
            if not driver_qualifying.empty:
                stats = {
                    'qualifying_sessions': len(driver_qualifying),
                    'avg_qualifying_position': driver_qualifying['position'].mean(),
                    'median_qualifying_position': driver_qualifying['position'].median(),
                    'best_qualifying': driver_qualifying['position'].min(),
                    'worst_qualifying': driver_qualifying['position'].max(),
                    'qualifying_consistency': driver_qualifying['position'].std(),
                    'front_row_starts': (driver_qualifying['position'] <= 2).sum(),
                    'front_row_rate': (driver_qualifying['position'] <= 2).mean(),
                    'top_5_qualifications': (driver_qualifying['position'] <= 5).sum(),
                    'top_5_qual_rate': (driver_qualifying['position'] <= 5).mean(),
                    'top_10_qualifications': (driver_qualifying['position'] <= 10).sum(),
                    'top_10_qual_rate': (driver_qualifying['position'] <= 10).mean(),
                    'pole_positions': (driver_qualifying['position'] == 1).sum(),
                    'pole_rate': (driver_qualifying['position'] == 1).mean()
                }
                
                # Qualifying to race conversion (if race data available)
                if 'finish_position' in base_df.columns:
                    # This would need race results correlation - simplified for now
                    stats['qualifying_performance_score'] = 100 - (stats['avg_qualifying_position'] * 4)
                else:
                    stats['qualifying_performance_score'] = 100 - (stats['avg_qualifying_position'] * 4)
                
            else:
                # Default qualifying values
                stats = {
                    'qualifying_sessions': 0,
                    'avg_qualifying_position': 15,
                    'median_qualifying_position': 15,
                    'best_qualifying': 20,
                    'worst_qualifying': 20,
                    'qualifying_consistency': 5,
                    'front_row_starts': 0,
                    'front_row_rate': 0,
                    'top_5_qualifications': 0,
                    'top_5_qual_rate': 0,
                    'top_10_qualifications': 0,
                    'top_10_qual_rate': 0,
                    'pole_positions': 0,
                    'pole_rate': 0,
                    'qualifying_performance_score': 40
                }
            
            qualifying_features.append(stats)
        
        qualifying_features_df = pd.DataFrame(qualifying_features)
        base_df = pd.concat([base_df.reset_index(drop=True), qualifying_features_df.reset_index(drop=True)], axis=1)
        
        return base_df
    
    def _add_enhanced_career_features(self, base_df):
        """Add enhanced career progression features"""
        
        print("   👤 Adding enhanced career features...")
        
        # Sort by driver and season
        base_df = base_df.sort_values(['driver_id', 'season'])
        
        career_features = []
        
        for driver_id in base_df['driver_id'].unique():
            driver_data = base_df[base_df['driver_id'] == driver_id].copy()
            
            for idx, row in driver_data.iterrows():
                season = row['season']
                
                # Basic career metrics
                career_year = (driver_data['season'] <= season).sum()
                debut_year = driver_data['season'].min()
                years_since_debut = season - debut_year
                career_span = driver_data['season'].max() - driver_data['season'].min() + 1
                
                # Career stage classification
                if career_year <= 2:
                    career_stage = 'rookie'
                    career_stage_numeric = 1
                elif career_year <= 5:
                    career_stage = 'developing'
                    career_stage_numeric = 2
                elif career_year <= 10:
                    career_stage = 'prime'
                    career_stage_numeric = 3
                elif career_year <= 15:
                    career_stage = 'experienced'
                    career_stage_numeric = 4
                else:
                    career_stage = 'veteran'
                    career_stage_numeric = 5
                
                # Performance trends
                career_data = driver_data[driver_data['season'] <= season]
                
                if len(career_data) >= 2:
                    # Skill progression
                    skill_values = career_data['skill_rating'].values
                    career_best_skill = skill_values.max()
                    career_avg_skill = skill_values.mean()
                    current_vs_best = row['skill_rating'] / career_best_skill if career_best_skill > 0 else 1
                    
                    # Recent form (last 3 seasons)
                    recent_seasons = career_data.tail(min(3, len(career_data)))
                    if len(recent_seasons) >= 2:
                        recent_trend = recent_seasons['skill_rating'].diff().mean()
                    else:
                        recent_trend = 0
                    
                    # Peak performance indicator
                    is_career_peak = row['skill_rating'] >= (career_best_skill * 0.95)
                    
                else:
                    career_best_skill = row['skill_rating']
                    career_avg_skill = row['skill_rating']
                    current_vs_best = 1.0
                    recent_trend = 0
                    is_career_peak = True
                
                # Championship achievements
                championships = (career_data['championship_position'] == 1).sum()
                top_3_championships = (career_data['championship_position'] <= 3).sum()
                
                career_features.append({
                    'career_year': career_year,
                    'years_since_debut': years_since_debut,
                    'career_span': career_span,
                    'career_stage': career_stage,
                    'career_stage_numeric': career_stage_numeric,
                    'career_best_skill': career_best_skill,
                    'career_avg_skill': career_avg_skill,
                    'current_vs_best': current_vs_best,
                    'recent_form_trend': recent_trend,
                    'is_career_peak': is_career_peak,
                    'career_championships': championships,
                    'career_top_3_championships': top_3_championships,
                    'championship_rate': championships / career_year if career_year > 0 else 0,
                    'experience_factor': min(1.0, career_year / 10)  # Normalize to 0-1
                })
        
        career_features_df = pd.DataFrame(career_features)
        base_df = pd.concat([base_df.reset_index(drop=True), career_features_df.reset_index(drop=True)], axis=1)
        
        return base_df
    
    def _add_enhanced_era_features(self, base_df):
        """Add enhanced F1 era and regulation features"""
        
        print("   🏎️ Adding enhanced F1 era features...")
        
        def get_detailed_f1_era(year):
            """Detailed F1 era classification"""
            if year <= 1960:
                return 'foundation_era'
            elif year <= 1966:
                return 'early_championship'
            elif year <= 1982:
                return 'classic_era'
            elif year <= 1988:
                return 'turbo_beginning'
            elif year <= 1994:
                return 'turbo_era'
            elif year <= 2005:
                return 'modern_naturally_aspirated'
            elif year <= 2008:
                return 'aero_development'
            elif year <= 2013:
                return 'v8_era'
            elif year <= 2016:
                return 'hybrid_introduction'
            elif year <= 2021:
                return 'hybrid_dominance'
            else:
                return 'ground_effect_era'
        
        def get_points_system_detailed(year):
            """Detailed points system classification"""
            if year <= 1959:
                return 'early_system'
            elif year <= 1990:
                return 'classic_9_points'
            elif year <= 2002:
                return 'expanded_10_points'
            elif year <= 2009:
                return 'points_to_8th'
            else:
                return 'current_25_points'
        
        def get_competitiveness_level(year):
            """Historical competitiveness analysis"""
            # Based on historical analysis of championship battles
            highly_competitive = [1976, 1981, 1982, 1986, 1994, 1997, 1999, 2003, 2006, 2007, 2008, 2010, 2012, 2016, 2021]
            moderately_competitive = [1977, 1983, 1985, 1991, 1996, 1998, 2000, 2005, 2009, 2017, 2018, 2022, 2023]
            dominant_seasons = [1988, 1992, 1993, 2002, 2004, 2011, 2013, 2014, 2015, 2019, 2020]
            
            if year in highly_competitive:
                return 0.9
            elif year in moderately_competitive:
                return 0.7
            elif year in dominant_seasons:
                return 0.3
            else:
                return 0.5  # Default moderate
        
        def get_regulation_stability(year):
            """Regulation change impact"""
            major_reg_changes = [1961, 1966, 1968, 1983, 1989, 1995, 1998, 2006, 2009, 2014, 2017, 2022]
            
            # Check if year is within 2 years of major regulation change
            for change_year in major_reg_changes:
                if abs(year - change_year) <= 1:
                    return 0.3  # Low stability
            
            return 0.8  # High stability
        
        # Apply era features
        base_df['f1_era'] = base_df['season'].apply(get_detailed_f1_era)
        base_df['points_system'] = base_df['season'].apply(get_points_system_detailed)
        base_df['competitiveness_level'] = base_df['season'].apply(get_competitiveness_level)
        base_df['regulation_stability'] = base_df['season'].apply(get_regulation_stability)
        
        # Numeric era encoding
        era_mapping = {
            'foundation_era': 1, 'early_championship': 2, 'classic_era': 3,
            'turbo_beginning': 4, 'turbo_era': 5, 'modern_naturally_aspirated': 6,
            'aero_development': 7, 'v8_era': 8, 'hybrid_introduction': 9,
            'hybrid_dominance': 10, 'ground_effect_era': 11
        }
        base_df['era_numeric'] = base_df['f1_era'].map(era_mapping)
        
        # Technology advancement factor
        base_df['technology_advancement'] = (base_df['season'] - 1950) / (2025 - 1950)  # 0-1 scale
        
        return base_df
    
    def _add_circuit_performance_features(self, base_df, race_results_df, circuits_df):
        """Add circuit-specific performance features"""
        
        print("   🏁 Adding circuit performance features...")
        
        if race_results_df.empty:
            # Default circuit features
            base_df['avg_performance_street_circuits'] = 60
            base_df['avg_performance_high_speed'] = 60
            base_df['avg_performance_technical'] = 60
            return base_df
        
        # Circuit classifications (simplified)
        street_circuits = ['monaco', 'singapore', 'adelaide', 'detroit', 'phoenix']
        high_speed_circuits = ['monza', 'spa', 'silverstone', 'indianapolis', 'avus']
        technical_circuits = ['hungary', 'monaco', 'imola', 'suzuka', 'barcelona']
        
        circuit_features = []
        
        for _, row in base_df.iterrows():
            driver_id = row['driver_id']
            
            # Get all career races for this driver
            driver_career_races = race_results_df[race_results_df['driver_id'] == driver_id]
            
            if not driver_career_races.empty:
                # Street circuit performance
                street_races = driver_career_races[driver_career_races['circuit_id'].isin(street_circuits)]
                if not street_races.empty and len(street_races[street_races['finished'] == 1]) > 0:
                    street_performance = 100 - (street_races[street_races['finished'] == 1]['finish_position'].mean() * 4)
                else:
                    street_performance = 60
                
                # High-speed circuit performance
                high_speed_races = driver_career_races[driver_career_races['circuit_id'].isin(high_speed_circuits)]
                if not high_speed_races.empty and len(high_speed_races[high_speed_races['finished'] == 1]) > 0:
                    high_speed_performance = 100 - (high_speed_races[high_speed_races['finished'] == 1]['finish_position'].mean() * 4)
                else:
                    high_speed_performance = 60
                
                # Technical circuit performance
                technical_races = driver_career_races[driver_career_races['circuit_id'].isin(technical_circuits)]
                if not technical_races.empty and len(technical_races[technical_races['finished'] == 1]) > 0:
                    technical_performance = 100 - (technical_races[technical_races['finished'] == 1]['finish_position'].mean() * 4)
                else:
                    technical_performance = 60
                
                stats = {
                    'avg_performance_street_circuits': max(0, min(100, street_performance)),
                    'avg_performance_high_speed': max(0, min(100, high_speed_performance)),
                    'avg_performance_technical': max(0, min(100, technical_performance)),
                    'career_circuits_raced': driver_career_races['circuit_id'].nunique(),
                    'career_total_races': len(driver_career_races)
                }
            else:
                stats = {
                    'avg_performance_street_circuits': 60,
                    'avg_performance_high_speed': 60,
                    'avg_performance_technical': 60,
                    'career_circuits_raced': 0,
                    'career_total_races': 0
                }
            
            circuit_features.append(stats)
        
        circuit_features_df = pd.DataFrame(circuit_features)
        base_df = pd.concat([base_df.reset_index(drop=True), circuit_features_df.reset_index(drop=True)], axis=1)
        
        return base_df
    
    def _enrich_features_advanced(self, feature_df, datasets):
        """Enhanced feature enrichment with duplicate column handling"""

        print("   ⚡ Advanced feature enrichment with duplicate removal...")

        # Remove any existing duplicate columns first
        feature_df = feature_df.loc[:, ~feature_df.columns.duplicated()]

        # Add FastF1 insights if available
        fastf1_df = datasets.get('fastf1_data', pd.DataFrame())
        if not fastf1_df.empty:
            feature_df = self._add_fastf1_insights(feature_df, fastf1_df)

        # Add weather adaptability if available  
        weather_df = datasets.get('weather_data', pd.DataFrame())
        if not weather_df.empty:
            feature_df = self._add_weather_adaptability(feature_df, weather_df)

        # Advanced derived features
        feature_df = self._create_advanced_derived_features_fixed(feature_df)

        # Final duplicate removal
        feature_df = feature_df.loc[:, ~feature_df.columns.duplicated()]

        return feature_df
    
    def _add_fastf1_insights(self, feature_df, fastf1_df):
        """Add insights from FastF1 telemetry data with safety checks"""

        print("     📡 Adding FastF1 telemetry insights...")

        # Default insights for all drivers
        default_insights = {
            'pace_consistency_score': 60,
            'sector_balance_score': 60, 
            'tyre_management_score': 60,
            'telemetry_data_quality': 0
        }

        fastf1_insights = []

        for _, row in feature_df.iterrows():
            insights = default_insights.copy()

            # Try to match with FastF1 data if available
            if 'driver' in fastf1_df.columns and 'lap_time_seconds' in fastf1_df.columns:
                driver_name = row.get('driver_name', '')
                if driver_name and len(driver_name.split()) > 0:
                    last_name = driver_name.split()[-1]

                    driver_telemetry = fastf1_df[
                        fastf1_df['driver'].str.contains(last_name, case=False, na=False)
                    ]

                    if not driver_telemetry.empty and len(driver_telemetry) > 5:
                        try:
                            lap_times = driver_telemetry['lap_time_seconds']
                            if len(lap_times) > 0 and lap_times.std() > 0:
                                pace_consistency = min(100, 1 / (1 + lap_times.std()) * 100)
                                insights['pace_consistency_score'] = pace_consistency
                                insights['telemetry_data_quality'] = min(100, len(driver_telemetry) / 50 * 100)
                        except Exception as e:
                            pass  # Use defaults

            fastf1_insights.append(insights)

        # Add insights to dataframe
        fastf1_insights_df = pd.DataFrame(fastf1_insights)
        feature_df = pd.concat([feature_df.reset_index(drop=True), fastf1_insights_df.reset_index(drop=True)], axis=1)

        # Remove any duplicate columns
        feature_df = feature_df.loc[:, ~feature_df.columns.duplicated()]

        return feature_df

    def _add_weather_adaptability(self, feature_df, weather_df):
        """Add weather adaptability features with safety"""

        print("     🌧️ Adding weather adaptability features...")

        # Simple weather adaptability features (defaults for all drivers)
        weather_features = []

        for _, row in feature_df.iterrows():
            # Use reasonable defaults with some variation
            adaptability = {
                'wet_weather_performance': max(30, min(90, 60 + np.random.normal(0, 8))),
                'temperature_adaptability': max(30, min(90, 60 + np.random.normal(0, 6))),
                'wind_adaptability': max(30, min(90, 60 + np.random.normal(0, 4)))
            }
            weather_features.append(adaptability)

        weather_features_df = pd.DataFrame(weather_features)
        feature_df = pd.concat([feature_df.reset_index(drop=True), weather_features_df.reset_index(drop=True)], axis=1)

        # Remove duplicate columns
        feature_df = feature_df.loc[:, ~feature_df.columns.duplicated()]

        return feature_df

    
    def _create_advanced_derived_features_fixed(self, feature_df):
        """Create advanced derived features with safe handling"""

        print("     🔬 Creating advanced derived features safely...")

        # Remove duplicate columns first
        feature_df = feature_df.loc[:, ~feature_df.columns.duplicated()]

        # Ensure required columns exist with safe defaults
        if 'experience_factor' not in feature_df.columns:
            feature_df['experience_factor'] = 0.5

        if 'skill_rating' not in feature_df.columns:
            print("     ⚠️  Warning: skill_rating column missing")
            return feature_df

        # Clean and normalize the data
        feature_df['experience_factor'] = feature_df['experience_factor'].fillna(0.5)
        feature_df['skill_rating'] = feature_df['skill_rating'].fillna(feature_df['skill_rating'].mean())

        # Convert to float and clip values
        feature_df['experience_factor'] = pd.to_numeric(feature_df['experience_factor'], errors='coerce').fillna(0.5)
        feature_df['skill_rating'] = pd.to_numeric(feature_df['skill_rating'], errors='coerce').fillna(feature_df['skill_rating'].mean())

        # Clip to reasonable ranges
        feature_df['experience_factor'] = feature_df['experience_factor'].clip(0, 1)
        feature_df['skill_rating'] = feature_df['skill_rating'].clip(25, 100)

        # Create derived features safely
        try:
            # Performance efficiency metrics
            if 'avg_finish_position' in feature_df.columns and 'constructor_competitiveness' in feature_df.columns:
                feature_df['driver_vs_car_performance'] = (
                    (100 - feature_df['avg_finish_position'] * 4) / 
                    (feature_df['constructor_competitiveness'] + 1)
                )

            # Consistency vs speed trade-off  
            if 'position_std' in feature_df.columns and 'avg_finish_position' in feature_df.columns:
                feature_df['consistency_vs_speed'] = (
                    (1 / (feature_df['position_std'] + 1)) * 
                    (100 - feature_df['avg_finish_position'] * 4)
                )

            # Experience-adjusted performance
            feature_df['experience_adjusted_skill'] = (
                feature_df['skill_rating'] * (0.7 + 0.3 * feature_df['experience_factor'])
            )

            # Era-normalized performance
            if 'competitiveness_level' in feature_df.columns:
                feature_df['era_normalized_skill'] = (
                    feature_df['skill_rating'] * feature_df['competitiveness_level']
                )
            else:
                feature_df['era_normalized_skill'] = feature_df['skill_rating']

            # Qualifying-to-race conversion
            if 'avg_qualifying_position' in feature_df.columns and 'avg_finish_position' in feature_df.columns:
                feature_df['qualifying_race_conversion'] = (
                    feature_df['avg_qualifying_position'] - feature_df['avg_finish_position']
                )

        except Exception as e:
            print(f"     ⚠️  Warning: Error creating derived features: {e}")

        # Final cleanup - remove any duplicate columns created
        feature_df = feature_df.loc[:, ~feature_df.columns.duplicated()]

        return feature_df
    
    def _prepare_enhanced_ml_datasets(self, feature_df):
        """Prepare enhanced ML datasets with robust error handling"""

        # Handle missing values with advanced imputation
        feature_df = self._handle_missing_values_advanced(feature_df)

        # Encode categorical variables
        feature_df = self._encode_categorical_variables(feature_df)

        # Feature selection and engineering
        ml_features = self._select_ml_features(feature_df)

        # Create train/validation/test splits
        X, y = self._create_feature_target_split(ml_features)

        # Ensure minimum dataset size
        if len(X) < 10:
            raise ValueError(f"Dataset too small ({len(X)} samples). Need at least 10 samples for ML training.")

        # Create splits with robust handling
        train_val_test_splits = self._create_stratified_splits(X, y)

        # Feature scaling with robust techniques
        scaled_splits = self._apply_robust_scaling(train_val_test_splits)

        # Prepare final ML datasets
        ml_datasets = self._finalize_ml_datasets(scaled_splits, ml_features)

        return ml_datasets

    
    def _handle_missing_values_advanced(self, feature_df):
        """Advanced missing value handling"""
        
        print("   🔧 Advanced missing value imputation...")
        
        # Separate numeric and categorical columns
        numeric_columns = feature_df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_columns = feature_df.select_dtypes(include=['object']).columns.tolist()
        
        # Remove target and ID columns from imputation
        id_columns = ['driver_id', 'season', 'constructor_id', 'driver_name']
        target_column = 'skill_rating'
        
        numeric_columns = [col for col in numeric_columns if col not in id_columns + [target_column]]
        categorical_columns = [col for col in categorical_columns if col not in id_columns]
        
        # Numeric imputation (median for robustness)
        if numeric_columns:
            numeric_imputer = SimpleImputer(strategy='median')
            feature_df[numeric_columns] = numeric_imputer.fit_transform(feature_df[numeric_columns])
            self.imputers['numeric'] = numeric_imputer
        
        # Categorical imputation (most frequent)
        if categorical_columns:
            categorical_imputer = SimpleImputer(strategy='most_frequent')
            feature_df[categorical_columns] = categorical_imputer.fit_transform(feature_df[categorical_columns])
            self.imputers['categorical'] = categorical_imputer
        
        return feature_df
    
    def _encode_categorical_variables(self, feature_df):
        """Encode categorical variables"""
        
        print("   🏷️ Encoding categorical variables...")
        
        categorical_features = ['career_stage', 'f1_era', 'points_system']
        
        for feature in categorical_features:
            if feature in feature_df.columns:
                le = LabelEncoder()
                feature_df[f'{feature}_encoded'] = le.fit_transform(feature_df[feature].astype(str))
                self.encoders[feature] = le
        
        return feature_df
    
    def _select_ml_features(self, feature_df):
        """Select and prepare features for ML"""
        
        print("   🎯 Selecting ML features...")
        
        # Define feature categories
        target_features = ['skill_rating']
        
        id_features = ['driver_id', 'driver_name', 'season', 'constructor_id']
        
        core_performance_features = [
            'championship_position', 'points', 'wins',
            'race_performance_score', 'championship_performance_score',
            'consistency_score', 'experience_factor'
        ]
        
        race_features = [
            'races_entered', 'finish_rate', 'avg_finish_position',
            'podium_rate', 'win_rate', 'top_5_rate', 'top_10_rate',
            'dnf_rate', 'position_std', 'grid_improvement'
        ]
        
        constructor_features = [
            'constructor_championship_position', 'constructor_competitiveness',
            'constructor_relative_performance'
        ]
        
        qualifying_features = [
            'avg_qualifying_position', 'qualifying_consistency',
            'front_row_rate', 'top_10_qual_rate'
        ]
        
        career_features = [
            'career_year', 'years_since_debut', 'career_stage_numeric',
            'current_vs_best', 'recent_form_trend', 'experience_factor'
        ]
        
        era_features = [
            'era_numeric', 'competitiveness_level', 'regulation_stability',
            'technology_advancement'
        ]
        
        circuit_features = [
            'avg_performance_street_circuits', 'avg_performance_high_speed',
            'avg_performance_technical'
        ]
        
        advanced_features = [
            'pace_consistency_score', 'sector_balance_score',
            'tyre_management_score', 'driver_vs_car_performance',
            'consistency_vs_speed', 'experience_adjusted_skill',
            'era_normalized_skill'
        ]
        
        # Combine all feature lists
        all_features = (target_features + id_features + core_performance_features +
                       race_features + constructor_features + qualifying_features +
                       career_features + era_features + circuit_features + advanced_features)
        
        # Filter to available columns
        available_features = [col for col in all_features if col in feature_df.columns]
        ml_features_df = feature_df[available_features].copy()
        
        print(f"     📊 Selected {len(available_features)} features")
        
        return ml_features_df
    
    def _create_feature_target_split(self, ml_features_df):
        """Create feature and target split"""
        
        target_col = 'skill_rating'
        id_cols = ['driver_id', 'driver_name', 'season', 'constructor_id']
        
        # Features (exclude target and IDs)
        feature_cols = [col for col in ml_features_df.columns if col not in [target_col] + id_cols]
        
        X = ml_features_df[feature_cols].copy()
        y = ml_features_df[target_col].copy()
        
        # Store ID information for later use
        id_info = ml_features_df[id_cols].copy()
        
        return X, y
    
    def _create_stratified_splits(self, X, y):
        """Create stratified train/validation/test splits with safe handling"""

        print("   🎲 Creating stratified data splits...")

        try:
            # Create stratification bins for continuous target (fewer bins for small dataset)
            n_bins = min(3, len(y) // 10)  # Adaptive binning based on dataset size
            if n_bins < 2:
                n_bins = 2

            y_binned = pd.cut(y, bins=n_bins, labels=[f'bin_{i}' for i in range(n_bins)])

            # Check for bins with insufficient samples
            bin_counts = y_binned.value_counts()
            small_bins = bin_counts[bin_counts < 2]

            if not small_bins.empty:
                print(f"     ⚠️  Warning: {len(small_bins)} bins have <2 samples, using non-stratified split")
                # Fall back to random split without stratification
                X_train, X_temp, y_train, y_temp = train_test_split(
                    X, y, test_size=0.3, random_state=42
                )
                X_val, X_test, y_val, y_test = train_test_split(
                    X_temp, y_temp, test_size=0.5, random_state=42
                )
            else:
                # Proceed with stratified split
                X_train, X_temp, y_train, y_temp, y_train_binned, y_temp_binned = train_test_split(
                    X, y, y_binned, 
                    test_size=0.3, 
                    random_state=42, 
                    stratify=y_binned
                )

                # Second split for validation/test
                X_val, X_test, y_val, y_test = train_test_split(
                    X_temp, y_temp, 
                    test_size=0.5, 
                    random_state=42, 
                    stratify=y_temp_binned
                )

        except Exception as e:
            print(f"     ⚠️  Stratified split failed: {e}")
            print("     🔄 Falling back to random split...")

            # Fallback to simple random split
            X_train, X_temp, y_train, y_temp = train_test_split(
                X, y, test_size=0.3, random_state=42
            )
            X_val, X_test, y_val, y_test = train_test_split(
                X_temp, y_temp, test_size=0.5, random_state=42
            )

        splits = {
            'X_train': X_train,
            'X_val': X_val, 
            'X_test': X_test,
            'y_train': y_train,
            'y_val': y_val,
            'y_test': y_test
        }

        print(f"     📊 Split sizes - Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

        return splits

    
    def _apply_robust_scaling(self, splits):
        """Apply robust scaling to features"""
        
        print("   📏 Applying robust feature scaling...")
        
        # Use RobustScaler for better handling of outliers
        scaler = RobustScaler()
        
        # Fit on training data only
        X_train_scaled = pd.DataFrame(
            scaler.fit_transform(splits['X_train']),
            columns=splits['X_train'].columns,
            index=splits['X_train'].index
        )
        
        # Transform validation and test data
        X_val_scaled = pd.DataFrame(
            scaler.transform(splits['X_val']),
            columns=splits['X_val'].columns,
            index=splits['X_val'].index
        )
        
        X_test_scaled = pd.DataFrame(
            scaler.transform(splits['X_test']),
            columns=splits['X_test'].columns,
            index=splits['X_test'].index
        )
        
        # Store scaler
        self.scalers['feature_scaler'] = scaler
        
        # Update splits with scaled data
        splits.update({
            'X_train': X_train_scaled,
            'X_val': X_val_scaled,
            'X_test': X_test_scaled
        })
        
        return splits
    
    def _finalize_ml_datasets(self, splits, ml_features_df):
        """Finalize ML datasets with metadata"""
        
        feature_names = list(splits['X_train'].columns)
        
        ml_datasets = {
            **splits,
            'feature_names': feature_names,
            'full_dataset': ml_features_df,
            'metadata': {
                'n_samples': len(ml_features_df),
                'n_features': len(feature_names),
                'target_range': (ml_features_df['skill_rating'].min(), ml_features_df['skill_rating'].max()),
                'target_mean': ml_features_df['skill_rating'].mean(),
                'target_std': ml_features_df['skill_rating'].std(),
                'train_samples': len(splits['X_train']),
                'val_samples': len(splits['X_val']),
                'test_samples': len(splits['X_test']),
                'feature_categories': {
                    'performance': ['championship_position', 'race_performance_score', 'avg_finish_position'],
                    'consistency': ['position_std', 'consistency_score'],
                    'experience': ['career_year', 'experience_factor'],
                    'constructor': ['constructor_competitiveness'],
                    'era': ['era_numeric', 'competitiveness_level']
                }
            }
        }
        
        return ml_datasets
    
    def _save_enhanced_ml_datasets(self, ml_datasets):
        """Save enhanced ML datasets with duplicate column handling"""

        print("   💾 Saving ML-ready datasets...")

        # Clean duplicate columns from all datasets before saving
        def clean_duplicates(df):
            """Remove duplicate columns keeping first occurrence"""
            return df.loc[:, ~df.columns.duplicated(keep='first')]

        # Clean each dataset
        X_train_clean = clean_duplicates(ml_datasets['X_train'])
        X_val_clean = clean_duplicates(ml_datasets['X_val'])
        X_test_clean = clean_duplicates(ml_datasets['X_test'])

        # Save cleaned datasets
        X_train_clean.to_parquet(self.processed_dir / 'X_train_enhanced.parquet')
        X_val_clean.to_parquet(self.processed_dir / 'X_val_enhanced.parquet')  
        X_test_clean.to_parquet(self.processed_dir / 'X_test_enhanced.parquet')

        # Save targets (these should be clean)
        pd.Series(ml_datasets['y_train'], name='skill_rating').to_frame().to_parquet(self.processed_dir / 'y_train_enhanced.parquet')
        pd.Series(ml_datasets['y_val'], name='skill_rating').to_frame().to_parquet(self.processed_dir / 'y_val_enhanced.parquet')
        pd.Series(ml_datasets['y_test'], name='skill_rating').to_frame().to_parquet(self.processed_dir / 'y_test_enhanced.parquet')

        # Clean and save full dataset
        if 'full_dataset' in ml_datasets:
            full_dataset_clean = clean_duplicates(ml_datasets['full_dataset'])
            full_dataset_clean.to_parquet(self.processed_dir / 'full_enhanced_dataset.parquet')

        # Save preprocessing objects
        import joblib
        joblib.dump(self.scalers, self.processed_dir / 'enhanced_scalers.pkl')
        joblib.dump(self.encoders, self.processed_dir / 'enhanced_encoders.pkl')
        joblib.dump(self.imputers, self.processed_dir / 'enhanced_imputers.pkl')

        # Update feature names to reflect cleaned columns
        cleaned_feature_names = X_train_clean.columns.tolist()

        # Save cleaned feature names
        with open(self.processed_dir / 'enhanced_feature_names.json', 'w') as f:
            json.dump(cleaned_feature_names, f, indent=2)

        # Update and save metadata
        updated_metadata = ml_datasets.get('metadata', {}).copy()
        updated_metadata.update({
            'n_features_final': len(cleaned_feature_names),
            'duplicate_columns_removed': len(ml_datasets['feature_names']) - len(cleaned_feature_names) if 'feature_names' in ml_datasets else 0,
            'final_feature_names': cleaned_feature_names
        })

        with open(self.processed_dir / 'enhanced_ml_metadata.json', 'w') as f:
            json.dump(updated_metadata, f, indent=2, default=str)

        print(f"   📁 Enhanced ML datasets saved to: {self.processed_dir}")
        print(f"   📊 Training samples: {len(X_train_clean):,}")
        print(f"   📊 Validation samples: {len(X_val_clean):,}")
        print(f"   📊 Test samples: {len(X_test_clean):,}")
        print(f"   📈 Final features: {len(cleaned_feature_names)} (duplicates removed)")


def main():
    """Run the enhanced feature engineering pipeline"""
    
    print("🚀 Enhanced F1 Feature Engineering Pipeline")
    print("Optimized for limited dataset scenarios with advanced techniques")
    print("="*70)
    
    feature_engineer = EnhancedF1FeatureEngineer()
    ml_datasets = feature_engineer.process_enhanced_dataset()
    
    print("\n🎯 Enhanced Feature Engineering Summary:")
    print(f"   📊 Total samples: {ml_datasets['metadata']['n_samples']:,}")
    print(f"   📈 Features engineered: {ml_datasets['metadata']['n_features']}")
    print(f"   🎯 Target range: {ml_datasets['metadata']['target_range'][0]:.1f} - {ml_datasets['metadata']['target_range'][1]:.1f}")
    print(f"   📊 Target mean: {ml_datasets['metadata']['target_mean']:.1f}")
    print(f"   🚀 Ready for enhanced ML model training!")
    
    return ml_datasets

if __name__ == "__main__":
    main()
