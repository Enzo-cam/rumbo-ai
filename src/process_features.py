"""
Process Driver Features from Scania Real Data

This script processes the REAL Scania API structure where data is already
aggregated by driver (no individual trips).

Input: data/raw_driver_trips.json
  Structure: {"Drivers": [{"DriverRef": "...", "Distance": 8442, ...}]}

Output: data/drivers_features.csv
  One row per driver with calculated features and scores

Usage:
    python src/process_features.py --input data/raw_driver_trips.json
"""

import json
import logging
import argparse
import sys
from pathlib import Path

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


def load_scania_data(file_path: Path) -> dict:
    """
    Load raw Scania API data from JSON file.

    Args:
        file_path: Path to raw JSON file

    Returns:
        dict: Raw API response data
    """
    logger.info(f"Loading Scania data from: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        drivers = data.get('Drivers', [])
        logger.info(f"OK - Loaded data with {len(drivers)} drivers")
        return data

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        logger.error("Run extract_scania_data.py first to fetch data from API")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        raise


def extract_driver_features(driver: dict) -> dict:
    """
    Extract features from a single driver (data already aggregated by Scania).

    Args:
        driver: Driver data from Scania API

    Returns:
        dict: Extracted features for the driver
    """
    # Basic info
    driver_id = driver.get('DriverRef') or driver.get('DriverIdentification', 'unknown')
    driver_name = driver.get('DriverName', 'Unknown')

    # Safety features
    harsh_braking_per_100km = float(driver.get('HarshBrakeApplicationsTLValue') or 0)
    harsh_accel_per_100km = float(driver.get('HarshAccelerationsValue') or 0)
    speeding_percentage = float(driver.get('SpeedingValue') or 0)
    brake_score = float(driver.get('UseOfBrakesScaniaDriverSupport') or 0)
    harsh_braking_count = int(driver.get('HarshBrakeApplications') or 0)

    # Efficiency features
    fuel_per_100km = float(driver.get('AverageFuelConsumption') or 0)
    idle_time_percentage = float(driver.get('IdlingValue') or 0)
    coasting_percentage = float(driver.get('CoastingValue') or 0)
    anticipation_score = float(driver.get('AnticipationScaniaDriverSupport') or 0)

    # Compliance features
    total_distance_km = float(driver.get('Distance') or 0)
    average_speed_kmh = float(driver.get('AverageSpeed') or 0)
    total_fuel_liters = float(driver.get('TotalFuelConsumption') or 0)
    fuel_idling_liters = float(driver.get('TotalFuelConsumptionIdling') or 0)

    # Cruise control usage
    distance_with_cruise = float(driver.get('DistanceWithCruiseControl') or 0)
    cruise_control_usage_pct = (distance_with_cruise / total_distance_km * 100) if total_distance_km > 0 else 0

    # Composite scores from Scania
    scania_driver_support_score = float(driver.get('ScaniaDriverSupportValue') or 0)
    hill_driving_score = float(driver.get('HillDrivingScaniaDriverSupport') or 0)

    # CO2 calculations
    co2_total_kg = total_fuel_liters * CO2_PER_LITER_DIESEL
    co2_per_km = (co2_total_kg / total_distance_km) if total_distance_km > 0 else 0
    co2_from_idling_kg = fuel_idling_liters * CO2_PER_LITER_DIESEL

    # Carbon efficiency score based on real data distribution (Oct 2024, Villa Mercedes)
    # P10: 0.690 kg/km, Median: 0.738 kg/km, P90: 0.767 kg/km
    # Formula: linear scale from 0.65 kg/km (100 pts) to 0.80 kg/km (0 pts)
    carbon_efficiency_score = max(0, min(100, ((0.80 - co2_per_km) / 0.15) * 100))

    # Calculate our composite scores
    safety_score = calculate_safety_score(
        harsh_braking_per_100km,
        speeding_percentage,
        brake_score,
        harsh_accel_per_100km
    )

    efficiency_score = calculate_efficiency_score(
        fuel_per_100km,
        idle_time_percentage,
        cruise_control_usage_pct,
        anticipation_score
    )

    compliance_score = calculate_compliance_score(
        total_distance_km,
        average_speed_kmh
    )

    # Overall driver score
    driver_score_base = (
        0.40 * safety_score +
        0.35 * efficiency_score +
        0.25 * compliance_score
    )

    return {
        'driver_id': driver_id,
        'driver_name': driver_name,

        # Distance and compliance
        'total_distance_km': total_distance_km,
        'avg_speed_kmh': average_speed_kmh,

        # Safety features
        'harsh_braking_count': harsh_braking_count,
        'harsh_braking_per_100km_avg': harsh_braking_per_100km,
        'harsh_acceleration_per_100km_avg': harsh_accel_per_100km,
        'speeding_percentage_avg': speeding_percentage,
        'brake_score_avg': brake_score,

        # Efficiency features
        'fuel_per_100km_avg': fuel_per_100km,
        'total_fuel_liters': total_fuel_liters,
        'idle_time_percentage_avg': idle_time_percentage,
        'fuel_idling_liters': fuel_idling_liters,
        'coasting_percentage_avg': coasting_percentage,
        'cruise_control_usage_pct_avg': cruise_control_usage_pct,
        'anticipation_score_avg': anticipation_score,

        # Composite scores from Scania
        'scania_driver_support_score_avg': scania_driver_support_score,
        'hill_driving_score_avg': hill_driving_score,

        # CO2 metrics
        'total_co2_emissions_kg': co2_total_kg,
        'avg_co2_per_km': co2_per_km,
        'total_co2_from_idling_kg': co2_from_idling_kg,
        'carbon_efficiency_score_avg': carbon_efficiency_score,

        # Our calculated scores
        'safety_score': round(safety_score, 2),
        'efficiency_score': round(efficiency_score, 2),
        'compliance_score': round(compliance_score, 2),
        'driver_score_base': round(driver_score_base, 2)
    }


def calculate_safety_score(harsh_braking: float, speeding: float,
                          brake_score: float, harsh_accel: float) -> float:
    """
    Calculate composite safety score.

    Components:
    - Low harsh braking (40%)
    - Low speeding (30%)
    - High brake score (20%)
    - Low harsh acceleration (10%)

    Returns:
        float: Safety score (0-100)
    """
    # Normalize harsh braking (inverse: lower is better)
    harsh_braking_norm = max(0, 100 - (harsh_braking * 100))

    # Normalize speeding (inverse: lower is better)
    speeding_norm = max(0, 100 - speeding)

    # Brake score is already 0-100 (higher is better)
    brake_score_norm = brake_score

    # Normalize harsh acceleration (inverse: lower is better)
    harsh_accel_norm = max(0, 100 - (harsh_accel * 100))

    # Weighted composite
    safety_score = (
        0.40 * harsh_braking_norm +
        0.30 * speeding_norm +
        0.20 * brake_score_norm +
        0.10 * harsh_accel_norm
    )

    return safety_score


def calculate_efficiency_score(fuel: float, idle: float,
                               cruise: float, anticipation: float) -> float:
    """
    Calculate composite efficiency score.

    Components:
    - Low fuel consumption (35%)
    - Low idle time (25%)
    - High cruise control usage (20%)
    - High anticipation score (20%)

    Returns:
        float: Efficiency score (0-100)
    """
    # Normalize fuel consumption (inverse: lower is better)
    # Based on Scania Fleet Management benchmarks for Euro 6 long-haul trucks:
    # - Excellent: 22-26 L/100km (optimal driving, efficient load)
    # - Average: 26-30 L/100km
    # - Poor: >32 L/100km (aggressive driving, overload)
    # Formula: linear scale from 22 (100 pts) to 32 (0 pts)
    fuel_norm = max(0, min(100, ((32 - fuel) / 10) * 100))

    # Normalize idle time (inverse: lower is better)
    idle_norm = max(0, 100 - (idle * 5))

    # Cruise control usage percentage (higher is better)
    cruise_norm = cruise

    # Anticipation score is already 0-100 (higher is better)
    anticipation_norm = anticipation

    # Weighted composite
    efficiency_score = (
        0.35 * fuel_norm +
        0.25 * idle_norm +
        0.20 * cruise_norm +
        0.20 * anticipation_norm
    )

    return efficiency_score


def calculate_compliance_score(distance: float, avg_speed: float) -> float:
    """
    Calculate composite compliance score.

    Components:
    - Total distance driven (60%)
    - Average speed within limits (40%)

    Returns:
        float: Compliance score (0-100)
    """
    # Normalize total distance (experience/activity indicator)
    # Based on real data: October 2024 (28 business days in Argentina)
    # - Low activity: <5,000 km (~180 km/day)
    # - Average: 8,000 km (~285 km/day)
    # - High activity: 15,000+ km (~535 km/day)
    # Formula: linear scale from 0 km (0 pts) to 15,000 km (100 pts)
    distance_norm = min(100, (distance / 150))

    # Normalize average speed (should be reasonable, not too low or high)
    # Note: Scania's AverageSpeed = distance / total_engine_time (includes idle & PTO)
    # Based on real interurban routes in Argentina with loading/unloading stops:
    # - Too low: <35 km/h (excessive idle, delays)
    # - Optimal: 50-70 km/h (cruise 80-90 km/h with realistic stops)
    # - Risky: >80 km/h (speeding, safety risk)
    if 50 <= avg_speed <= 70:
        speed_norm = 100
    elif avg_speed < 50:
        speed_norm = max(0, 50 + (avg_speed - 35) * 2)
    else:  # > 70
        speed_norm = max(0, 100 - ((avg_speed - 70) * 3))

    # Weighted composite
    compliance_score = (
        0.60 * distance_norm +
        0.40 * speed_norm
    )

    return compliance_score


def generate_processing_report(df: pd.DataFrame) -> str:
    """
    Generate a detailed processing report.

    Args:
        df: Driver features DataFrame

    Returns:
        str: Formatted report
    """
    report = []
    report.append("=" * 80)
    report.append("FEATURE PROCESSING REPORT")
    report.append("=" * 80)
    report.append("")

    # Driver statistics
    report.append("DRIVER STATISTICS")
    report.append("-" * 80)
    report.append(f"Total drivers processed: {len(df)}")
    report.append(f"Total distance: {df['total_distance_km'].sum():,.0f} km")
    report.append(f"Total fuel consumed: {df['total_fuel_liters'].sum():,.0f} liters")
    report.append(f"Total CO2 emissions: {df['total_co2_emissions_kg'].sum():,.0f} kg")
    report.append("")

    # Score statistics
    report.append("AVERAGE SCORES")
    report.append("-" * 80)
    report.append(f"Safety Score: {df['safety_score'].mean():.2f}")
    report.append(f"Efficiency Score: {df['efficiency_score'].mean():.2f}")
    report.append(f"Compliance Score: {df['compliance_score'].mean():.2f}")
    report.append(f"Overall Score: {df['driver_score_base'].mean():.2f}")
    report.append("")

    # CO2 metrics
    report.append("CO2 EMISSIONS")
    report.append("-" * 80)
    report.append(f"Average CO2 per km: {df['avg_co2_per_km'].mean():.3f} kg")
    report.append(f"Total CO2 emissions: {df['total_co2_emissions_kg'].sum():,.0f} kg")
    report.append(f"CO2 from idling: {df['total_co2_from_idling_kg'].sum():,.0f} kg ({df['total_co2_from_idling_kg'].sum() / df['total_co2_emissions_kg'].sum() * 100:.1f}% of total)")
    report.append(f"Carbon efficiency score: {df['carbon_efficiency_score_avg'].mean():.2f}")
    report.append("")

    # Top performers
    report.append("TOP 5 DRIVERS (by overall score)")
    report.append("-" * 80)
    top_drivers = df.nlargest(5, 'driver_score_base')[
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
        raw_data = load_scania_data(Path(args.input))

        # Extract drivers
        drivers = raw_data.get('Drivers', [])

        if not drivers:
            logger.error("No drivers found in raw data!")
            logger.error("Check if the JSON structure is correct.")
            sys.exit(1)

        logger.info(f"Processing {len(drivers)} drivers...")

        # Process each driver
        driver_features = []
        for driver in drivers:
            try:
                features = extract_driver_features(driver)
                driver_features.append(features)
            except Exception as e:
                logger.warning(f"Failed to process driver {driver.get('DriverName')}: {e}")
                continue

        # Create DataFrame
        df = pd.DataFrame(driver_features)

        # Save
        output_path = Path(args.output)
        df.to_csv(output_path, index=False)
        logger.info(f"OK - Saved {len(df)} drivers to: {output_path}")

        # Generate and save report
        report = generate_processing_report(df)
        report_path = output_path.parent / 'processing_report.txt'

        with open(report_path, 'w') as f:
            f.write(report)

        logger.info(f"OK - Saved processing report to: {report_path}")
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
