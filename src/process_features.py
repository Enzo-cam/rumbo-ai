"""
Process Driver Features from Scania Raw Data

This script processes raw Scania Driver Evaluation data and calculates
aggregated features for each driver, including composite scores for:
- Safety
- Efficiency
- Compliance

Input: data/raw_driver_trips.json (from extract_scania_data.py)
Output: data/drivers_features.csv

Usage:
    python process_features.py --input data/raw_driver_trips.json
"""

import json
import logging
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("ERROR: pandas and numpy required. Run: pip install pandas numpy")
    sys.exit(1)

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
CO2_PER_LITER_DIESEL = 2.68  # kg CO2 per liter of diesel (EPA)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_raw_data(file_path: Path) -> Dict:
    """
    Load raw Scania API data from JSON file.

    Args:
        file_path: Path to raw JSON file

    Returns:
        Dict: Raw API response data
    """
    logger.info(f"Loading raw data from: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info("✓ Raw data loaded successfully")
        return data

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        logger.error("Run extract_scania_data.py first to fetch data from API")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        raise


def extract_trip_features(trip: Dict, vehicle_id: str) -> Optional[Dict]:
    """
    Extract features from a single trip.

    Args:
        trip: Trip data from Scania API
        vehicle_id: VIN of the vehicle

    Returns:
        Dict: Extracted features for the trip, or None if invalid
    """
    # Get driver identification
    driver_id = trip.get('DriverRef') or trip.get('DriverIdentification')
    driver_name = trip.get('DriverName', 'Unknown')

    if not driver_id:
        return None

    # Parse dates
    start_date = trip.get('StartDate')
    stop_date = trip.get('StopDate')

    # Extract safety features
    harsh_braking_count = float(trip.get('HarshBrakeApplications', 0))
    harsh_braking_per_100km = float(trip.get('HarshBrakeApplicationsTLValue', 0))
    harsh_acceleration_per_100km = float(trip.get('HarshAccelerationsValue', 0))
    speeding_percentage = float(trip.get('SpeedingValue', 0))
    brake_score = float(trip.get('UseOfBrakesScaniaDriverSupport', 0))

    # Extract efficiency features
    fuel_per_100km = float(trip.get('AverageFuelConsumption', 0))
    idle_time_percentage = float(trip.get('IdlingValue', 0))
    coasting_percentage = float(trip.get('CoastingValue', 0))
    anticipation_score = float(trip.get('AnticipationScaniaDriverSupport', 0))

    # Extract compliance features
    distance_km = float(trip.get('Distance', 0))
    average_speed_kmh = float(trip.get('AverageSpeed', 0))

    # Extract composite score from Scania
    scania_driver_support_score = float(trip.get('ScaniaDriverSupportValue', 0))
    hill_driving_score = float(trip.get('HillDrivingScaniaDriverSupport', 0))

    # Extract cruise control usage
    distance_with_cruise = float(trip.get('DistanceWithCruiseControl', 0))
    cruise_control_usage_pct = (distance_with_cruise / distance_km * 100) if distance_km > 0 else 0

    # Extract fuel consumption
    total_fuel_liters = float(trip.get('TotalFuelConsumption', 0))
    fuel_idling_liters = float(trip.get('TotalFuelConsumptionIdling', 0))

    # Calculate CO2 emissions
    co2_emissions_kg = total_fuel_liters * CO2_PER_LITER_DIESEL
    co2_per_km = (co2_emissions_kg / distance_km) if distance_km > 0 else 0
    co2_from_idling_kg = fuel_idling_liters * CO2_PER_LITER_DIESEL

    # Calculate carbon efficiency score (inverted: lower CO2 = higher score)
    # Normalize co2_per_km to 0-100 scale (assuming 0.35 kg/km is average)
    carbon_efficiency_score = max(0, 100 - (co2_per_km * 350))

    features = {
        'trip_id': f"{driver_id}_{start_date}",
        'driver_id': driver_id,
        'driver_name': driver_name,
        'vin': vehicle_id,
        'start_date': start_date,
        'stop_date': stop_date,

        # Distance and time
        'distance_km': distance_km,
        'average_speed_kmh': average_speed_kmh,

        # Safety features
        'harsh_braking_count': harsh_braking_count,
        'harsh_braking_per_100km': harsh_braking_per_100km,
        'harsh_acceleration_per_100km': harsh_acceleration_per_100km,
        'speeding_percentage': speeding_percentage,
        'brake_score': brake_score,

        # Efficiency features
        'fuel_per_100km': fuel_per_100km,
        'total_fuel_liters': total_fuel_liters,
        'idle_time_percentage': idle_time_percentage,
        'fuel_idling_liters': fuel_idling_liters,
        'coasting_percentage': coasting_percentage,
        'cruise_control_usage_pct': cruise_control_usage_pct,
        'anticipation_score': anticipation_score,

        # Composite scores
        'scania_driver_support_score': scania_driver_support_score,
        'hill_driving_score': hill_driving_score,

        # CO2 metrics
        'co2_emissions_kg': co2_emissions_kg,
        'co2_per_km': co2_per_km,
        'co2_from_idling_kg': co2_from_idling_kg,
        'carbon_efficiency_score': carbon_efficiency_score
    }

    return features


def process_all_trips(raw_data: Dict) -> pd.DataFrame:
    """
    Process all trips from raw Scania data.

    Args:
        raw_data: Raw API response data

    Returns:
        DataFrame: All trips with extracted features
    """
    logger.info("Processing trips...")

    vehicles = raw_data.get('EvaluationVehicles', [])
    all_trips = []

    for vehicle in vehicles:
        vehicle_id = vehicle.get('VIN', 'Unknown')
        trips = vehicle.get('Trips', [])

        for trip in trips:
            features = extract_trip_features(trip, vehicle_id)
            if features:
                all_trips.append(features)

    df = pd.DataFrame(all_trips)

    logger.info(f"✓ Processed {len(df)} trips")
    logger.info(f"  Unique drivers: {df['driver_id'].nunique()}")
    logger.info(f"  Unique vehicles: {df['vin'].nunique()}")

    return df


def calculate_safety_score(driver_data: pd.Series) -> float:
    """
    Calculate composite safety score for a driver.

    Components:
    - Low harsh braking (40%)
    - Low speeding (30%)
    - High brake score (20%)
    - Low harsh acceleration (10%)

    Returns:
        float: Safety score (0-100)
    """
    # Normalize harsh braking (inverse: lower is better)
    # Assume 0.0 = perfect, 1.0 = very bad
    harsh_braking_norm = max(0, 100 - (driver_data['harsh_braking_per_100km_avg'] * 100))

    # Normalize speeding (inverse: lower is better)
    speeding_norm = max(0, 100 - driver_data['speeding_percentage_avg'])

    # Brake score is already 0-100 (higher is better)
    brake_score_norm = driver_data['brake_score_avg']

    # Normalize harsh acceleration (inverse: lower is better)
    harsh_accel_norm = max(0, 100 - (driver_data['harsh_acceleration_per_100km_avg'] * 100))

    # Weighted composite
    safety_score = (
        0.40 * harsh_braking_norm +
        0.30 * speeding_norm +
        0.20 * brake_score_norm +
        0.10 * harsh_accel_norm
    )

    return round(safety_score, 2)


def calculate_efficiency_score(driver_data: pd.Series) -> float:
    """
    Calculate composite efficiency score for a driver.

    Components:
    - Low fuel consumption (35%)
    - Low idle time (25%)
    - High cruise control usage (20%)
    - High anticipation score (20%)

    Returns:
        float: Efficiency score (0-100)
    """
    # Normalize fuel consumption (inverse: lower is better)
    # Assume 25 L/100km is good, 35 L/100km is bad
    fuel_norm = max(0, 100 - ((driver_data['fuel_per_100km_avg'] - 20) * 5))

    # Normalize idle time (inverse: lower is better)
    idle_norm = max(0, 100 - (driver_data['idle_time_percentage_avg'] * 5))

    # Cruise control usage percentage (higher is better)
    cruise_norm = driver_data['cruise_control_usage_pct_avg']

    # Anticipation score is already 0-100 (higher is better)
    anticipation_norm = driver_data['anticipation_score_avg']

    # Weighted composite
    efficiency_score = (
        0.35 * fuel_norm +
        0.25 * idle_norm +
        0.20 * cruise_norm +
        0.20 * anticipation_norm
    )

    return round(efficiency_score, 2)


def calculate_compliance_score(driver_data: pd.Series) -> float:
    """
    Calculate composite compliance score for a driver.

    Components:
    - Total distance driven (experience) (40%)
    - Number of trips (consistency) (30%)
    - Average speed within limits (30%)

    Returns:
        float: Compliance score (0-100)
    """
    # Normalize total distance (experience indicator)
    # Assume 10,000 km is minimum, 30,000 km is excellent
    distance_norm = min(100, (driver_data['total_distance_km'] / 300))

    # Normalize trip count (consistency indicator)
    # Assume 10 trips is minimum, 50 trips is excellent
    trips_norm = min(100, (driver_data['total_trips'] / 0.5))

    # Normalize average speed (should be reasonable, not too low or high)
    # Assume 60-80 km/h is optimal
    avg_speed = driver_data['avg_speed_kmh']
    if 60 <= avg_speed <= 80:
        speed_norm = 100
    elif avg_speed < 60:
        speed_norm = max(0, 50 + (avg_speed - 40))
    else:  # > 80
        speed_norm = max(0, 100 - ((avg_speed - 80) * 2))

    # Weighted composite
    compliance_score = (
        0.40 * distance_norm +
        0.30 * trips_norm +
        0.30 * speed_norm
    )

    return round(compliance_score, 2)


def aggregate_driver_features(trips_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate trip-level features to driver-level.

    Args:
        trips_df: DataFrame with trip-level features

    Returns:
        DataFrame: Driver-level aggregated features
    """
    logger.info("Aggregating features by driver...")

    # Group by driver
    driver_groups = trips_df.groupby('driver_id')

    # Aggregate metrics
    driver_features = pd.DataFrame({
        'driver_id': trips_df.groupby('driver_id')['driver_id'].first(),
        'driver_name': trips_df.groupby('driver_id')['driver_name'].first(),

        # Trip counts and totals
        'total_trips': driver_groups.size(),
        'total_distance_km': driver_groups['distance_km'].sum(),
        'avg_speed_kmh': driver_groups['average_speed_kmh'].mean(),

        # Safety features (averages)
        'harsh_braking_count_total': driver_groups['harsh_braking_count'].sum(),
        'harsh_braking_per_100km_avg': driver_groups['harsh_braking_per_100km'].mean(),
        'harsh_acceleration_per_100km_avg': driver_groups['harsh_acceleration_per_100km'].mean(),
        'speeding_percentage_avg': driver_groups['speeding_percentage'].mean(),
        'brake_score_avg': driver_groups['brake_score'].mean(),

        # Efficiency features (averages)
        'fuel_per_100km_avg': driver_groups['fuel_per_100km'].mean(),
        'total_fuel_liters': driver_groups['total_fuel_liters'].sum(),
        'idle_time_percentage_avg': driver_groups['idle_time_percentage'].mean(),
        'coasting_percentage_avg': driver_groups['coasting_percentage'].mean(),
        'cruise_control_usage_pct_avg': driver_groups['cruise_control_usage_pct'].mean(),
        'anticipation_score_avg': driver_groups['anticipation_score'].mean(),

        # Composite scores
        'scania_driver_support_score_avg': driver_groups['scania_driver_support_score'].mean(),
        'hill_driving_score_avg': driver_groups['hill_driving_score'].mean(),

        # CO2 metrics
        'total_co2_emissions_kg': driver_groups['co2_emissions_kg'].sum(),
        'avg_co2_per_km': driver_groups['co2_per_km'].mean(),
        'total_co2_from_idling_kg': driver_groups['co2_from_idling_kg'].sum(),
        'carbon_efficiency_score_avg': driver_groups['carbon_efficiency_score'].mean()
    }).reset_index(drop=True)

    # Calculate composite scores
    logger.info("Calculating composite scores...")

    driver_features['safety_score'] = driver_features.apply(calculate_safety_score, axis=1)
    driver_features['efficiency_score'] = driver_features.apply(calculate_efficiency_score, axis=1)
    driver_features['compliance_score'] = driver_features.apply(calculate_compliance_score, axis=1)

    # Calculate overall driver score (weighted combination)
    driver_features['driver_score_base'] = (
        0.40 * driver_features['safety_score'] +
        0.35 * driver_features['efficiency_score'] +
        0.25 * driver_features['compliance_score']
    ).round(2)

    logger.info(f"✓ Aggregated features for {len(driver_features)} drivers")

    return driver_features


def generate_processing_report(trips_df: pd.DataFrame, drivers_df: pd.DataFrame) -> str:
    """
    Generate a detailed processing report.

    Args:
        trips_df: Trip-level data
        drivers_df: Driver-level data

    Returns:
        str: Formatted report
    """
    report = []
    report.append("=" * 80)
    report.append("FEATURE PROCESSING REPORT")
    report.append("=" * 80)
    report.append("")

    # Trip statistics
    report.append("TRIP STATISTICS")
    report.append("-" * 80)
    report.append(f"Total trips: {len(trips_df)}")
    report.append(f"Date range: {trips_df['start_date'].min()} to {trips_df['stop_date'].max()}")
    report.append(f"Total distance: {trips_df['distance_km'].sum():.0f} km")
    report.append(f"Total fuel consumed: {trips_df['total_fuel_liters'].sum():.0f} liters")
    report.append(f"Total CO2 emissions: {trips_df['co2_emissions_kg'].sum():.0f} kg")
    report.append("")

    # Driver statistics
    report.append("DRIVER STATISTICS")
    report.append("-" * 80)
    report.append(f"Total drivers: {len(drivers_df)}")
    report.append(f"Average safety score: {drivers_df['safety_score'].mean():.2f}")
    report.append(f"Average efficiency score: {drivers_df['efficiency_score'].mean():.2f}")
    report.append(f"Average compliance score: {drivers_df['compliance_score'].mean():.2f}")
    report.append(f"Average overall score: {drivers_df['driver_score_base'].mean():.2f}")
    report.append("")

    # Top performers
    report.append("TOP 5 DRIVERS (by overall score)")
    report.append("-" * 80)
    top_drivers = drivers_df.nlargest(5, 'driver_score_base')[
        ['driver_name', 'driver_score_base', 'safety_score', 'efficiency_score']
    ]
    for idx, driver in top_drivers.iterrows():
        report.append(f"  {driver['driver_name']}: {driver['driver_score_base']:.2f} "
                      f"(Safety: {driver['safety_score']:.2f}, Efficiency: {driver['efficiency_score']:.2f})")
    report.append("")

    report.append("=" * 80)
    report.append("Processing completed successfully!")
    report.append("=" * 80)

    return "\n".join(report)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Process driver features from Scania raw data'
    )
    parser.add_argument(
        '--input',
        type=str,
        help='Input raw JSON file path',
        default=str(DATA_DIR / 'raw_driver_trips.json')
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output CSV file path',
        default=str(DATA_DIR / 'drivers_features.csv')
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("DRIVER FEATURE PROCESSING")
    logger.info("=" * 80)
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")
    logger.info("")

    try:
        # Load raw data
        raw_data = load_raw_data(Path(args.input))

        # Process trips
        trips_df = process_all_trips(raw_data)

        # Save trip-level data
        trips_output = Path(args.output).parent / 'trips_processed.csv'
        trips_df.to_csv(trips_output, index=False)
        logger.info(f"✓ Saved trip-level data to: {trips_output}")

        # Aggregate to driver-level
        drivers_df = aggregate_driver_features(trips_df)

        # Save driver-level data
        drivers_df.to_csv(args.output, index=False)
        logger.info(f"✓ Saved driver features to: {args.output}")

        # Generate and save report
        report = generate_processing_report(trips_df, drivers_df)
        report_path = Path(args.output).parent / 'processing_report.txt'

        with open(report_path, 'w') as f:
            f.write(report)

        logger.info(f"✓ Saved processing report to: {report_path}")
        logger.info("")
        print(report)

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"PROCESSING FAILED: {e}")
        logger.error("=" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
