"""
Master Pipeline Script for RUMBO Driver ML Pipeline

This script orchestrates the complete ML pipeline for driver analysis:
1. Extract data from Scania API
2. Process features
3. Train clustering model
4. Generate driver_scores.json

Usage:
    # Full pipeline
    python run_pipeline.py --start-date 202510210000 --end-date 202510310000

    # Skip extraction (use existing raw data)
    python run_pipeline.py --skip-extraction

    # Use specific raw data file
    python run_pipeline.py --raw-data data/raw_driver_trips.json --skip-extraction
"""

import sys
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_command(command: list, description: str) -> bool:
    """
    Run a subprocess command and log results.

    Args:
        command: Command to run as list
        description: Description of the command

    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("=" * 80)
    logger.info(f"STEP: {description}")
    logger.info("=" * 80)
    logger.info(f"Command: {' '.join(command)}")
    logger.info("")

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=False,  # Show output in real-time
            text=True
        )
        logger.info(f"✓ {description} completed successfully")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {description} failed with return code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Run complete RUMBO driver ML pipeline'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date for Scania data (YYYYMMDDHHMM)',
        default=None
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date for Scania data (YYYYMMDDHHMM)',
        default=None
    )
    parser.add_argument(
        '--skip-extraction',
        action='store_true',
        help='Skip data extraction (use existing raw data)'
    )
    parser.add_argument(
        '--raw-data',
        type=str,
        help='Path to existing raw data JSON',
        default='data/raw_driver_trips.json'
    )
    parser.add_argument(
        '--k-clusters',
        type=int,
        help='Number of clusters (auto-detect if not specified)',
        default=None
    )

    args = parser.parse_args()

    logger.info("")
    logger.info("🚀" * 40)
    logger.info("RUMBO DRIVER ML PIPELINE")
    logger.info("🚀" * 40)
    logger.info("")
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Skip Extraction: {args.skip_extraction}")
    if not args.skip_extraction:
        logger.info(f"Date Range: {args.start_date or 'auto'} to {args.end_date or 'auto'}")
    logger.info("")

    # Pipeline steps
    steps_completed = 0
    total_steps = 4 if not args.skip_extraction else 3

    # Step 1: Extract data from Scania API
    if not args.skip_extraction:
        cmd = ['python', 'src/extract_scania_data.py']
        if args.start_date:
            cmd.extend(['--start-date', args.start_date])
        if args.end_date:
            cmd.extend(['--end-date', args.end_date])

        if not run_command(cmd, "Extract data from Scania API"):
            logger.error("Pipeline aborted due to extraction failure")
            sys.exit(1)
        steps_completed += 1
        logger.info(f"Progress: {steps_completed}/{total_steps} steps completed")
        logger.info("")

    # Step 2: Process features
    cmd = ['python', 'src/process_features.py', '--input', args.raw_data]
    if not run_command(cmd, "Process driver features"):
        logger.error("Pipeline aborted due to feature processing failure")
        sys.exit(1)
    steps_completed += 1
    logger.info(f"Progress: {steps_completed}/{total_steps} steps completed")
    logger.info("")

    # Step 3: Train clustering
    cmd = ['python', 'src/train_driver_clustering.py']
    if args.k_clusters:
        cmd.extend(['--k', str(args.k_clusters)])

    if not run_command(cmd, "Train K-Means clustering"):
        logger.error("Pipeline aborted due to clustering failure")
        sys.exit(1)
    steps_completed += 1
    logger.info(f"Progress: {steps_completed}/{total_steps} steps completed")
    logger.info("")

    # Step 4: Generate driver scores JSON
    cmd = ['python', 'src/generate_driver_scores_json.py']
    if not run_command(cmd, "Generate driver_scores.json"):
        logger.error("Pipeline aborted due to JSON generation failure")
        sys.exit(1)
    steps_completed += 1
    logger.info(f"Progress: {steps_completed}/{total_steps} steps completed")
    logger.info("")

    # Pipeline completed
    logger.info("")
    logger.info("✅" * 40)
    logger.info("PIPELINE COMPLETED SUCCESSFULLY!")
    logger.info("✅" * 40)
    logger.info("")
    logger.info(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    logger.info("Generated Files:")
    logger.info("  - data/raw_driver_trips.json (if extracted)")
    logger.info("  - data/trips_processed.csv")
    logger.info("  - data/drivers_features.csv")
    logger.info("  - data/drivers_clustered.csv")
    logger.info("  - data/driver_scores.json ⭐")
    logger.info("  - models/driver_clustering_model.pkl")
    logger.info("  - outputs/clustering_report.txt")
    logger.info("  - outputs/optimal_k_analysis.png")
    logger.info("  - outputs/clusters_pca.png")
    logger.info("")
    logger.info("Next Steps:")
    logger.info("  1. Review driver_scores.json")
    logger.info("  2. Check clustering visualizations in outputs/")
    logger.info("  3. Deploy driver_scores.json to your API backend")
    logger.info("")


if __name__ == "__main__":
    main()
