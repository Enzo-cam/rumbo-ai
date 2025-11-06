"""
Train K-Means Clustering Model for Driver Segmentation

This script trains an unsupervised K-Means clustering model to automatically
segment drivers into behavioral groups (e.g., Conservative, Balanced, Aggressive).

Input: data/drivers_features.csv (from process_features.py)
Output:
    - data/drivers_clustered.csv (drivers with cluster labels)
    - models/driver_clustering_model.pkl (trained model)
    - outputs/clustering_report.txt (detailed analysis)

Usage:
    python train_driver_clustering.py --input data/drivers_features.csv
"""

import logging
import argparse
import sys
import pickle
from pathlib import Path
from typing import Dict, Tuple

try:
    import pandas as pd
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score, davies_bouldin_score
    from sklearn.decomposition import PCA
except ImportError:
    print("ERROR: Required libraries not installed. Run:")
    print("pip install pandas numpy matplotlib seaborn scikit-learn")
    sys.exit(1)

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
MODELS_DIR = Path(__file__).parent.parent / "models"
OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"

# Create directories
MODELS_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

# Clustering features (based on RUMBO.md specification)
CLUSTERING_FEATURES = [
    'harsh_braking_per_100km_avg',
    'fuel_per_100km_avg',
    'idle_time_percentage_avg',
    'scania_driver_support_score_avg',
    'speeding_percentage_avg'
]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_driver_features(file_path: Path) -> pd.DataFrame:
    """
    Load driver features from CSV.

    Args:
        file_path: Path to driver features CSV

    Returns:
        DataFrame: Driver features
    """
    logger.info(f"Loading driver features from: {file_path}")

    try:
        df = pd.read_csv(file_path)
        logger.info(f"✓ Loaded {len(df)} drivers")

        # Validate required features exist
        missing_features = [f for f in CLUSTERING_FEATURES if f not in df.columns]
        if missing_features:
            raise ValueError(f"Missing required features: {missing_features}")

        return df

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        logger.error("Run process_features.py first to generate driver features")
        raise


def prepare_clustering_data(df: pd.DataFrame) -> Tuple[np.ndarray, StandardScaler]:
    """
    Prepare and normalize data for clustering.

    Args:
        df: Driver features DataFrame

    Returns:
        Tuple of (normalized features, scaler object)
    """
    logger.info("Preparing data for clustering...")

    # Extract clustering features
    X = df[CLUSTERING_FEATURES].copy()

    # Handle missing values
    if X.isnull().any().any():
        logger.warning("Found missing values, filling with median")
        X = X.fillna(X.median())

    # Normalize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    logger.info(f"✓ Prepared {X_scaled.shape[0]} samples with {X_scaled.shape[1]} features")

    return X_scaled, scaler


def find_optimal_k(X: np.ndarray, k_range: range = range(2, 6)) -> Dict:
    """
    Use elbow method and silhouette score to find optimal K.

    Args:
        X: Normalized feature matrix
        k_range: Range of K values to test

    Returns:
        Dict with inertias, silhouette scores, and recommended K
    """
    logger.info(f"Finding optimal K (testing K={list(k_range)})...")

    inertias = []
    silhouette_scores = []

    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)

        inertias.append(kmeans.inertia_)

        # Calculate silhouette score
        silhouette_avg = silhouette_score(X, labels)
        silhouette_scores.append(silhouette_avg)

        logger.info(f"  K={k}: Inertia={kmeans.inertia_:.2f}, Silhouette={silhouette_avg:.3f}")

    # Find K with best silhouette score
    best_k = list(k_range)[np.argmax(silhouette_scores)]

    logger.info(f"✓ Recommended K: {best_k} (Silhouette Score: {max(silhouette_scores):.3f})")

    return {
        'k_range': list(k_range),
        'inertias': inertias,
        'silhouette_scores': silhouette_scores,
        'optimal_k': best_k
    }


def train_kmeans(X: np.ndarray, n_clusters: int) -> KMeans:
    """
    Train K-Means clustering model.

    Args:
        X: Normalized feature matrix
        n_clusters: Number of clusters

    Returns:
        Trained KMeans model
    """
    logger.info(f"Training K-Means with K={n_clusters}...")

    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=20,  # More initializations for stability
        max_iter=300
    )

    kmeans.fit(X)

    # Evaluate
    silhouette_avg = silhouette_score(X, kmeans.labels_)
    davies_bouldin = davies_bouldin_score(X, kmeans.labels_)

    logger.info(f"✓ Model trained successfully")
    logger.info(f"  Silhouette Score: {silhouette_avg:.3f} (higher is better)")
    logger.info(f"  Davies-Bouldin Index: {davies_bouldin:.3f} (lower is better)")

    return kmeans


