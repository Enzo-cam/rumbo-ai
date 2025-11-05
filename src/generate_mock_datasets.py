"""
Mock Dataset Generator for Driver-Route Matching System
Generates synthetic but realistic data for drivers and routes in Argentina
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

# Set random seed for reproducibility
np.random.seed(42)

# Configuration
NUM_DRIVERS = 350
NUM_ROUTES = 150
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def generate_drivers_dataset(n_drivers=NUM_DRIVERS):
    """
    Generate synthetic driver dataset with realistic correlations
    """
    print(f"Generating {n_drivers} driver records...")
    
    # Base metrics with realistic distributions
    driver_ids = [f"DRV{str(i).zfill(5)}" for i in range(1, n_drivers + 1)]
    
    # Compliance metrics (0-100 scale)
    dispatch_compliance = np.random.beta(8, 2, n_drivers) * 100  # Most drivers are compliant
    route_deviations = np.random.gamma(2, 2, n_drivers)  # Right-skewed, most have few deviations
    unauthorized_stops = np.random.poisson(1.5, n_drivers)  # Count data
    unplanned_absences = np.random.poisson(2, n_drivers)  # Count data
    
    # Driving metrics
    driven_km = np.random.normal(15000, 5000, n_drivers)  # Annual km driven
    driven_km = np.clip(driven_km, 5000, 35000)  # Realistic bounds
    
    # ETA difference (minutes) - can be positive (late) or negative (early)
    eta_difference = np.random.normal(0, 15, n_drivers)
    
    # Environmental metrics
    carbon_footprint = np.random.normal(2500, 800, n_drivers)  # kg CO2/year
    carbon_footprint = np.clip(carbon_footprint, 1000, 5000)
    
    # Driving style (0-100, higher = more aggressive)
    driving_aggressiveness = np.random.beta(2, 5, n_drivers) * 100
    
    # Energy efficiency (0-100, higher = better)
    energy_efficiency = 100 - (driving_aggressiveness * 0.6 + np.random.normal(0, 10, n_drivers))
    energy_efficiency = np.clip(energy_efficiency, 30, 100)
    
    # Calculate composite scores
    # Safety score (0-100, higher = safer)
    safety_score = (
        0.4 * (100 - np.clip(route_deviations * 5, 0, 100)) +
        0.3 * (100 - np.clip(unauthorized_stops * 10, 0, 100)) +
        0.3 * (100 - driving_aggressiveness)
    )
    safety_score = np.clip(safety_score, 0, 100)
    
    # Efficiency score (0-100, higher = more efficient)
    efficiency_score = (
        0.4 * energy_efficiency +
        0.3 * (100 - np.abs(eta_difference) * 2) +
        0.3 * (100 - np.clip(carbon_footprint / 50, 0, 100))
    )
    efficiency_score = np.clip(efficiency_score, 0, 100)
    
    # Compliance score (0-100, higher = more compliant)
    compliance_score = (
        0.5 * dispatch_compliance +
        0.3 * (100 - np.clip(unplanned_absences * 10, 0, 100)) +
        0.2 * (100 - np.clip(route_deviations * 5, 0, 100))
    )
    compliance_score = np.clip(compliance_score, 0, 100)
    
    # Base driver score (weighted combination)
    driver_score_base = (
        0.4 * safety_score +
        0.35 * efficiency_score +
        0.25 * compliance_score
    )
    
    # Create DataFrame
    drivers_df = pd.DataFrame({
        'driver_id': driver_ids,
        'dispatch_compliance': dispatch_compliance.round(2),
        'route_deviations': route_deviations.round(2),
        'unauthorized_stops': unauthorized_stops,
        'driven_km': driven_km.round(0),
        'eta_difference': eta_difference.round(2),
        'unplanned_absences': unplanned_absences,
        'carbon_footprint': carbon_footprint.round(2),
        'driving_aggressiveness': driving_aggressiveness.round(2),
        'energy_efficiency': energy_efficiency.round(2),
        'safety_score': safety_score.round(2),
        'efficiency_score': efficiency_score.round(2),
        'compliance_score': compliance_score.round(2),
        'driver_score_base': driver_score_base.round(2)
    })
    
    return drivers_df


def generate_routes_dataset(n_routes=NUM_ROUTES):
    """
    Generate synthetic route dataset with realistic correlations
    Based on 7 key variables for route complexity assessment
    """
    print(f"Generating {n_routes} route records...")
    
    # Base identifiers
    route_ids = [f"RTE{str(i).zfill(4)}" for i in range(1, n_routes + 1)]
    
    # ========================================================================
    # 1. total_distance_km (Static, OSRM-based)
    # ========================================================================
    # Total route distance in kilometers
    # Formula: routes[0].distance / 1000 (OSRM returns meters)
    total_distance_km = np.random.gamma(5, 100, n_routes)  # Right-skewed distribution
    total_distance_km = np.clip(total_distance_km, 50, 2000)
    
    # ========================================================================
    # 2. avg_speed_kmh (Static, OSRM-based)
    # ========================================================================
    # Average speed acts as proxy for road type
    # High speed (90 km/h) = highway, low speed (40 km/h) = urban/mountain
    # Formula: (distance_km) / (duration_hours)
    # Generate realistic speeds based on route characteristics
    highway_ratio = np.random.beta(3, 3, n_routes)  # Bell-shaped around 0.5
    avg_speed_kmh = 40 + (highway_ratio * 60)  # Range: 40-100 km/h
    avg_speed_kmh = avg_speed_kmh + np.random.normal(0, 5, n_routes)  # Add noise
    avg_speed_kmh = np.clip(avg_speed_kmh, 30, 110)
    
    # ========================================================================
    # 3. navigation_steps_count (Static, OSRM-based)
    # ========================================================================
    # Number of navigation steps/turns - measures navigation complexity
    # Formula: len(routes[0].legs[0].steps)
    # More steps = more complex navigation
    # Correlate with distance and highway ratio (highways have fewer steps)
    base_steps = total_distance_km / 20  # Base: 1 step per 20km
    complexity_factor = (1 - highway_ratio) * 2  # Urban routes have more steps
    navigation_steps_count = (base_steps * complexity_factor * np.random.uniform(0.5, 1.5, n_routes)).astype(int)
    navigation_steps_count = np.clip(navigation_steps_count, 5, 200)
    
    # ========================================================================
    # 4. avg_compliance_index (Historical, Database)
    # ========================================================================
    # Measures route predictability: actual_time / planned_time
    # Value near 1.0 = perfect, 1.5 = takes 50% longer than planned
    # Formula: AVG(actual_time_minutes) / AVG(planned_time_minutes)
    # Routes with high complexity or traffic have higher values
    base_compliance = 1.0
    traffic_impact = (1 - highway_ratio) * 0.3  # Urban routes have more delays
    distance_impact = np.clip(total_distance_km / 1000, 0, 0.2)  # Longer routes accumulate delays
    avg_compliance_index = base_compliance + traffic_impact + distance_impact + np.random.normal(0, 0.1, n_routes)
    avg_compliance_index = np.clip(avg_compliance_index, 0.8, 2.0)
    
    # ========================================================================
    # 5. time_variability_min (Historical, Database)
    # ========================================================================
    # Standard deviation of actual travel times - measures consistency
    # Formula: STDDEV(actual_time_minutes)
    # Highway routes are consistent (low variability), urban routes vary more
    base_variability = 10  # Base 10 minutes
    route_length_factor = total_distance_km / 100  # Longer routes have more variability
    consistency_factor = (1 - highway_ratio) * 30  # Urban routes less consistent
    time_variability_min = base_variability + route_length_factor + consistency_factor + np.random.normal(0, 5, n_routes)
    time_variability_min = np.clip(time_variability_min, 5, 120)
    
    # ========================================================================
    # 6. normalized_breakdown_rate (Historical, Database)
    # ========================================================================
    # Measures physical risk: breakdowns per trip
    # Formula: SUM(had_breakdown) / COUNT(total_trips)
    # Poor road conditions or demanding terrain increase this rate
    base_rate = 0.02  # 2% base breakdown rate
    terrain_factor = (1 - highway_ratio) * 0.08  # Poor roads increase breakdowns
    distance_factor = np.clip(total_distance_km / 2000, 0, 0.05)  # Longer routes = more exposure
    normalized_breakdown_rate = base_rate + terrain_factor + distance_factor + np.random.normal(0, 0.01, n_routes)
    normalized_breakdown_rate = np.clip(normalized_breakdown_rate, 0.0, 0.3)
    
    # ========================================================================
    # 7. fuel_efficiency_lt_km (Historical, Database)
    # ========================================================================
    # Fuel consumption per km - proxy for engine effort
    # Formula: AVG(liters_consumed / km_traveled)
    # High values indicate: hills, poor roads, urban stop-and-go traffic
    base_consumption = 0.25  # Base 0.25 lt/km (25 lt per 100km)
    terrain_consumption = (1 - highway_ratio) * 0.15  # Urban/mountain uses more fuel
    # Add some routes with particularly challenging terrain
    challenging_routes = np.random.random(n_routes) < 0.2  # 20% are challenging
    fuel_efficiency_lt_km = base_consumption + terrain_consumption + (challenging_routes * 0.1) + np.random.normal(0, 0.03, n_routes)
    fuel_efficiency_lt_km = np.clip(fuel_efficiency_lt_km, 0.15, 0.6)
    
    # ========================================================================
    # Calculate highway_ratio (used internally for score calculations)
    # ========================================================================
    # This is kept as internal variable but not exported to final dataset
    
    # ========================================================================
    # Calculate composite scores (based only on 7 key variables)
    # ========================================================================
    # Peligrosity score (0-100, higher = more dangerous)
    # Based on: breakdown rate, time variability, distance, speed
    peligrosity_score = (
        0.35 * np.clip(normalized_breakdown_rate * 250, 0, 100) +
        0.30 * np.clip(time_variability_min / 1.2, 0, 100) +
        0.20 * np.clip(total_distance_km / 20, 0, 100) +
        0.15 * (100 - np.clip(avg_speed_kmh / 1.1, 0, 100))
    )
    peligrosity_score = np.clip(peligrosity_score, 0, 100)
    
    # Efficiency score (0-100, higher = more efficient)
    # Based on: speed, compliance, fuel efficiency
    efficiency_score = (
        0.35 * np.clip(avg_speed_kmh / 1.1, 0, 100) +
        0.35 * (100 - np.abs(avg_compliance_index - 1.0) * 100) +
        0.30 * np.clip((0.5 - fuel_efficiency_lt_km) * 200, 0, 100)
    )
    efficiency_score = np.clip(efficiency_score, 0, 100)
    
    # Operational complexity score (0-100, higher = more complex)
    # Based on: navigation steps, time variability, compliance variability
    operational_complexity_score = (
        0.40 * np.clip(navigation_steps_count / 2, 0, 100) +
        0.35 * np.clip(time_variability_min / 1.2, 0, 100) +
        0.25 * np.clip((avg_compliance_index - 1.0) * 100, 0, 100)
    )
    operational_complexity_score = np.clip(operational_complexity_score, 0, 100)
    
    # Create DataFrame with only key variables and scores
    routes_df = pd.DataFrame({
        'route_id': route_ids,
        # === 7 KEY VARIABLES ===
        'total_distance_km': total_distance_km.round(2),
        'avg_speed_kmh': avg_speed_kmh.round(2),
        'navigation_steps_count': navigation_steps_count,
        'avg_compliance_index': avg_compliance_index.round(3),
        'time_variability_min': time_variability_min.round(2),
        'normalized_breakdown_rate': normalized_breakdown_rate.round(4),
        'fuel_efficiency_lt_km': fuel_efficiency_lt_km.round(3),
        # === Composite scores ===
        'peligrosity_score': peligrosity_score.round(2),
        'efficiency_score': efficiency_score.round(2),
        'operational_complexity_score': operational_complexity_score.round(2)
    })
    
    return routes_df


def generate_metadata(drivers_df, routes_df):
    """
    Generate metadata describing the datasets
    """
    metadata = {
        "drivers": {
            "description": "Synthetic driver dataset with performance and behavior metrics",
            "n_records": len(drivers_df),
            "columns": {
                "driver_id": {"type": "string", "description": "Unique driver identifier"},
                "dispatch_compliance": {"type": "float", "range": [0, 100], "description": "Compliance with dispatch schedules (%)"},
                "route_deviations": {"type": "float", "range": [0, 20], "description": "Number of route deviations"},
                "unauthorized_stops": {"type": "int", "range": [0, 10], "description": "Count of unauthorized stops"},
                "driven_km": {"type": "float", "range": [5000, 35000], "description": "Total kilometers driven annually"},
                "eta_difference": {"type": "float", "range": [-60, 60], "description": "Average ETA difference in minutes (negative=early, positive=late)"},
                "unplanned_absences": {"type": "int", "range": [0, 15], "description": "Count of unplanned absences"},
                "carbon_footprint": {"type": "float", "range": [1000, 5000], "description": "Annual carbon footprint (kg CO2)"},
                "driving_aggressiveness": {"type": "float", "range": [0, 100], "description": "Driving aggressiveness score (higher=more aggressive)"},
                "energy_efficiency": {"type": "float", "range": [30, 100], "description": "Energy efficiency score (higher=better)"},
                "safety_score": {"type": "float", "range": [0, 100], "description": "Composite safety score"},
                "efficiency_score": {"type": "float", "range": [0, 100], "description": "Composite efficiency score"},
                "compliance_score": {"type": "float", "range": [0, 100], "description": "Composite compliance score"},
                "driver_score_base": {"type": "float", "range": [0, 100], "description": "Base driver score (weighted combination)"}
            }
        },
        "routes": {
            "description": "Synthetic route dataset with operational and risk metrics - Based on 7 key complexity variables",
            "n_records": len(routes_df),
            "columns": {
                "route_id": {"type": "string", "description": "Unique route identifier"},
                # === 7 KEY VARIABLES ===
                "total_distance_km": {
                    "type": "float", 
                    "range": [50, 2000], 
                    "description": "Total route distance in kilometers (OSRM-based: routes[0].distance / 1000)",
                    "source": "Static - OSRM API"
                },
                "avg_speed_kmh": {
                    "type": "float", 
                    "range": [30, 110], 
                    "description": "Average speed in km/h - proxy for road type (high=highway, low=urban/mountain)",
                    "source": "Static - OSRM API",
                    "formula": "(distance_km) / (duration_hours)"
                },
                "navigation_steps_count": {
                    "type": "int", 
                    "range": [5, 200], 
                    "description": "Number of navigation steps/turns - measures navigation complexity",
                    "source": "Static - OSRM API",
                    "formula": "len(routes[0].legs[0].steps)"
                },
                "avg_compliance_index": {
                    "type": "float", 
                    "range": [0.8, 2.0], 
                    "description": "Route predictability: actual_time / planned_time (1.0=perfect, 1.5=50% longer)",
                    "source": "Historical - Database",
                    "formula": "AVG(actual_time_minutes) / AVG(planned_time_minutes)"
                },
                "time_variability_min": {
                    "type": "float", 
                    "range": [5, 120], 
                    "description": "Standard deviation of travel times in minutes - measures consistency",
                    "source": "Historical - Database",
                    "formula": "STDDEV(actual_time_minutes)"
                },
                "normalized_breakdown_rate": {
                    "type": "float", 
                    "range": [0.0, 0.3], 
                    "description": "Breakdown rate per trip - measures physical risk and road conditions",
                    "source": "Historical - Database",
                    "formula": "SUM(had_breakdown) / COUNT(total_trips)"
                },
                "fuel_efficiency_lt_km": {
                    "type": "float", 
                    "range": [0.15, 0.6], 
                    "description": "Fuel consumption in liters per km - proxy for engine effort and terrain difficulty",
                    "source": "Historical - Database",
                    "formula": "AVG(liters_consumed / km_traveled)"
                },
                # === Composite scores (calculated from 7 key variables) ===
                "peligrosity_score": {"type": "float", "range": [0, 100], "description": "Danger/risk score (higher=more dangerous)"},
                "efficiency_score": {"type": "float", "range": [0, 100], "description": "Route efficiency score"},
                "operational_complexity_score": {"type": "float", "range": [0, 100], "description": "Operational complexity score"}
            }
        },
        "generation_date": "2025-10-29",
        "random_seed": 42
    }
    
    return metadata


def generate_report(drivers_df, routes_df):
    """
    Generate statistical report of the datasets
    """
    report = []
    report.append("=" * 80)
    report.append("DATASET GENERATION REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Drivers statistics
    report.append("DRIVERS DATASET STATISTICS")
    report.append("-" * 80)
    report.append(f"Total records: {len(drivers_df)}")
    report.append("")
    
    key_driver_cols = ['safety_score', 'efficiency_score', 'compliance_score', 
                       'driver_score_base', 'driven_km', 'eta_difference']
    
    for col in key_driver_cols:
        stats = drivers_df[col].describe()
        report.append(f"{col}:")
        report.append(f"  Mean: {stats['mean']:.2f}")
        report.append(f"  Std:  {stats['std']:.2f}")
        report.append(f"  Min:  {stats['min']:.2f}")
        report.append(f"  Max:  {stats['max']:.2f}")
        report.append("")
    
    # Routes statistics
    report.append("")
    report.append("ROUTES DATASET STATISTICS")
    report.append("-" * 80)
    report.append(f"Total records: {len(routes_df)}")
    report.append("")
    
    key_route_cols = ['total_distance_km', 'avg_speed_kmh', 'navigation_steps_count',
                      'avg_compliance_index', 'time_variability_min', 
                      'normalized_breakdown_rate', 'fuel_efficiency_lt_km',
                      'peligrosity_score', 'efficiency_score', 
                      'operational_complexity_score']
    
    for col in key_route_cols:
        stats = routes_df[col].describe()
        report.append(f"{col}:")
        report.append(f"  Mean: {stats['mean']:.2f}")
        report.append(f"  Std:  {stats['std']:.2f}")
        report.append(f"  Min:  {stats['min']:.2f}")
        report.append(f"  Max:  {stats['max']:.2f}")
        report.append("")
    
    report.append("=" * 80)
    report.append("Generation completed successfully!")
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    """
    Main execution function
    """
    print("Starting mock dataset generation...")
    print("=" * 80)
    
    # Generate datasets
    drivers_df = generate_drivers_dataset()
    routes_df = generate_routes_dataset()
    
    # Save datasets
    drivers_path = DATA_DIR / "drivers_mock.csv"
    routes_path = DATA_DIR / "routes_mock.csv"
    
    drivers_df.to_csv(drivers_path, index=False)
    routes_df.to_csv(routes_path, index=False)
    
    print(f"✓ Saved drivers dataset to: {drivers_path}")
    print(f"✓ Saved routes dataset to: {routes_path}")
    
    # Generate and save metadata
    metadata = generate_metadata(drivers_df, routes_df)
    metadata_path = DATA_DIR / "dataset_metadata.json"
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✓ Saved metadata to: {metadata_path}")
    
    # Generate and save report
    report = generate_report(drivers_df, routes_df)
    report_path = DATA_DIR / "generation_report.txt"
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"✓ Saved generation report to: {report_path}")
    
    print("")
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Drivers generated: {len(drivers_df)}")
    print(f"Routes generated: {len(routes_df)}")
    print("")
    print(report)


if __name__ == "__main__":
    main()
