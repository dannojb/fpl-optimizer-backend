"""
Team Optimization Service

Greedy optimization algorithm for transfer recommendations.
Port of frontend TypeScript optimizer to Python.
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def optimizeTeam(current_team: List[Dict], all_players: List[Dict]) -> Dict:
    """
    Greedy optimization algorithm for transfer recommendations.

    Evaluates potential player swaps within budget, formation, and team constraints.
    Returns top 3-5 recommendations sorted by improvement value.

    Args:
        current_team: User's current 15-player team
        all_players: Complete player database (~600 players)

    Returns:
        Dict with recommendations list and computation time
    """
    # Input validation
    if len(current_team) != 15:
        logger.warning(f'Current team must have exactly 15 players, got {len(current_team)}')
        return {'recommendations': [], 'computationTime': 0}

    # Calculate current team metrics
    current_cost = calculate_team_cost(current_team)
    available_budget = 1000 - current_cost

    # Find recommendations for each position
    recommendations = []

    for position in [1, 2, 3, 4]:
        position_recs = find_position_recommendations(
            current_team,
            all_players,
            position,
            available_budget
        )
        recommendations.extend(position_recs)

    # Apply constraints and filter
    valid_recommendations = [
        rec for rec in recommendations
        if validate_budget_constraint(current_team, rec)
        and validate_formation_constraint(rec)
        and validate_team_constraint(current_team, rec)
    ]

    # Deduplicate by playerOut (prevent same player being transferred out multiple times)
    deduped_recs = deduplicate_recommendations(valid_recommendations)

    # Sort by improvement and take top 5
    top_recommendations = sorted(
        deduped_recs,
        key=lambda x: calculate_improvement(x),
        reverse=True
    )[:5]

    logger.info(f'Optimization found {len(top_recommendations)} recommendations')

    return {
        'recommendations': top_recommendations,
        'computationTime': 0  # Will be calculated by router
    }


def calculate_team_cost(players: List[Dict]) -> int:
    """Calculate total cost of a team."""
    return sum(p['now_cost'] for p in players)


def find_position_recommendations(
    current_team: List[Dict],
    all_players: List[Dict],
    position: int,
    available_budget: int
) -> List[Dict]:
    """
    Find potential recommendations for a specific position.

    Args:
        current_team: Current team
        all_players: All available players
        position: Position (1=GK, 2=DEF, 3=MID, 4=FWD)
        available_budget: Available budget

    Returns:
        List of recommendation dictionaries
    """
    recommendations = []

    # Get current players in this position
    current_players_in_position = [p for p in current_team if p['position'] == position]

    # Get all candidate players (same position, not in current team)
    current_player_ids = {p['id'] for p in current_team}
    candidates = [p for p in all_players if p['position'] == position and p['id'] not in current_player_ids]

    # For each current player, find potential upgrades
    for current_player in current_players_in_position:
        # Find candidates that are upgrades
        upgrades = []

        for candidate in candidates:
            # Must have more points
            if candidate['total_points'] <= current_player['total_points']:
                continue

            # Must be affordable
            cost_diff = candidate['now_cost'] - current_player['now_cost']
            if cost_diff > available_budget:
                continue

            points_diff = candidate['total_points'] - current_player['total_points']

            # Calculate value score (points improvement per cost unit)
            if cost_diff == 0:
                value_score = points_diff * 1000  # Free upgrade gets huge bonus
            else:
                value_score = points_diff / abs(cost_diff)

            upgrades.append({
                'candidate': candidate,
                'value_score': value_score,
                'points_diff': points_diff,
                'cost_diff': cost_diff
            })

        # Sort by value score and take top 3
        upgrades.sort(key=lambda x: x['value_score'], reverse=True)
        top_upgrades = upgrades[:3]

        # Create recommendations
        for upgrade in top_upgrades:
            rationale = generate_rationale(
                current_player,
                upgrade['candidate'],
                upgrade['points_diff'],
                upgrade['cost_diff']
            )

            recommendations.append({
                'playerOut': current_player,
                'playerIn': upgrade['candidate'],
                'rationale': rationale,
                'cost_change': upgrade['cost_diff']
            })

    return recommendations


def validate_budget_constraint(current_team: List[Dict], rec: Dict) -> bool:
    """Validate budget constraint."""
    current_cost = calculate_team_cost(current_team)
    new_cost = current_cost - rec['playerOut']['now_cost'] + rec['playerIn']['now_cost']
    return new_cost <= 1000


def validate_formation_constraint(rec: Dict) -> bool:
    """Validate formation constraint (same position swap)."""
    return rec['playerOut']['position'] == rec['playerIn']['position']


def validate_team_constraint(current_team: List[Dict], rec: Dict) -> bool:
    """
    Validate max 3 players per team constraint.

    Simulates the transfer and checks if any team would have more than 3 players.
    """
    # Simulate the transfer
    new_team = [p for p in current_team if p['id'] != rec['playerOut']['id']]
    new_team.append(rec['playerIn'])

    # Count players by team
    team_counts = {}
    for player in new_team:
        team_name = player['team_name']
        team_counts[team_name] = team_counts.get(team_name, 0) + 1

    # Check if any team has more than 3 players
    return all(count <= 3 for count in team_counts.values())


def deduplicate_recommendations(recommendations: List[Dict]) -> List[Dict]:
    """Deduplicate recommendations (prevent same playerOut appearing twice)."""
    seen = set()
    deduped = []

    for rec in recommendations:
        player_out_id = rec['playerOut']['id']
        if player_out_id not in seen:
            seen.add(player_out_id)
            deduped.append(rec)

    return deduped


def calculate_improvement(rec: Dict) -> int:
    """Calculate improvement score for sorting."""
    return rec['playerIn']['total_points'] - rec['playerOut']['total_points']


def generate_rationale(
    player_out: Dict,
    player_in: Dict,
    points_diff: int,
    cost_diff: int
) -> str:
    """
    Generate plain English rationale for a transfer recommendation.

    Uses player comparison data (form, points, cost, PPG) to create
    concise, data-backed rationale.

    Priority: points > form > cost > PPG
    """
    form_diff = player_in['form'] - player_out['form']
    ppg_diff = player_in['points_per_game'] - player_out['points_per_game']

    # Strong combined factors: excellent points + form
    if points_diff > 50 and form_diff > 2:
        return f"Much better form, +{points_diff} points"

    if points_diff > 30 and form_diff > 1:
        return f"Better form, +{points_diff} points"

    # Budget-friendly + good performance
    if cost_diff < 0 and points_diff > 20:
        saved = abs(cost_diff / 10.0)
        return f"Great value, +{points_diff} pts, saves £{saved:.1f}m"

    if cost_diff < 0 and form_diff > 1.5:
        saved = abs(cost_diff / 10.0)
        return f"Budget-friendly, better form, -£{saved:.1f}m"

    # Points-focused (strongest signal)
    if points_diff > 50:
        return f"Much better season (+{points_diff} points)"

    if points_diff > 20:
        return f"Higher season total (+{points_diff} points)"

    if points_diff > 10:
        return f"Better performance (+{points_diff} points)"

    # Form-focused (recent performance)
    if form_diff > 2.5:
        return f"Excellent recent form (+{form_diff:.1f})"

    if form_diff > 1.5:
        return f"Better recent form (+{form_diff:.1f})"

    if form_diff > 0.5:
        return f"Improved form (+{form_diff:.1f})"

    # Points per game (consistency)
    if ppg_diff > 1.5 and points_diff > 5:
        return f"More consistent, +{ppg_diff:.1f} pts/game"

    # Cost-focused
    if cost_diff < 0:
        saved = abs(cost_diff / 10.0)
        return f"Budget option, frees up £{saved:.1f}m"

    if cost_diff == 0 and points_diff > 0:
        return f"Equal price, +{points_diff} points"

    if cost_diff > 0 and points_diff > 30:
        cost = cost_diff / 10.0
        return f"Premium upgrade, +£{cost:.1f}m for +{points_diff} pts"

    # Default fallback
    if points_diff > 0:
        return f"+{points_diff} points this season"

    return "Recommended upgrade"
