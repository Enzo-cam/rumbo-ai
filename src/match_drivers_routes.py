"""
Driver-Route Matching Optimization
Uses linear programming to optimally assign drivers to routes
"""

import pandas as pd
import numpy as np
from pulp import *
from pathlib import Path

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)


def calculate_compatibility_matrix(drivers_df, routes_df):
    """
    Calculate compatibility score between each driver-route pair
    
    Compatibility considers:
    - Score matching (better drivers for harder routes)
    - Kilometer balancing (prefer drivers with lower km to balance workload)
    """
    print("Calculating compatibility matrix...")
    
    n_drivers = len(drivers_df)
    n_routes = len(routes_df)
    
    # Create compatibility matrix
    compatibility = np.zeros((n_drivers, n_routes))
    
    for i, driver in drivers_df.iterrows():
        for j, route in routes_df.iterrows():
            # Base compatibility: how well driver score matches route requirements
            score_diff = abs(driver['driver_score_adjusted'] - route['route_score_final'])
            score_compatibility = 100 - score_diff  # Higher when scores are close
            
            # Bonus for high-skill drivers on demanding routes
            if driver['driver_score_adjusted'] >= route['route_score_final']:
                skill_bonus = 10
            else:
                skill_bonus = -20  # Penalty for under-qualified drivers
            
            # Kilometer balance factor (prefer drivers with lower km for workload balance)
            km_factor = -driver['km_balance'] / 1000  # Normalize
            
            # Safety matching for dangerous routes
            if route['peligrosity_score'] > 70:
                safety_bonus = driver['safety_score'] * 0.2
            else:
                safety_bonus = 0
            
            # Calculate total compatibility
            compatibility[i, j] = score_compatibility + skill_bonus + km_factor + safety_bonus
    
    print(f"  Compatibility range: [{compatibility.min():.2f}, {compatibility.max():.2f}]")
    
    return compatibility


def solve_matching_problem(drivers_df, routes_df, compatibility_matrix):
    """
    Solve the driver-route assignment problem using linear programming
    
    Objective: Maximize total compatibility
    Constraints:
    - Each route gets exactly one driver
    - Each driver gets at most one route (some drivers may not be assigned)
    """
    print("Solving matching optimization problem...")
    
    n_drivers = len(drivers_df)
    n_routes = len(routes_df)
    
    # Create the problem
    prob = LpProblem("Driver_Route_Matching", LpMaximize)
    
    # Decision variables: x[i,j] = 1 if driver i is assigned to route j
    x = {}
    for i in range(n_drivers):
        for j in range(n_routes):
            x[i, j] = LpVariable(f"x_{i}_{j}", cat='Binary')
    
    # Objective function: maximize total compatibility
    prob += lpSum([compatibility_matrix[i, j] * x[i, j] 
                   for i in range(n_drivers) 
                   for j in range(n_routes)])
    
    # Constraint 1: Each route must be assigned to exactly one driver
    for j in range(n_routes):
        prob += lpSum([x[i, j] for i in range(n_drivers)]) == 1, f"Route_{j}_assigned"
    
    # Constraint 2: Each driver can be assigned to at most one route
    for i in range(n_drivers):
        prob += lpSum([x[i, j] for j in range(n_routes)]) <= 1, f"Driver_{i}_max_one"
    
    # Solve the problem
    print("  Running optimization solver...")
    prob.solve(PULP_CBC_CMD(msg=0))  # msg=0 suppresses solver output
    
    # Check solution status
    status = LpStatus[prob.status]
    print(f"  Solution status: {status}")
    
    if status != 'Optimal':
        print("  Warning: Optimal solution not found!")
        return None
    
    # Extract solution
    assignments = []
    for i in range(n_drivers):
        for j in range(n_routes):
            if x[i, j].varValue == 1:
                assignments.append({
                    'driver_idx': i,
                    'route_idx': j,
                    'compatibility': compatibility_matrix[i, j]
                })
    
    print(f"  Total assignments: {len(assignments)}")
    print(f"  Unassigned drivers: {n_drivers - len(assignments)}")
    print(f"  Total compatibility score: {value(prob.objective):.2f}")
    
    return assignments


def create_assignment_dataframe(assignments, drivers_df, routes_df, compatibility_matrix):
    """
    Create a detailed assignment DataFrame with all relevant information
    """
    print("Creating assignment report...")
    
    assignment_data = []
    
    for assignment in assignments:
        driver_idx = assignment['driver_idx']
        route_idx = assignment['route_idx']
        
        driver = drivers_df.iloc[driver_idx]
        route = routes_df.iloc[route_idx]
        
        assignment_data.append({
            'driver_id': driver['driver_id'],
            'route_id': route['route_id'],
            'driver_score': driver['driver_score_adjusted'],
            'route_score': route['route_score_final'],
            'match_score': compatibility_matrix[driver_idx, route_idx],
            'score_difference': driver['driver_score_adjusted'] - route['route_score_final'],
            'km_balance': driver['km_balance'],
            'driver_safety': driver['safety_score'],
            'driver_efficiency': driver['efficiency_score'],
            'route_difficulty': route['difficulty_tier'],
            'route_distance_km': route['total_distance_km'],
            'route_peligrosity': route['peligrosity_score']
        })
    
    assignment_df = pd.DataFrame(assignment_data)
    
    # Sort by match score (best matches first)
    assignment_df = assignment_df.sort_values('match_score', ascending=False)
    
    return assignment_df