def interpret_clusters(
    df: pd.DataFrame,
    labels: np.ndarray
) -> Dict[int, Dict]:
    """
    Interpret cluster characteristics.

    Args:
        df: Original driver features DataFrame
        labels: Cluster labels

    Returns:
        Dict mapping cluster ID to interpretation
    """
    logger.info("Interpreting clusters...")

    df_clustered = df.copy()
    df_clustered['cluster'] = labels

    cluster_profiles = {}

    for cluster_id in np.unique(labels):
        cluster_data = df_clustered[df_clustered['cluster'] == cluster_id]

        profile = {
            'count': len(cluster_data),
            'percentage': len(cluster_data) / len(df) * 100,
            'safety_score_avg': cluster_data['safety_score'].mean(),
            'efficiency_score_avg': cluster_data['efficiency_score'].mean(),
            'harsh_braking_avg': cluster_data['harsh_braking_per_100km_avg'].mean(),
            'fuel_consumption_avg': cluster_data['fuel_per_100km_avg'].mean(),
            'scania_support_score_avg': cluster_data['scania_driver_support_score_avg'].mean()
        }

        # Infer cluster name based on characteristics
        safety = profile['safety_score_avg']
        harsh_braking = profile['harsh_braking_avg']

        if safety > 80 and harsh_braking < 0.3:
            cluster_name = "Conservador"
        elif safety > 70:
            cluster_name = "Equilibrado"
        else:
            cluster_name = "Agresivo"

        profile['cluster_name'] = cluster_name

        cluster_profiles[cluster_id] = profile

        logger.info(f"  Cluster {cluster_id} ({cluster_name}): {len(cluster_data)} drivers ({profile['percentage']:.1f}%)")
        logger.info(f"    Safety Score: {profile['safety_score_avg']:.2f}")
        logger.info(f"    Harsh Braking: {profile['harsh_braking_avg']:.3f}/100km")

    return cluster_profiles


def create_visualizations(
    X_scaled: np.ndarray,
    labels: np.ndarray,
    kmeans: KMeans,
    optimal_k_results: Dict,
    output_dir: Path
):
    """
    Create and save clustering visualizations.

    Args:
        X_scaled: Normalized features
        labels: Cluster labels
        kmeans: Trained KMeans model
        optimal_k_results: Results from K optimization
        output_dir: Directory to save plots
    """
    logger.info("Creating visualizations...")

    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (12, 8)

    # 1. Elbow Method
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(optimal_k_results['k_range'], optimal_k_results['inertias'], 'bo-')
    ax1.set_xlabel('Number of Clusters (K)')
    ax1.set_ylabel('Inertia')
    ax1.set_title('Elbow Method: Inertia vs K')
    ax1.grid(True)

    ax2.plot(optimal_k_results['k_range'], optimal_k_results['silhouette_scores'], 'ro-')
    ax2.set_xlabel('Number of Clusters (K)')
    ax2.set_ylabel('Silhouette Score')
    ax2.set_title('Silhouette Score vs K')
    ax2.grid(True)
    ax2.axhline(y=0.25, color='g', linestyle='--', label='Acceptable Threshold')
    ax2.legend()

    plt.tight_layout()
    plt.savefig(output_dir / 'optimal_k_analysis.png', dpi=150)
    logger.info(f"  ✓ Saved: optimal_k_analysis.png")
    plt.close()

    # 2. PCA Visualization
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)

    plt.figure(figsize=(10, 8))
    scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=labels, cmap='viridis', alpha=0.6, s=100)
    plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%} variance)')
    plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%} variance)')
    plt.title('Driver Clusters - PCA Visualization')
    plt.colorbar(scatter, label='Cluster')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'clusters_pca.png', dpi=150)
    logger.info(f"  ✓ Saved: clusters_pca.png")
    plt.close()

    # 3. Cluster Size Distribution
    unique, counts = np.unique(labels, return_counts=True)

    plt.figure(figsize=(8, 6))
    plt.bar(unique, counts, color='steelblue', alpha=0.7)
    plt.xlabel('Cluster ID')
    plt.ylabel('Number of Drivers')
    plt.title('Driver Distribution Across Clusters')
    plt.grid(axis='y', alpha=0.3)

    for i, count in enumerate(counts):
        plt.text(unique[i], count + 1, str(count), ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_dir / 'cluster_distribution.png', dpi=150)
    logger.info(f"  ✓ Saved: cluster_distribution.png")
    plt.close()

    logger.info("✓ All visualizations created")


