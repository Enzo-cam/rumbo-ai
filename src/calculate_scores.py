"""
Score Calculator for Driver-Route Matching System
Calculates final adjusted scores for drivers and routes
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
ALPHA = 0.15  # Weight for kilometer balancing adjustment


def calculate_driver_scores(drivers_df):
    """
    Calculate final adjusted driver scores with kilometer leveling
    
    Formula:
    - driver_score_final = 0.4 * safety + 0.35 * efficiency + 0.25 * compliance
    - km_balance = mean_driven_km - driven_km
    - driver_score_adjusted = driver_score_final + alpha * km_balance_scaled
    """
    print("Calculating driver scores...")
    
    # Calculate final score (already done in base, but recalculating for clarity)
    driver_score_final = (
        0.4 * drivers_df['safety_score'] +
        0.35 * drivers_df['efficiency_score'] +
        0.25 * drivers_df['compliance_score']
    )
    
    # Calculate kilometer balance
    mean_driven_km = drivers_df['driven_km'].mean()
    km_balance = mean_driven_km - drivers_df['driven_km']
    
    # Scale km_balance to [-10, 10] range for adjustment
    km_balance_scaled = (km_balance / drivers_df['driven_km'].std()) * 5
    km_balance_scaled = np.clip(km_balance_scaled, -10, 10)
    
    # Calculate adjusted score
    driver_score_adjusted = driver_score_final + (ALPHA * km_balance_scaled)
    driver_score_adjusted = np.clip(driver_score_adjusted, 0, 100)
    
    # Add new columns
    drivers_scored = drivers_df.copy()
    drivers_scored['driver_score_final'] = driver_score_final.round(2)
    drivers_scored['km_balance'] = km_balance.round(2)
    drivers_scored['km_balance_scaled'] = km_balance_scaled.round(2)
    drivers_scored['driver_score_adjusted'] = driver_score_adjusted.round(2)
    
    print(f"  Mean driver score (final): {driver_score_final.mean():.2f}")
    print(f"  Mean driver score (adjusted): {driver_score_adjusted.mean():.2f}")
    print(f"  Mean km balance: {km_balance.mean():.2f}")
    
    return drivers_scored


def calculate_route_scores(routes_df):
    """
    Calculate final route scores
    
    Formula:
    - route_score_final = 0.4 * efficiency + 0.3 * complexity + 0.3 * peligrosity
    
    Note: Higher score means more demanding route (requires better drivers)
    """
    print("Calculating route scores...")
    
    # Calculate final route score
    # We weight efficiency positively, but complexity and danger also increase requirements
    route_score_final = (
        0.4 * routes_df['efficiency_score'] +
        0.3 * routes_df['operational_complexity_score'] +
        0.3 * routes_df['peligrosity_score']
    )
    
    route_score_final = np.clip(route_score_final, 0, 100)
    
    # Add new column
    routes_scored = routes_df.copy()
    routes_scored['route_score_final'] = route_score_final.round(2)
    
    # Calculate route difficulty tier
    routes_scored['difficulty_tier'] = pd.cut(
        route_score_final,
        bins=[0, 40, 60, 80, 100],
        labels=['Easy', 'Medium', 'Hard', 'Expert']
    )
    
    print(f"  Mean route score: {route_score_final.mean():.2f}")
    print(f"  Route difficulty distribution:")
    print(routes_scored['difficulty_tier'].value_counts().to_string())
    
    return routes_scored


def generate_score_report(drivers_scored, routes_scored):
    """
    Generate a detailed scoring report
    """
    report = []
    report.append("=" * 80)
    report.append("SCORING REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Driver scoring summary
    report.append("DRIVER SCORING SUMMARY")
    report.append("-" * 80)
    report.append(f"Total drivers: {len(drivers_scored)}")
    report.append("")
    
    report.append("Score Distribution:")
    report.append(f"  Base Score:     Mean={drivers_scored['driver_score_base'].mean():.2f}, "
                  f"Std={drivers_scored['driver_score_base'].std():.2f}")
    report.append(f"  Final Score:    Mean={drivers_scored['driver_score_final'].mean():.2f}, "
                  f"Std={drivers_scored['driver_score_final'].std():.2f}")
    report.append(f"  Adjusted Score: Mean={drivers_scored['driver_score_adjusted'].mean():.2f}, "
                  f"Std={drivers_scored['driver_score_adjusted'].std():.2f}")
    report.append("")
    
    report.append("Kilometer Balancing:")
    report.append(f"  Mean km driven: {drivers_scored['driven_km'].mean():.2f}")
    report.append(f"  Mean km balance: {drivers_scored['km_balance'].mean():.2f}")
    report.append(f"  Adjustment impact: ±{(drivers_scored['driver_score_adjusted'] - drivers_scored['driver_score_final']).abs().mean():.2f} points")
    report.append("")
    
    # Top and bottom drivers
    top_drivers = drivers_scored.nlargest(5, 'driver_score_adjusted')[['driver_id', 'driver_score_adjusted', 'safety_score', 'efficiency_score']]
    report.append("Top 5 Drivers:")
    for _, driver in top_drivers.iterrows():
        report.append(f"  {driver['driver_id']}: Score={driver['driver_score_adjusted']:.2f} "
                     f"(Safety={driver['safety_score']:.2f}, Efficiency={driver['efficiency_score']:.2f})")
    report.append("")
    
    # Route scoring summary
    report.append("")
    report.append("ROUTE SCORING SUMMARY")
    report.append("-" * 80)
    report.append(f"Total routes: {len(routes_scored)}")
    report.append("")
    
    report.append("Score Distribution:")
    report.append(f"  Route Score: Mean={routes_scored['route_score_final'].mean():.2f}, "
                  f"Std={routes_scored['route_score_final'].std():.2f}")
    report.append("")
    
    report.append("Difficulty Distribution:")
    for tier in ['Easy', 'Medium', 'Hard', 'Expert']:
        count = (routes_scored['difficulty_tier'] == tier).sum()
        pct = count / len(routes_scored) * 100
        report.append(f"  {tier}: {count} routes ({pct:.1f}%)")
    report.append("")
    
    # Top demanding routes
    top_routes = routes_scored.nlargest(5, 'route_score_final')[['route_id', 'route_score_final', 'difficulty_tier', 'total_distance_km']]
    report.append("Top 5 Most Demanding Routes:")
    for _, route in top_routes.iterrows():
        report.append(f"  {route['route_id']}: Score={route['route_score_final']:.2f} "
                     f"({route['difficulty_tier']}, {route['total_distance_km']:.0f} km)")
    report.append("")
    
    report.append("=" * 80)
    report.append("Scoring completed successfully!")
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    """
    Main execution function
    """
    print("Starting score calculation...")
    print("=" * 80)
    
    # Load datasets
    drivers_df = pd.read_csv(DATA_DIR / "drivers_mock.csv")
    routes_df = pd.read_csv(DATA_DIR / "routes_mock.csv")
    
    print(f"Loaded {len(drivers_df)} drivers and {len(routes_df)} routes")
    print("")
    
    # Calculate scores
    drivers_scored = calculate_driver_scores(drivers_df)
    routes_scored = calculate_route_scores(routes_df)
    
    # Save scored datasets
    drivers_output = DATA_DIR / "scored_drivers.csv"
    routes_output = DATA_DIR / "scored_routes.csv"
    
    drivers_scored.to_csv(drivers_output, index=False)
    routes_scored.to_csv(routes_output, index=False)
    
    print("")
    print(f"✓ Saved scored drivers to: {drivers_output}")
    print(f"✓ Saved scored routes to: {routes_output}")
    
    # Generate and save report
    report = generate_score_report(drivers_scored, routes_scored)
    report_path = DATA_DIR / "scoring_report.txt"
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"✓ Saved scoring report to: {report_path}")
    
    print("")
    print(report)


if __name__ == "__main__":
    main()
