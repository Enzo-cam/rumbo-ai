"""
Extract Driver Evaluation Data from Scania Fleet Management API

This script connects to Scania's Driver Evaluation Report API and fetches
driver behavior data for a specified date range.

API Documentation:
- Endpoint: https://dataaccess.scania.com/cs/driver/reports/DriverEvaluationReport/v2
- Authentication: Bearer Token (OAuth 2.0)
- Date Format: YYYYMMDDHHMM (e.g., 202510210000)

Usage:
    python extract_scania_data.py --start-date 202510210000 --end-date 202510310000

Environment Variables:
    SCANIA_API_TOKEN: Bearer token for Scania API authentication

Output:
    data/raw_driver_trips.json - Raw API response
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
import time

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("ERROR: 'requests' library not installed. Run: pip install requests")
    sys.exit(1)

# Configuration
API_BASE_URL = "https://dataaccess.scania.com/cs/driver/reports"
API_ENDPOINT = f"{API_BASE_URL}/DriverEvaluationReport/v2"
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(DATA_DIR / 'scania_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def create_session_with_retries() -> requests.Session:
    """
    Create a requests session with automatic retry logic for robustness.

    Retry strategy:
    - Total retries: 3
    - Backoff factor: 1 (waits 1s, 2s, 4s between retries)
    - Retry on: 500, 502, 503, 504 (server errors)
    """
    session = requests.Session()

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def get_api_token() -> str:
    """
    Get Scania API token from environment variable.

    Returns:
        str: Bearer token

    Raises:
        EnvironmentError: If SCANIA_API_TOKEN is not set
    """
    token = os.getenv('SCANIA_API_TOKEN')

    if not token:
        raise EnvironmentError(
            "SCANIA_API_TOKEN environment variable is not set.\n"
            "Please set it with: export SCANIA_API_TOKEN='your_token_here'"
        )

    return token


def validate_date_format(date_str: str) -> bool:
    """
    Validate date string format (YYYYMMDDHHMM).

    Args:
        date_str: Date string to validate

    Returns:
        bool: True if valid format
    """
    try:
        datetime.strptime(date_str, '%Y%m%d%H%M')
        return True
    except ValueError:
        return False


def fetch_driver_evaluation_report(
    start_date: str,
    end_date: str,
    driver_ref_list: Optional[List[str]] = None,
    timeout: int = 60
) -> Dict:
    """
    Fetch Driver Evaluation Report from Scania API.

    Args:
        start_date: Start date in format YYYYMMDDHHMM (e.g., 202510210000)
        end_date: End date in format YYYYMMDDHHMM (e.g., 202510310000)
        driver_ref_list: Optional list of specific driver IDs (empty = all drivers)
        timeout: Request timeout in seconds

    Returns:
        Dict: API response JSON

    Raises:
        ValueError: If date format is invalid
        requests.RequestException: If API request fails
    """
    # Validate date formats
    if not validate_date_format(start_date):
        raise ValueError(f"Invalid start_date format: {start_date}. Expected: YYYYMMDDHHMM")
    if not validate_date_format(end_date):
        raise ValueError(f"Invalid end_date format: {end_date}. Expected: YYYYMMDDHHMM")

    # Get API token
    token = get_api_token()

    # Prepare headers
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    # Prepare query parameters
    params = {
        'startDate': start_date,
        'endDate': end_date
    }

    # Add driver filter if specified
    if driver_ref_list:
        params['driverRefList'] = ','.join(driver_ref_list)

    logger.info(f"Fetching driver data from {start_date} to {end_date}")
    logger.info(f"API Endpoint: {API_ENDPOINT}")
    logger.info(f"Params: {params}")

    # Create session with retries
    session = create_session_with_retries()

    try:
        # Make API request
        response = session.get(
            API_ENDPOINT,
            headers=headers,
            params=params,
            timeout=timeout
        )

        # Log response status
        logger.info(f"Response Status: {response.status_code}")

        # Raise exception for bad status codes
        response.raise_for_status()

        # Parse JSON response
        data = response.json()

        logger.info(f"Successfully fetched data")

        # Log basic stats
        if 'EvaluationVehicles' in data:
            vehicles = data.get('EvaluationVehicles', [])
            total_trips = sum(len(v.get('Trips', [])) for v in vehicles)
            logger.info(f"Total vehicles: {len(vehicles)}")
            logger.info(f"Total trips: {total_trips}")

        return data

    except requests.exceptions.Timeout:
        logger.error(f"Request timeout after {timeout}s")
        raise
    except requests.exceptions.ConnectionError:
        logger.error("Connection error - check network connectivity")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        logger.error(f"Response body: {response.text}")
        raise
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        logger.error(f"Response body: {response.text}")
        raise
    finally:
        session.close()


def save_raw_data(data: Dict, output_path: Path) -> None:
    """
    Save raw API response to JSON file.

    Args:
        data: API response data
        output_path: Path to output JSON file
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ Saved raw data to: {output_path}")

        # Log file size
        file_size = output_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        logger.info(f"  File size: {file_size_mb:.2f} MB")

    except Exception as e:
        logger.error(f"Failed to save raw data: {e}")
        raise