def generate_clustering_report(
    cluster_profiles: Dict,
    kmeans: KMeans,
    optimal_k_results: Dict
) -> str:
    """
    Generate detailed clustering report.

    Args:
        cluster_profiles: Cluster interpretation results
        kmeans: Trained model
        optimal_k_results: K optimization results

    Returns:
        str: Formatted report
    """
    report = []
    report.append("=" * 80)
    report.append("DRIVER CLUSTERING REPORT")
    report.append("=" * 80)
    report.append("")

    # Model parameters
    report.append("MODEL PARAMETERS")
    report.append("-" * 80)
    report.append(f"Algorithm: K-Means")
    report.append(f"Number of clusters (K): {kmeans.n_clusters}")
    report.append(f"Random state: {kmeans.random_state}")
    report.append(f"Iterations: {kmeans.n_iter_}")
    report.append(f"Inertia: {kmeans.inertia_:.2f}")
    report.append("")

    # Cluster analysis
    report.append("CLUSTER PROFILES")
    report.append("-" * 80)

    for cluster_id, profile in cluster_profiles.items():
        report.append(f"\nCluster {cluster_id}: {profile['cluster_name']}")
        report.append(f"  Number of drivers: {profile['count']} ({profile['percentage']:.1f}%)")
        report.append(f"  Safety Score: {profile['safety_score_avg']:.2f}")
        report.append(f"  Efficiency Score: {profile['efficiency_score_avg']:.2f}")
        report.append(f"  Harsh Braking: {profile['harsh_braking_avg']:.3f}/100km")
        report.append(f"  Fuel Consumption: {profile['fuel_consumption_avg']:.2f} L/100km")
        report.append(f"  Scania Support Score: {profile['scania_support_score_avg']:.2f}")

    report.append("")
    report.append("=" * 80)
    report.append("Clustering completed successfully!")
    report.append("=" * 80)

    return "\n".join(report)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Train K-Means clustering model for driver segmentation'
    )
    parser.add_argument(
        '--input',
        type=str,
        help='Input driver features CSV',
        default=str(DATA_DIR / 'drivers_features.csv')
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output clustered drivers CSV',
        default=str(DATA_DIR / 'drivers_clustered.csv')
    )
    parser.add_argument(
        '--k',
        type=int,
        help='Number of clusters (if not specified, will auto-detect)',
        default=None
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("DRIVER CLUSTERING TRAINING")
    logger.info("=" * 80)
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")
    logger.info("")

    try:
        # Load data
        df = load_driver_features(Path(args.input))

        # Prepare data
        X_scaled, scaler = prepare_clustering_data(df)

        # Find optimal K (if not specified)
        if args.k is None:
            optimal_k_results = find_optimal_k(X_scaled)
            k = optimal_k_results['optimal_k']
        else:
            k = args.k
            optimal_k_results = None

        logger.info(f"Using K={k} clusters")
        logger.info("")

        # Train model
        kmeans = train_kmeans(X_scaled, k)

        # Get cluster labels
        labels = kmeans.labels_

        # Interpret clusters
        cluster_profiles = interpret_clusters(df, labels)

        # Add cluster info to dataframe
        df_clustered = df.copy()
        df_clustered['cluster'] = labels
        df_clustered['cluster_name'] = df_clustered['cluster'].map(
            {cid: profile['cluster_name'] for cid, profile in cluster_profiles.items()}
        )

        # Save clustered data
        df_clustered.to_csv(args.output, index=False)
        logger.info("")
        logger.info(f"✓ Saved clustered drivers to: {args.output}")

        # Save model and scaler
        model_path = MODELS_DIR / 'driver_clustering_model.pkl'
        with open(model_path, 'wb') as f:
            pickle.dump({'kmeans': kmeans, 'scaler': scaler, 'features': CLUSTERING_FEATURES}, f)
        logger.info(f"✓ Saved model to: {model_path}")

        # Create visualizations
        if optimal_k_results:
            create_visualizations(X_scaled, labels, kmeans, optimal_k_results, OUTPUTS_DIR)

        # Generate report
        report = generate_clustering_report(cluster_profiles, kmeans, optimal_k_results or {})
        report_path = OUTPUTS_DIR / 'clustering_report.txt'

        with open(report_path, 'w') as f:
            f.write(report)

        logger.info(f"✓ Saved clustering report to: {report_path}")
        logger.info("")
        print(report)

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"CLUSTERING FAILED: {e}")
        logger.error("=" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
