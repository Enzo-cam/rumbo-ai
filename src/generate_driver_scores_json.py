"""
Generate Final Driver Scores JSON for API

This script generates the final driver_scores.json file with all driver
information, scores, and fleet statistics in a format ready for the API backend.

Input: data/drivers_clustered.csv (from train_driver_clustering.py)
Output: data/driver_scores.json

JSON Structure:
{
  "generated_at": "2025-11-06T00:00:00",
  "drivers": [...],
  "fleet_statistics": {...}
}

Usage:
    python generate_driver_scores_json.py --input data/drivers_clustered.csv
"""

import json
import logging
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("ERROR: pandas and numpy required. Run: pip install pandas numpy")
    sys.exit(1)

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
ALPHA = 0.15  # Weight for kilometer balancing adjustment

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_clustered_drivers(file_path: Path) -> pd.DataFrame:
    """
    Load clustered driver data.

    Args:
        file_path: Path to clustered drivers CSV

    Returns:
        DataFrame: Clustered driver data
    """
    logger.info(f"Loading clustered drivers from: {file_path}")

    try:
        df = pd.read_csv(file_path)
        logger.info(f"✓ Loaded {len(df)} drivers")
        return df

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        logger.error("Run train_driver_clustering.py first to generate clustered data")
        raise