def generate_metadata(data: Dict, start_date: str, end_date: str) -> Dict:
    """
    Generate metadata about the extracted dataset.

    Args:
        data: API response data
        start_date: Start date used for extraction
        end_date: End date used for extraction

    Returns:
        Dict: Metadata dictionary
    """
    vehicles = data.get('EvaluationVehicles', [])

    # Collect unique drivers
    drivers = set()
    trips = []

    for vehicle in vehicles:
        for trip in vehicle.get('Trips', []):
            driver_id = trip.get('DriverRef') or trip.get('DriverName')
            if driver_id:
                drivers.add(driver_id)
            trips.append(trip)

    metadata = {
        'extraction_date': datetime.now().isoformat(),
        'start_date': start_date,
        'end_date': end_date,
        'total_vehicles': len(vehicles),
        'total_drivers': len(drivers),
        'total_trips': len(trips),
        'api_version': 'v2',
        'data_source': 'Scania Driver Evaluation Report'
    }

    return metadata


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Extract driver evaluation data from Scania API'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date in format YYYYMMDDHHMM (default: 30 days ago)',
        default=None
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date in format YYYYMMDDHHMM (default: now)',
        default=None
    )
    parser.add_argument(
        '--drivers',
        type=str,
        nargs='+',
        help='Specific driver IDs to fetch (optional, default: all)',
        default=None
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (default: data/raw_driver_trips.json)',
        default=str(DATA_DIR / 'raw_driver_trips.json')
    )

    args = parser.parse_args()

    # Generate default dates if not provided
    if not args.end_date:
        end_dt = datetime.now()
        args.end_date = end_dt.strftime('%Y%m%d%H%M')

    if not args.start_date:
        end_dt = datetime.strptime(args.end_date, '%Y%m%d%H%M')
        start_dt = end_dt - timedelta(days=30)
        args.start_date = start_dt.strftime('%Y%m%d%H%M')

    logger.info("="*80)
    logger.info("SCANIA DATA EXTRACTION")
    logger.info("="*80)
    logger.info(f"Start Date: {args.start_date}")
    logger.info(f"End Date: {args.end_date}")
    logger.info(f"Output: {args.output}")
    logger.info("")

    try:
        # Fetch data from API
        data = fetch_driver_evaluation_report(
            start_date=args.start_date,
            end_date=args.end_date,
            driver_ref_list=args.drivers
        )

        # Generate metadata
        metadata = generate_metadata(data, args.start_date, args.end_date)

        # Add metadata to response
        data['_metadata'] = metadata

        # Save raw data
        output_path = Path(args.output)
        save_raw_data(data, output_path)

        # Save metadata separately
        metadata_path = output_path.parent / 'extraction_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"✓ Saved metadata to: {metadata_path}")
        logger.info("")
        logger.info("="*80)
        logger.info("EXTRACTION SUMMARY")
        logger.info("="*80)
        logger.info(f"Total Vehicles: {metadata['total_vehicles']}")
        logger.info(f"Total Drivers: {metadata['total_drivers']}")
        logger.info(f"Total Trips: {metadata['total_trips']}")
        logger.info("")
        logger.info("✓ Extraction completed successfully!")
        logger.info("="*80)

    except Exception as e:
        logger.error("="*80)
        logger.error(f"EXTRACTION FAILED: {e}")
        logger.error("="*80)
        sys.exit(1)


if __name__ == "__main__":
    main()