def generate_matching_report(assignment_df, drivers_df, routes_df):
    """
    Generate a comprehensive matching report
    """
    report = []
    report.append("=" * 80)
    report.append("DRIVER-ROUTE MATCHING REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Overall statistics
    report.append("MATCHING STATISTICS")
    report.append("-" * 80)
    report.append(f"Total drivers available: {len(drivers_df)}")
    report.append(f"Total routes to assign: {len(routes_df)}")
    report.append(f"Successful assignments: {len(assignment_df)}")
    report.append(f"Unassigned drivers: {len(drivers_df) - len(assignment_df)}")
    report.append("")
    
    report.append("Match Quality Metrics:")
    report.append(f"  Average match score: {assignment_df['match_score'].mean():.2f}")
    report.append(f"  Average score difference: {assignment_df['score_difference'].mean():.2f}")
    report.append(f"  Std score difference: {assignment_df['score_difference'].std():.2f}")
    report.append("")
    
    # Score matching analysis
    over_qualified = (assignment_df['score_difference'] > 10).sum()
    well_matched = ((assignment_df['score_difference'] >= -10) & 
                    (assignment_df['score_difference'] <= 10)).sum()
    under_qualified = (assignment_df['score_difference'] < -10).sum()
    
    report.append("Driver-Route Fit Analysis:")
    report.append(f"  Over-qualified drivers: {over_qualified} ({over_qualified/len(assignment_df)*100:.1f}%)")
    report.append(f"  Well-matched: {well_matched} ({well_matched/len(assignment_df)*100:.1f}%)")
    report.append(f"  Under-qualified: {under_qualified} ({under_qualified/len(assignment_df)*100:.1f}%)")
    report.append("")
    
    # Difficulty distribution
    report.append("Assignments by Route Difficulty:")
    for tier in ['Easy', 'Medium', 'Hard', 'Expert']:
        count = (assignment_df['route_difficulty'] == tier).sum()
        if count > 0:
            avg_driver_score = assignment_df[assignment_df['route_difficulty'] == tier]['driver_score'].mean()
            report.append(f"  {tier}: {count} assignments (avg driver score: {avg_driver_score:.2f})")
    report.append("")
    
    # Top 10 best matches
    report.append("TOP 10 BEST MATCHES")
    report.append("-" * 80)
    top_matches = assignment_df.head(10)
    for idx, match in top_matches.iterrows():
        report.append(f"{match['driver_id']} → {match['route_id']}")
        report.append(f"  Match Score: {match['match_score']:.2f}")
        report.append(f"  Driver: {match['driver_score']:.2f} (Safety: {match['driver_safety']:.2f}, Efficiency: {match['driver_efficiency']:.2f})")
        report.append(f"  Route: {match['route_score']:.2f} ({match['route_difficulty']}, {match['route_distance_km']:.0f} km)")
        report.append(f"  Fit: {'+' if match['score_difference'] > 0 else ''}{match['score_difference']:.2f} points")
        report.append("")
    
    # Unassigned drivers analysis
    assigned_driver_ids = set(assignment_df['driver_id'])
    unassigned_drivers = drivers_df[~drivers_df['driver_id'].isin(assigned_driver_ids)]
    
    if len(unassigned_drivers) > 0:
        report.append("")
        report.append("UNASSIGNED DRIVERS ANALYSIS")
        report.append("-" * 80)
        report.append(f"Total unassigned: {len(unassigned_drivers)}")
        report.append(f"Average score: {unassigned_drivers['driver_score_adjusted'].mean():.2f}")
        report.append(f"Score range: [{unassigned_drivers['driver_score_adjusted'].min():.2f}, "
                     f"{unassigned_drivers['driver_score_adjusted'].max():.2f}]")
        report.append("")
    
    report.append("=" * 80)
    report.append("Matching completed successfully!")
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    """
    Main execution function
    """
    print("Starting driver-route matching optimization...")
    print("=" * 80)
    
    # Load scored datasets
    drivers_df = pd.read_csv(DATA_DIR / "scored_drivers.csv")
    routes_df = pd.read_csv(DATA_DIR / "scored_routes.csv")
    
    print(f"Loaded {len(drivers_df)} drivers and {len(routes_df)} routes")
    print("")
    
    # Calculate compatibility matrix
    compatibility_matrix = calculate_compatibility_matrix(drivers_df, routes_df)
    
    # Solve matching problem
    assignments = solve_matching_problem(drivers_df, routes_df, compatibility_matrix)
    
    if assignments is None:
        print("ERROR: Could not find optimal solution!")
        return
    
    # Create assignment DataFrame
    assignment_df = create_assignment_dataframe(assignments, drivers_df, routes_df, compatibility_matrix)
    
    # Save assignments
    output_path = OUTPUTS_DIR / "driver_route_assignment.csv"
    assignment_df.to_csv(output_path, index=False)
    print("")
    print(f"✓ Saved assignments to: {output_path}")
    
    # Generate and save report
    report = generate_matching_report(assignment_df, drivers_df, routes_df)
    report_path = OUTPUTS_DIR / "matching_report.txt"
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"✓ Saved matching report to: {report_path}")
    
    print("")
    print(report)


if __name__ == "__main__":
    main()
