"""
ALRIS - Module 4: Regional Demand Forecasting Engine
=====================================================
Builds explainable predictive models for enrolment demand.
Uses Linear Regression and ARIMA for time-series forecasting.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
import os
import json

warnings.filterwarnings('ignore')

# Government color palette
GOV_COLORS = {
    'primary': '#1a365d',
    'secondary': '#2c5282',
    'accent': '#ed8936',
    'success': '#38a169',
    'warning': '#dd6b20',
    'danger': '#e53e3e'
}


class ForecastingEngine:
    """
    Builds demand forecasts for UIDAI services.
    """
    
    def __init__(self, processed_data, features):
        """Initialize with processed data and features."""
        self.monthly_agg = processed_data['monthly_agg']
        self.state_monthly_agg = processed_data['state_monthly_agg']
        self.state_features = features['state_features']
        
        # Forecast results
        self.forecasts = {}
        self.model_metrics = {}
        
    def prepare_time_series(self):
        """Prepare time series data for forecasting."""
        print("\n[FC] Preparing TIME SERIES data...")
        
        # Create time index
        self.ts_data = self.monthly_agg.copy()
        self.ts_data['date'] = pd.to_datetime(self.ts_data['month'])
        self.ts_data = self.ts_data.sort_values('date')
        self.ts_data['time_idx'] = range(len(self.ts_data))
        
        # Calculate total activity
        self.ts_data['total_activity'] = (
            self.ts_data['total_enrolment'] + 
            self.ts_data['total_demo_updates'].fillna(0) + 
            self.ts_data['total_bio_updates'].fillna(0)
        )
        
        print(f"  [OK] Time series prepared: {len(self.ts_data)} months")
        print(f"  Date range: {self.ts_data['date'].min().strftime('%Y-%m')} to {self.ts_data['date'].max().strftime('%Y-%m')}")
        
        return self
    
    def build_linear_regression(self, target='total_enrolment'):
        """
        Build Linear Regression model for trend forecasting.
        
        This is an explainable model that captures linear trends.
        """
        print(f"\n[FC] Building LINEAR REGRESSION for {target}...")
        
        # Prepare features and target
        X = self.ts_data[['time_idx']].values
        y = self.ts_data[target].values
        
        # Split data (last 20% for validation)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Train model
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # Predict
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
        
        # Calculate metrics
        train_mae = mean_absolute_error(y_train, y_train_pred)
        test_mae = mean_absolute_error(y_test, y_test_pred)
        test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
        r2 = r2_score(y_test, y_test_pred)
        
        self.model_metrics['linear_regression'] = {
            'target': target,
            'train_mae': round(train_mae, 2),
            'test_mae': round(test_mae, 2),
            'test_rmse': round(test_rmse, 2),
            'r2_score': round(r2, 4),
            'coefficient': round(model.coef_[0], 4),
            'intercept': round(model.intercept_, 4)
        }
        
        # Store model
        self.lr_model = model
        self.lr_predictions = {
            'train': y_train_pred,
            'test': y_test_pred,
            'split_idx': split_idx
        }
        
        print(f"  Coefficient (trend): {model.coef_[0]:,.2f} per month")
        print(f"  Train MAE: {train_mae:,.2f}")
        print(f"  Test MAE: {test_mae:,.2f}")
        print(f"  R² Score: {r2:.4f}")
        
        return self
    
    def build_arima_forecast(self, target='total_enrolment', periods=3):
        """
        Build ARIMA model for time-series forecasting.
        Uses statsmodels ARIMA with simple parameters for explainability.
        """
        print(f"\n[FC] Building ARIMA FORECAST for {target}...")
        
        try:
            from statsmodels.tsa.arima.model import ARIMA
            
            # Prepare data
            y = self.ts_data[target].values
            
            # Simple ARIMA(1,1,1) - explainable configuration
            # p=1: One autoregressive term
            # d=1: First differencing for stationarity
            # q=1: One moving average term
            model = ARIMA(y, order=(1, 1, 1))
            fitted_model = model.fit()
            
            # Forecast next periods
            forecast = fitted_model.forecast(steps=periods)
            
            # Get confidence intervals
            forecast_df = fitted_model.get_forecast(steps=periods)
            conf_int = forecast_df.conf_int()
            
            # SUPER CORRECT: Model Confidence Calculation
            # Based on AIC and residual variance
            residual_var = np.var(fitted_model.resid)
            data_var = np.var(y)
            confidence_score = 100 * (1 - min(1, residual_var / data_var if data_var != 0 else 1))
            confidence_score = round(max(0, min(99.9, confidence_score)), 2)
            
            self.forecasts['arima'] = {
                'target': target,
                'periods_ahead': periods,
                'forecast_values': forecast.tolist(),
                'lower_bound': conf_int.iloc[:, 0].tolist(),
                'upper_bound': conf_int.iloc[:, 1].tolist(),
                'model_confidence': confidence_score,
                'aic': round(fitted_model.aic, 2),
                'bic': round(fitted_model.bic, 2)
            }
            
            # Also store fitted values for visualization
            self.arima_fitted = fitted_model.fittedvalues
            self.arima_forecast = forecast
            
            print(f"  [OK] ARIMA(1,1,1) model built (Confidence: {confidence_score}%)")
            print(f"  AIC: {fitted_model.aic:.2f}")

            print(f"  Forecast for next {periods} months:")
            for i, val in enumerate(forecast):
                print(f"    Month +{i+1}: {val:,.0f}")
            
        except ImportError:
            print("  [WARN] statsmodels not available, using simple moving average")
            self._simple_forecast(target, periods)
        
        return self
    
    def _simple_forecast(self, target, periods):
        """Fallback simple forecast using moving average."""
        y = self.ts_data[target].values
        
        # 3-month moving average
        ma = np.mean(y[-3:])
        # Linear trend
        trend = (y[-1] - y[-3]) / 2 if len(y) >= 3 else 0
        
        forecast = [ma + trend * (i+1) for i in range(periods)]
        
        self.forecasts['simple'] = {
            'target': target,
            'periods_ahead': periods,
            'forecast_values': forecast,
            'method': 'moving_average_with_trend'
        }
    
    def forecast_state_demand(self, top_n=10):
        """
        Forecast demand for top N states.
        """
        print(f"\n[FC] Forecasting STATE-LEVEL demand (top {top_n})...")
        
        top_states = self.state_features.nlargest(top_n, 'total_enrolment')['state'].tolist()
        
        state_forecasts = {}
        
        for state in top_states:
            state_data = self.state_monthly_agg[
                self.state_monthly_agg['state'] == state
            ].sort_values('month')
            
            if len(state_data) >= 3:
                # Simple linear trend
                y = state_data['total_enrolment'].values
                X = np.arange(len(y)).reshape(-1, 1)
                
                model = LinearRegression()
                model.fit(X, y)
                
                # Predict next 3 months
                future_X = np.array([[len(y)], [len(y)+1], [len(y)+2]])
                forecast = model.predict(future_X)
                
                state_forecasts[state] = {
                    'historical_avg': round(np.mean(y), 0),
                    'trend': round(model.coef_[0], 2),
                    'forecast_3month': [round(f, 0) for f in forecast],
                    'expected_growth': round(
                        (forecast[-1] - y[-1]) / y[-1] * 100, 2
                    ) if y[-1] > 0 else 0
                }
        
        self.forecasts['state_forecasts'] = state_forecasts
        
        print(f"  [OK] Forecasts generated for {len(state_forecasts)} states")
        
        return self
    
    def identify_stress_periods(self):
        """
        Identify infrastructure stress periods based on activity levels.
        """
        print("\n[FC] Identifying STRESS PERIODS...")
        
        # Calculate daily average activity
        self.ts_data['daily_avg'] = self.ts_data['total_activity'] / 30
        
        # Calculate thresholds
        mean_daily = self.ts_data['daily_avg'].mean()
        std_daily = self.ts_data['daily_avg'].std()
        
        high_threshold = mean_daily + std_daily
        critical_threshold = mean_daily + 2 * std_daily
        
        # Identify stress periods
        self.ts_data['stress_level'] = 'Normal'
        self.ts_data.loc[self.ts_data['daily_avg'] > high_threshold, 'stress_level'] = 'High'
        self.ts_data.loc[self.ts_data['daily_avg'] > critical_threshold, 'stress_level'] = 'Critical'
        
        stress_periods = self.ts_data[self.ts_data['stress_level'] != 'Normal'][
            ['month', 'total_activity', 'daily_avg', 'stress_level']
        ].to_dict('records')
        
        self.forecasts['stress_periods'] = {
            'high_threshold': round(high_threshold, 0),
            'critical_threshold': round(critical_threshold, 0),
            'periods': stress_periods
        }
        
        high_count = (self.ts_data['stress_level'] == 'High').sum()
        critical_count = (self.ts_data['stress_level'] == 'Critical').sum()
        
        print(f"  High stress periods: {high_count} months")
        print(f"  Critical stress periods: {critical_count} months")
        
        return self
    
    def generate_forecast_visualization(self, output_path):
        """
        Generate forecast visualization.
        """
        print("\n[FC] Generating FORECAST VISUALIZATION...")
        
        fig, axes = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot 1: Time series with linear trend
        ax1 = axes[0]
        dates = self.ts_data['date']
        actual = self.ts_data['total_enrolment']
        
        ax1.plot(dates, actual, color=GOV_COLORS['primary'], linewidth=2, 
                label='Actual Enrolments', marker='o', markersize=4)
        
        # Add linear regression line
        X = self.ts_data['time_idx'].values.reshape(-1, 1)
        trend_line = self.lr_model.predict(X)
        ax1.plot(dates, trend_line, color=GOV_COLORS['accent'], linewidth=2, 
                linestyle='--', label='Linear Trend')
        
        ax1.set_title('Monthly Enrolment Trend Analysis', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Date', fontsize=12)
        ax1.set_ylabel('Enrolment Count', fontsize=12)
        ax1.legend(loc='upper left')
        ax1.tick_params(axis='x', rotation=45)
        
        # Plot 2: Activity with stress levels
        ax2 = axes[1]
        colors = {
            'Normal': GOV_COLORS['success'],
            'High': GOV_COLORS['warning'],
            'Critical': GOV_COLORS['danger']
        }
        bar_colors = [colors[level] for level in self.ts_data['stress_level']]
        
        ax2.bar(dates, self.ts_data['total_activity'], color=bar_colors, alpha=0.7)
        ax2.axhline(y=self.forecasts['stress_periods']['high_threshold'] * 30, 
                   color=GOV_COLORS['warning'], linestyle='--', label='High Threshold')
        ax2.axhline(y=self.forecasts['stress_periods']['critical_threshold'] * 30, 
                   color=GOV_COLORS['danger'], linestyle='--', label='Critical Threshold')
        
        ax2.set_title('Infrastructure Stress Analysis', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel('Total Activity', fontsize=12)
        ax2.legend(loc='upper left')
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        chart_path = os.path.join(output_path, 'output', 'charts')
        os.makedirs(chart_path, exist_ok=True)
        plt.savefig(os.path.join(chart_path, 'forecast_analysis.png'), dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  [OK] Saved to {chart_path}/forecast_analysis.png")
        return self
    
    def get_forecasts(self):
        """Return all forecasts and metrics."""
        return {
            'forecasts': self.forecasts,
            'model_metrics': self.model_metrics
        }
    
    def save_forecasts(self, output_path):
        """Save forecasts to JSON."""
        print("\n[SAVE] Saving forecasts...")
        
        from utils import save_json, convert_to_native_types
        
        json_path = os.path.join(output_path, 'frontend', 'data')
        os.makedirs(json_path, exist_ok=True)
        
        forecasts_clean = convert_to_native_types(self.forecasts)
        metrics_clean = convert_to_native_types(self.model_metrics)
        
        save_json(forecasts_clean, os.path.join(json_path, 'forecasts.json'))
        save_json(metrics_clean, os.path.join(json_path, 'model_metrics.json'))
        
        print(f"  [OK] Saved to {json_path}")
        return self


def run_forecasting(processed_data, features, output_path):
    """Run the complete forecasting pipeline."""
    print("\n" + "="*60)
    print("REGIONAL DEMAND FORECASTING ENGINE")
    print("="*60)
    
    engine = ForecastingEngine(processed_data, features)
    
    engine.prepare_time_series()
    engine.build_linear_regression()
    engine.build_arima_forecast()
    engine.forecast_state_demand()
    engine.identify_stress_periods()
    engine.generate_forecast_visualization(output_path)
    engine.save_forecasts(output_path)
    
    print("\n" + "="*60)
    print("[OK] FORECASTING COMPLETE")
    print("="*60)
    
    return engine