def calculate_adjusted_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate km-balance adjusted driver scores.

    Formula:
    - km_balance = mean_fleet_km - driver_km
    - driver_score_adjusted = driver_score_base + (alpha * km_balance_scaled)

    Args:
        df: Driver data

    Returns:
        DataFrame: Driver data with adjusted scores
    """
    logger.info("Calculating adjusted scores with km balancing...")

    df = df.copy()

    # Calculate kilometer balance
    mean_km = df['total_distance_km'].mean()
    df['km_balance'] = mean_km - df['total_distance_km']

    # Scale km_balance to [-10, 10] range
    std_km = df['total_distance_km'].std()
    if std_km > 0:
        df['km_balance_scaled'] = (df['km_balance'] / std_km) * 5
        df['km_balance_scaled'] = df['km_balance_scaled'].clip(-10, 10)
    else:
        df['km_balance_scaled'] = 0

    # Calculate adjusted score
    df['driver_score_adjusted'] = df['driver_score_base'] + (ALPHA * df['km_balance_scaled'])
    df['driver_score_adjusted'] = df['driver_score_adjusted'].clip(0, 100).round(2)

    logger.info(f"  Mean adjustment: {(df['driver_score_adjusted'] - df['driver_score_base']).mean():.2f} points")
    logger.info("✓ Adjusted scores calculated")

    return df


def format_driver_json(driver: pd.Series) -> Dict:
    """
    Format a single driver's data for JSON output.

    Args:
        driver: Driver row from DataFrame

    Returns:
        Dict: Formatted driver data
    """
    return {
        "driver_id": str(driver['driver_id']),
        "driver_name": str(driver['driver_name']),

        # Clustering info
        "cluster": int(driver['cluster']),
        "cluster_name": str(driver['cluster_name']),

        # Scores
        "safety_score": round(float(driver['safety_score']), 2),
        "efficiency_score": round(float(driver['efficiency_score']), 2),
        "compliance_score": round(float(driver['compliance_score']), 2),
        "overall_score": round(float(driver['driver_score_adjusted']), 2),

        # Experience metrics
        "total_trips": int(driver['total_trips']),
        "km_accumulated": round(float(driver['total_distance_km']), 2),
        "km_balance": round(float(driver['km_balance']), 2),

        # Behavior metrics
        "harsh_braking_avg": round(float(driver['harsh_braking_per_100km_avg']), 3),
        "speeding_percentage_avg": round(float(driver['speeding_percentage_avg']), 2),
        "fuel_consumption_avg": round(float(driver['fuel_per_100km_avg']), 2),
        "idle_time_percentage_avg": round(float(driver['idle_time_percentage_avg']), 2),
        "cruise_control_usage_pct": round(float(driver['cruise_control_usage_pct_avg']), 2),

        # Scania scores
        "scania_support_score": round(float(driver['scania_driver_support_score_avg']), 2),
        "brake_score": round(float(driver['brake_score_avg']), 2),
        "anticipation_score": round(float(driver['anticipation_score_avg']), 2),

        # CO2 metrics
        "co2_per_km": round(float(driver['avg_co2_per_km']), 3),
        "total_co2_emissions_kg": round(float(driver['total_co2_emissions_kg']), 2),
        "carbon_efficiency_score": round(float(driver['carbon_efficiency_score_avg']), 2)
    }


def calculate_fleet_statistics(df: pd.DataFrame) -> Dict:
    """
    Calculate fleet-wide statistics.

    Args:
        df: Driver data

    Returns:
        Dict: Fleet statistics
    """
    logger.info("Calculating fleet statistics...")

    # Cluster distribution
    cluster_dist = df.groupby('cluster_name').size().to_dict()

    # Average scores
    avg_safety = df['safety_score'].mean()
    avg_efficiency = df['efficiency_score'].mean()
    avg_compliance = df['compliance_score'].mean()
    avg_overall = df['driver_score_adjusted'].mean()

    # CO2 metrics
    total_co2 = df['total_co2_emissions_kg'].sum()
    avg_co2_per_km = df['avg_co2_per_km'].mean()

    # Fleet performance ranges
    score_ranges = {
        "excellent": (df['driver_score_adjusted'] >= 85).sum(),
        "good": ((df['driver_score_adjusted'] >= 70) & (df['driver_score_adjusted'] < 85)).sum(),
        "average": ((df['driver_score_adjusted'] >= 60) & (df['driver_score_adjusted'] < 70)).sum(),
        "needs_improvement": (df['driver_score_adjusted'] < 60).sum()
    }

    statistics = {
        "total_drivers": int(len(df)),
        "total_trips": int(df['total_trips'].sum()),
        "total_km_driven": round(float(df['total_distance_km'].sum()), 2),

        "avg_safety_score": round(float(avg_safety), 2),
        "avg_efficiency_score": round(float(avg_efficiency), 2),
        "avg_compliance_score": round(float(avg_compliance), 2),
        "avg_overall_score": round(float(avg_overall), 2),

        "cluster_distribution": cluster_dist,
        "performance_distribution": score_ranges,

        "avg_co2_per_km_fleet": round(float(avg_co2_per_km), 3),
        "total_co2_emissions_fleet_kg": round(float(total_co2), 2),

        "top_performer": {
            "driver_id": str(df.loc[df['driver_score_adjusted'].idxmax(), 'driver_id']),
            "driver_name": str(df.loc[df['driver_score_adjusted'].idxmax(), 'driver_name']),
            "score": round(float(df['driver_score_adjusted'].max()), 2)
        },

        "most_experienced": {
            "driver_id": str(df.loc[df['total_distance_km'].idxmax(), 'driver_id']),
            "driver_name": str(df.loc[df['total_distance_km'].idxmax(), 'driver_name']),
            "km": round(float(df['total_distance_km'].max()), 2)
        }
    }

    logger.info(f"  Total drivers: {statistics['total_drivers']}")
    logger.info(f"  Avg overall score: {statistics['avg_overall_score']:.2f}")
    logger.info(f"  Cluster distribution: {cluster_dist}")
    logger.info("✓ Fleet statistics calculated")

    return statistics


def generate_driver_scores_json(df: pd.DataFrame, output_path: Path):
    """
    Generate final driver_scores.json file.

    Args:
        df: Driver data with adjusted scores
        output_path: Path to save JSON file
    """
    logger.info("Generating driver_scores.json...")

    # Sort drivers by adjusted score (descending)
    df_sorted = df.sort_values('driver_score_adjusted', ascending=False)

    # Format drivers
    drivers_list = [format_driver_json(row) for _, row in df_sorted.iterrows()]

    # Calculate fleet statistics
    fleet_stats = calculate_fleet_statistics(df)

    # Create final JSON structure
    output_data = {
        "generated_at": datetime.now().isoformat(),
        "version": "1.0",
        "data_source": "Scania Driver Evaluation Report v2",
        "drivers": drivers_list,
        "fleet_statistics": fleet_stats
    }

    # Save JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    file_size = output_path.stat().st_size / 1024  # KB
    logger.info(f"✓ Saved driver_scores.json to: {output_path}")
    logger.info(f"  File size: {file_size:.2f} KB")
    logger.info(f"  Total drivers: {len(drivers_list)}")


def generate_summary_report(df: pd.DataFrame, fleet_stats: Dict) -> str:
    """
    Generate human-readable summary report.

    Args:
        df: Driver data
        fleet_stats: Fleet statistics

    Returns:
        str: Formatted report
    """
    report = []
    report.append("=" * 80)
    report.append("DRIVER SCORES GENERATION REPORT")
    report.append("=" * 80)
    report.append("")

    report.append("FLEET OVERVIEW")
    report.append("-" * 80)
    report.append(f"Total Drivers: {fleet_stats['total_drivers']}")
    report.append(f"Total Trips: {fleet_stats['total_trips']}")
    report.append(f"Total Distance: {fleet_stats['total_km_driven']:,.0f} km")
    report.append("")

    report.append("AVERAGE SCORES")
    report.append("-" * 80)
    report.append(f"Safety Score: {fleet_stats['avg_safety_score']:.2f}")
    report.append(f"Efficiency Score: {fleet_stats['avg_efficiency_score']:.2f}")
    report.append(f"Compliance Score: {fleet_stats['avg_compliance_score']:.2f}")
    report.append(f"Overall Score: {fleet_stats['avg_overall_score']:.2f}")
    report.append("")

    report.append("CLUSTER DISTRIBUTION")
    report.append("-" * 80)
    for cluster_name, count in fleet_stats['cluster_distribution'].items():
        pct = (count / fleet_stats['total_drivers']) * 100
        report.append(f"{cluster_name}: {count} drivers ({pct:.1f}%)")
    report.append("")

    report.append("PERFORMANCE DISTRIBUTION")
    report.append("-" * 80)
    for level, count in fleet_stats['performance_distribution'].items():
        pct = (count / fleet_stats['total_drivers']) * 100
        report.append(f"{level.replace('_', ' ').title()}: {count} drivers ({pct:.1f}%)")
    report.append("")

    report.append("TOP PERFORMERS")
    report.append("-" * 80)
    top_5 = df.nlargest(5, 'driver_score_adjusted')[
        ['driver_name', 'driver_score_adjusted', 'cluster_name', 'safety_score', 'efficiency_score']
    ]
    for idx, (_, driver) in enumerate(top_5.iterrows(), 1):
        report.append(f"{idx}. {driver['driver_name']} - Score: {driver['driver_score_adjusted']:.2f} ({driver['cluster_name']})")
        report.append(f"   Safety: {driver['safety_score']:.2f}, Efficiency: {driver['efficiency_score']:.2f}")
    report.append("")

    report.append("CO2 METRICS")
    report.append("-" * 80)
    report.append(f"Fleet Average: {fleet_stats['avg_co2_per_km_fleet']:.3f} kg CO2/km")
    report.append(f"Total CO2 Emissions: {fleet_stats['total_co2_emissions_fleet_kg']:,.0f} kg")
    report.append("")

    report.append("=" * 80)
    report.append("Driver scores generation completed successfully!")
    report.append("=" * 80)

    return "\n".join(report)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Generate final driver scores JSON for API'
    )
    parser.add_argument(
        '--input',
        type=str,
        help='Input clustered drivers CSV',
        default=str(DATA_DIR / 'drivers_clustered.csv')
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output JSON file path',
        default=str(DATA_DIR / 'driver_scores.json')
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("DRIVER SCORES JSON GENERATION")
    logger.info("=" * 80)
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")
    logger.info("")

    try:
        # Load clustered drivers
        df = load_clustered_drivers(Path(args.input))

        # Calculate adjusted scores
        df_adjusted = calculate_adjusted_scores(df)

        # Calculate fleet statistics
        fleet_stats = calculate_fleet_statistics(df_adjusted)

        # Generate JSON
        output_path = Path(args.output)
        generate_driver_scores_json(df_adjusted, output_path)

        # Generate and save summary report
        report = generate_summary_report(df_adjusted, fleet_stats)
        report_path = output_path.parent / 'driver_scores_report.txt'

        with open(report_path, 'w') as f:
            f.write(report)

        logger.info(f"✓ Saved summary report to: {report_path}")
        logger.info("")
        print(report)

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"GENERATION FAILED: {e}")
        logger.error("=" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
