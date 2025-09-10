"""
Advanced F1 ML Model Training Pipeline - Production Grade
Trains ensemble models optimized for limited historical F1 data
Designed for cross-era driver skill prediction and race simulation
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import GridSearchCV, cross_val_score, KFold
from sklearn.ensemble import VotingRegressor
import xgboost as xgb
import lightgbm as lgb
from scipy import stats
import warnings
import json
import logging
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedF1MLTrainer:
    """
    Advanced ML trainer optimized for limited F1 historical data
    Uses ensemble methods and advanced techniques for maximum accuracy
    """
    
    def __init__(self, data_dir='data/ml_ready'):
        self.data_dir = Path(data_dir)
        self.models_dir = Path('models/trained')
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.models = {}
        self.ensemble_model = None
        self.feature_importance = {}
        self.performance_metrics = {}
        
    def train_advanced_models(self):
        """Train advanced ensemble models for F1 driver skill prediction"""
        
        print("🚀 Advanced F1 ML Model Training Pipeline")
        print("📊 Optimized for limited data with ensemble techniques")
        print("="*70)
        
        # Load processed datasets
        print("📥 Loading processed ML datasets...")
        datasets = self._load_ml_datasets()
        
        # Train individual models
        print("🎯 Training individual models...")
        individual_models = self._train_individual_models(datasets)
        
        # Create ensemble model
        print("🤝 Creating ensemble model...")
        ensemble_model = self._create_ensemble_model(datasets, individual_models)
        
        # Advanced model evaluation
        print("📊 Advanced model evaluation...")
        evaluation_results = self._evaluate_models_comprehensive(datasets, individual_models, ensemble_model)
        
        # Feature importance analysis
        print("🔍 Feature importance analysis...")
        importance_analysis = self._analyze_feature_importance(datasets, individual_models)
        
        # Model interpretability
        print("🧠 Model interpretability analysis...")
        interpretability_results = self._analyze_model_interpretability(datasets, ensemble_model)
        
        # Save trained models
        print("💾 Saving trained models...")
        self._save_trained_models(individual_models, ensemble_model, evaluation_results, importance_analysis)
        
        # Generate comprehensive report
        print("📋 Generating training report...")
        training_report = self._generate_training_report(
            evaluation_results, importance_analysis, interpretability_results, datasets
        )
        
        print("✅ Advanced ML training completed!")
        return {
            'models': individual_models,
            'ensemble': ensemble_model,
            'evaluation': evaluation_results,
            'importance': importance_analysis,
            'report': training_report
        }
    
    def _load_ml_datasets(self):
        """Load processed ML datasets"""
        
        datasets = {}
        
        try:
            datasets['X_train'] = pd.read_parquet(self.data_dir / 'X_train_enhanced.parquet')
            datasets['X_val'] = pd.read_parquet(self.data_dir / 'X_val_enhanced.parquet')
            datasets['X_test'] = pd.read_parquet(self.data_dir / 'X_test_enhanced.parquet')
            
            datasets['y_train'] = pd.read_parquet(self.data_dir / 'y_train_enhanced.parquet')['skill_rating']
            datasets['y_val'] = pd.read_parquet(self.data_dir / 'y_val_enhanced.parquet')['skill_rating']
            datasets['y_test'] = pd.read_parquet(self.data_dir / 'y_test_enhanced.parquet')['skill_rating']
            
            # Load metadata
            with open(self.data_dir / 'enhanced_ml_metadata.json', 'r') as f:
                datasets['metadata'] = json.load(f)
            
            # Load feature names
            with open(self.data_dir / 'enhanced_feature_names.json', 'r') as f:
                datasets['feature_names'] = json.load(f)
            
            logger.info(f"Loaded datasets - Train: {len(datasets['X_train'])}, Val: {len(datasets['X_val'])}, Test: {len(datasets['X_test'])}")
            
        except Exception as e:
            logger.error(f"Error loading datasets: {e}")
            raise
        
        return datasets
    
    def _train_individual_models(self, datasets):
        """Train individual models with optimized hyperparameters"""
        
        X_train = datasets['X_train']
        y_train = datasets['y_train']
        X_val = datasets['X_val']
        y_val = datasets['y_val']
        
        models = {}
        
        # 1. Random Forest (robust for limited data)
        print("   🌲 Training Random Forest...")
        rf_model = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train, y_train)
        models['random_forest'] = rf_model
        
        # 2. Gradient Boosting (excellent for structured data)
        print("   🚀 Training Gradient Boosting...")
        gb_model = GradientBoostingRegressor(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=8,
            min_samples_split=10,
            min_samples_leaf=4,
            subsample=0.8,
            random_state=42
        )
        gb_model.fit(X_train, y_train)
        models['gradient_boosting'] = gb_model
        
        # 3. XGBoost (advanced boosting)
        print("   ⚡ Training XGBoost...")
        xgb_model = xgb.XGBRegressor(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=6,
            min_child_weight=3,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1,
            random_state=42,
            n_jobs=-1,
            verbosity=0
        )
        xgb_model.fit(X_train, y_train)
        models['xgboost'] = xgb_model
        
        # 4. LightGBM (efficient and accurate)
        print("   💡 Training LightGBM...")
        lgb_model = lgb.LGBMRegressor(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=8,
            min_child_samples=10,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1,
            random_state=42,
            n_jobs=-1,
            verbosity=-1
        )
        lgb_model.fit(X_train, y_train)
        models['lightgbm'] = lgb_model
        
        # 5. Extra Trees (variance reduction)
        print("   🌳 Training Extra Trees...")
        et_model = ExtraTreesRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1
        )
        et_model.fit(X_train, y_train)
        models['extra_trees'] = et_model
        
        # 6. Ridge Regression (regularized linear)
        print("   📏 Training Ridge Regression...")
        ridge_model = Ridge(alpha=1.0, random_state=42)
        ridge_model.fit(X_train, y_train)
        models['ridge'] = ridge_model
        
        # 7. Support Vector Regression (non-linear patterns)
        print("   🎯 Training SVR...")
        svr_model = SVR(
            kernel='rbf',
            C=1.0,
            gamma='scale',
            epsilon=0.1
        )
        svr_model.fit(X_train, y_train)
        models['svr'] = svr_model
        
        # Evaluate individual models
        print("   📊 Evaluating individual models...")
        for name, model in models.items():
            val_pred = model.predict(X_val)
            val_r2 = r2_score(y_val, val_pred)
            val_rmse = np.sqrt(mean_squared_error(y_val, val_pred))
            print(f"     {name:15} - R²: {val_r2:.3f}, RMSE: {val_rmse:.2f}")
        
        return models
    
    def _create_ensemble_model(self, datasets, individual_models):
        """Create ensemble model with optimized weights"""
        
        X_train = datasets['X_train']
        y_train = datasets['y_train']
        X_val = datasets['X_val']
        y_val = datasets['y_val']
        
        # Select best performing models for ensemble
        model_performance = {}
        for name, model in individual_models.items():
            val_pred = model.predict(X_val)
            val_r2 = r2_score(y_val, val_pred)
            model_performance[name] = val_r2
        
        # Select top 5 models
        top_models = sorted(model_performance.items(), key=lambda x: x[1], reverse=True)[:5]
        selected_models = [(name, individual_models[name]) for name, _ in top_models]
        
        print(f"   🎯 Selected models for ensemble: {[name for name, _ in selected_models]}")
        
        # Create voting regressor ensemble
        ensemble_model = VotingRegressor(
            estimators=selected_models,
            n_jobs=-1
        )
        
        # Fit ensemble model
        ensemble_model.fit(X_train, y_train)
        
        # Evaluate ensemble
        val_pred = ensemble_model.predict(X_val)
        val_r2 = r2_score(y_val, val_pred)
        val_rmse = np.sqrt(mean_squared_error(y_val, val_pred))
        
        print(f"   🤝 Ensemble model - R²: {val_r2:.3f}, RMSE: {val_rmse:.2f}")
        
        return ensemble_model
    
    def _evaluate_models_comprehensive(self, datasets, individual_models, ensemble_model):
        """Comprehensive model evaluation"""
        
        X_train, y_train = datasets['X_train'], datasets['y_train']
        X_val, y_val = datasets['X_val'], datasets['y_val'] 
        X_test, y_test = datasets['X_test'], datasets['y_test']
        
        evaluation_results = {}
        
        # Evaluate all models (individual + ensemble)
        all_models = {**individual_models, 'ensemble': ensemble_model}
        
        for name, model in all_models.items():
            
            model_results = {}
            
            # Training set evaluation
            train_pred = model.predict(X_train)
            model_results['train'] = {
                'r2': r2_score(y_train, train_pred),
                'rmse': np.sqrt(mean_squared_error(y_train, train_pred)),
                'mae': mean_absolute_error(y_train, train_pred),
                'mape': np.mean(np.abs((y_train - train_pred) / y_train)) * 100
            }
            
            # Validation set evaluation
            val_pred = model.predict(X_val)
            model_results['validation'] = {
                'r2': r2_score(y_val, val_pred),
                'rmse': np.sqrt(mean_squared_error(y_val, val_pred)),
                'mae': mean_absolute_error(y_val, val_pred),
                'mape': np.mean(np.abs((y_val - val_pred) / y_val)) * 100
            }
            
            # Test set evaluation
            test_pred = model.predict(X_test)
            model_results['test'] = {
                'r2': r2_score(y_test, test_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, test_pred)),
                'mae': mean_absolute_error(y_test, test_pred),
                'mape': np.mean(np.abs((y_test - test_pred) / y_test)) * 100
            }
            
            # Cross-validation evaluation (on training + validation combined)
            X_train_val = pd.concat([X_train, X_val])
            y_train_val = pd.concat([y_train, y_val])
            
            cv_scores = cross_val_score(
                model, X_train_val, y_train_val, 
                cv=KFold(n_splits=5, shuffle=True, random_state=42),
                scoring='r2'
            )
            
            model_results['cross_validation'] = {
                'mean_r2': cv_scores.mean(),
                'std_r2': cv_scores.std(),
                'scores': cv_scores.tolist()
            }
            
            # Prediction distribution analysis
            model_results['prediction_analysis'] = {
                'train_pred_mean': train_pred.mean(),
                'train_pred_std': train_pred.std(),
                'val_pred_mean': val_pred.mean(),
                'val_pred_std': val_pred.std(),
                'test_pred_mean': test_pred.mean(),
                'test_pred_std': test_pred.std()
            }
            
            evaluation_results[name] = model_results
        
        return evaluation_results
    
    def _analyze_feature_importance(self, datasets, individual_models):
        """Analyze feature importance across models"""
        
        feature_names = datasets['feature_names']
        importance_analysis = {}
        
        # Models that support feature importance
        importance_models = ['random_forest', 'gradient_boosting', 'xgboost', 'lightgbm', 'extra_trees']
        
        all_importances = {}
        
        for model_name in importance_models:
            if model_name in individual_models:
                model = individual_models[model_name]
                
                if hasattr(model, 'feature_importances_'):
                    importances = model.feature_importances_
                elif hasattr(model, 'coef_'):
                    importances = np.abs(model.coef_)
                else:
                    continue
                
                # Store importances
                feature_importance = dict(zip(feature_names, importances))
                all_importances[model_name] = feature_importance
        
        # Calculate average importance across models
        if all_importances:
            avg_importance = {}
            for feature in feature_names:
                importances = [all_importances[model][feature] for model in all_importances.keys() if feature in all_importances[model]]
                if importances:
                    avg_importance[feature] = np.mean(importances)
                else:
                    avg_importance[feature] = 0
            
            # Sort by importance
            sorted_importance = sorted(avg_importance.items(), key=lambda x: x[1], reverse=True)
            
            importance_analysis = {
                'individual_models': all_importances,
                'average_importance': dict(sorted_importance),
                'top_10_features': sorted_importance[:10],
                'feature_rankings': {feature: rank + 1 for rank, (feature, _) in enumerate(sorted_importance)}
            }
        
        return importance_analysis
    
    def _analyze_model_interpretability(self, datasets, ensemble_model):
        """Analyze model interpretability and predictions"""
        
        X_test = datasets['X_test']
        y_test = datasets['y_test']
        
        test_predictions = ensemble_model.predict(X_test)
        
        interpretability_results = {
            'prediction_ranges': {
                'min_prediction': test_predictions.min(),
                'max_prediction': test_predictions.max(),
                'mean_prediction': test_predictions.mean(),
                'std_prediction': test_predictions.std()
            },
            'actual_vs_predicted': {
                'correlation': np.corrcoef(y_test, test_predictions)[0, 1],
                'residuals_mean': (y_test - test_predictions).mean(),
                'residuals_std': (y_test - test_predictions).std()
            },
            'performance_by_range': self._analyze_performance_by_skill_range(y_test, test_predictions),
            'error_analysis': self._analyze_prediction_errors(y_test, test_predictions)
        }
        
        return interpretability_results
    
    def _analyze_performance_by_skill_range(self, y_true, y_pred):
        """Analyze model performance by skill rating ranges"""
        
        # Define skill ranges
        ranges = [
            (25, 40, 'low_skill'),
            (40, 60, 'medium_skill'),
            (60, 80, 'high_skill'),
            (80, 100, 'elite_skill')
        ]
        
        range_performance = {}
        
        for min_val, max_val, range_name in ranges:
            mask = (y_true >= min_val) & (y_true < max_val)
            
            if mask.sum() > 0:
                range_true = y_true[mask]
                range_pred = y_pred[mask]
                
                range_performance[range_name] = {
                    'count': mask.sum(),
                    'r2': r2_score(range_true, range_pred),
                    'rmse': np.sqrt(mean_squared_error(range_true, range_pred)),
                    'mae': mean_absolute_error(range_true, range_pred)
                }
            else:
                range_performance[range_name] = {
                    'count': 0,
                    'r2': 0,
                    'rmse': 0,
                    'mae': 0
                }
        
        return range_performance
    
    def _analyze_prediction_errors(self, y_true, y_pred):
        """Analyze prediction errors in detail"""
        
        errors = y_true - y_pred
        
        error_analysis = {
            'error_distribution': {
                'mean': errors.mean(),
                'median': errors.median(),
                'std': errors.std(),
                'skewness': stats.skew(errors),
                'kurtosis': stats.kurtosis(errors)
            },
            'error_percentiles': {
                'p5': np.percentile(errors, 5),
                'p25': np.percentile(errors, 25),
                'p75': np.percentile(errors, 75),
                'p95': np.percentile(errors, 95)
            },
            'large_errors': {
                'count_above_10': (np.abs(errors) > 10).sum(),
                'count_above_15': (np.abs(errors) > 15).sum(),
                'max_error': np.abs(errors).max()
            }
        }
        
        return error_analysis
    
    def _save_trained_models(self, individual_models, ensemble_model, evaluation_results, importance_analysis):
        """Save trained models and metadata"""
        
        # Save individual models
        for name, model in individual_models.items():
            model_path = self.models_dir / f'{name}_model.pkl'
            joblib.dump(model, model_path)
        
        # Save ensemble model
        ensemble_path = self.models_dir / 'ensemble_model.pkl'
        joblib.dump(ensemble_model, ensemble_path)
        
        # Save evaluation results
        with open(self.models_dir / 'evaluation_results.json', 'w') as f:
            json.dump(evaluation_results, f, indent=2, default=str)
        
        # Save feature importance
        with open(self.models_dir / 'feature_importance.json', 'w') as f:
            json.dump(importance_analysis, f, indent=2, default=str)
        
        # Save model metadata
        model_metadata = {
            'training_timestamp': pd.Timestamp.now().isoformat(),
            'individual_models': list(individual_models.keys()),
            'ensemble_models': list(ensemble_model.named_estimators.keys()) if hasattr(ensemble_model, 'named_estimators') else [],
            'best_model': max(evaluation_results.keys(), key=lambda x: evaluation_results[x]['test']['r2']),
            'model_versions': {
                'individual_models_count': len(individual_models),
                'ensemble_components': len(ensemble_model.estimators) if hasattr(ensemble_model, 'estimators') else 0
            }
        }
        
        with open(self.models_dir / 'model_metadata.json', 'w') as f:
            json.dump(model_metadata, f, indent=2, default=str)
        
        print(f"   💾 Models saved to: {self.models_dir}")
    
    def _generate_training_report(self, evaluation_results, importance_analysis, interpretability_results, datasets):
        """Generate comprehensive training report"""
        
        report = {
            'training_summary': {
                'dataset_size': {
                    'train': len(datasets['X_train']),
                    'validation': len(datasets['X_val']),
                    'test': len(datasets['X_test']),
                    'total_features': len(datasets['feature_names'])
                },
                'target_statistics': {
                    'min': datasets['metadata']['target_range'][0],
                    'max': datasets['metadata']['target_range'][1],
                    'mean': datasets['metadata']['target_mean'],
                    'std': datasets['metadata']['target_std']
                }
            },
            
            'model_performance': {
                name: {
                    'test_r2': results['test']['r2'],
                    'test_rmse': results['test']['rmse'],
                    'test_mae': results['test']['mae'],
                    'cv_mean_r2': results['cross_validation']['mean_r2'],
                    'cv_std_r2': results['cross_validation']['std_r2']
                }
                for name, results in evaluation_results.items()
            },
            
            'best_models': {
                'highest_r2': max(evaluation_results.keys(), key=lambda x: evaluation_results[x]['test']['r2']),
                'lowest_rmse': min(evaluation_results.keys(), key=lambda x: evaluation_results[x]['test']['rmse']),
                'most_stable_cv': min(evaluation_results.keys(), key=lambda x: evaluation_results[x]['cross_validation']['std_r2'])
            },
            
            'feature_insights': {
                'top_5_features': importance_analysis.get('top_10_features', [])[:5] if importance_analysis else [],
                'total_features_analyzed': len(importance_analysis.get('average_importance', {})) if importance_analysis else 0
            },
            
            'model_interpretability': interpretability_results,
            
            'recommendations': self._generate_recommendations(evaluation_results, importance_analysis, datasets)
        }
        
        # Save report
        with open(self.models_dir / 'training_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report
    
    def _generate_recommendations(self, evaluation_results, importance_analysis, datasets):
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Model performance recommendations
        best_r2 = max(evaluation_results.values(), key=lambda x: x['test']['r2'])['test']['r2']
        
        if best_r2 >= 0.85:
            recommendations.append("Excellent model performance achieved! Models are ready for production use.")
        elif best_r2 >= 0.75:
            recommendations.append("Good model performance. Consider fine-tuning hyperparameters for production.")
        elif best_r2 >= 0.60:
            recommendations.append("Moderate performance. Consider collecting more data or advanced feature engineering.")
        else:
            recommendations.append("Low performance. Significant improvements needed before production deployment.")
        
        # Data size recommendations
        total_samples = datasets['metadata']['n_samples']
        
        if total_samples < 100:
            recommendations.append("Limited training data. Consider data augmentation or collecting more historical data.")
        elif total_samples < 300:
            recommendations.append("Moderate training data. Model may benefit from additional historical seasons.")
        else:
            recommendations.append("Sufficient training data for reliable model performance.")
        
        # Feature recommendations
        if importance_analysis and 'top_10_features' in importance_analysis:
            top_features = [feat[0] for feat in importance_analysis['top_10_features'][:3]]
            recommendations.append(f"Focus on key features: {', '.join(top_features)} for model interpretation.")
        
        # Ensemble recommendations
        ensemble_r2 = evaluation_results.get('ensemble', {}).get('test', {}).get('r2', 0)
        individual_best_r2 = max(
            [results['test']['r2'] for name, results in evaluation_results.items() if name != 'ensemble'],
            default=0
        )
        
        if ensemble_r2 > individual_best_r2:
            recommendations.append("Ensemble model outperforms individual models. Use ensemble for production.")
        else:
            recommendations.append("Individual models perform as well as ensemble. Consider simplicity vs. accuracy trade-off.")
        
        return recommendations
    
    def display_training_summary(self, training_results):
        """Display comprehensive training summary"""
        
        evaluation_results = training_results['evaluation']
        importance_analysis = training_results['importance']
        report = training_results['report']
        
        print("\n" + "="*80)
        print("🏆 ADVANCED F1 ML TRAINING COMPLETED!")
        print("="*80)
        
        # Model performance summary
        print("\n📊 Model Performance Summary:")
        print("-" * 50)
        
        performance_data = []
        for name, results in evaluation_results.items():
            performance_data.append({
                'Model': name.replace('_', ' ').title(),
                'Test R²': f"{results['test']['r2']:.3f}",
                'Test RMSE': f"{results['test']['rmse']:.2f}",
                'CV R² (μ±σ)': f"{results['cross_validation']['mean_r2']:.3f}±{results['cross_validation']['std_r2']:.3f}"
            })
        
        performance_df = pd.DataFrame(performance_data)
        print(performance_df.to_string(index=False))
        
        # Best models
        best_models = report['best_models']
        print(f"\n🥇 Best Models:")
        print(f"   Highest R²: {best_models['highest_r2'].replace('_', ' ').title()}")
        print(f"   Lowest RMSE: {best_models['lowest_rmse'].replace('_', ' ').title()}")
        print(f"   Most Stable: {best_models['most_stable_cv'].replace('_', ' ').title()}")
        
        # Top features
        if importance_analysis and 'top_10_features' in importance_analysis:
            print(f"\n🎯 Top 5 Most Important Features:")
            for i, (feature, importance) in enumerate(importance_analysis['top_10_features'][:5], 1):
                print(f"   {i}. {feature.replace('_', ' ').title()}: {importance:.3f}")
        
        # Dataset info
        dataset_info = report['training_summary']['dataset_size']
        print(f"\n📊 Dataset Summary:")
        print(f"   Training samples: {dataset_info['train']}")
        print(f"   Validation samples: {dataset_info['validation']}")
        print(f"   Test samples: {dataset_info['test']}")
        print(f"   Total features: {dataset_info['total_features']}")
        
        # Recommendations
        recommendations = report['recommendations']
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        print(f"\n💾 Models saved in: {self.models_dir}/")
        print("🚀 Ready for F1 historical driver simulation!")

def main():
    """Run the advanced ML training pipeline"""
    
    trainer = AdvancedF1MLTrainer()
    training_results = trainer.train_advanced_models()
    trainer.display_training_summary(training_results)
    
    return training_results

if __name__ == "__main__":
    main()
