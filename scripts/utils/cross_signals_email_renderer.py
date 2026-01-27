#!/usr/bin/env python3
"""
Cross Signals Email Renderer - Safe Plug-in

Renders Cross Signals insights as an optional email block.
If outputs/cross_signals.json doesn't exist or has 0 insights, returns empty string.

Usage:
    from scripts.utils.cross_signals_email_renderer import render_cross_signals_block

    cross_signals_block = render_cross_signals_block()
    if cross_signals_block:
        email_body += cross_signals_block
"""

import json
from pathlib import Path
from typing import Optional


def render_cross_signals_block(json_path: Optional[Path] = None) -> str:
    """
    Render Cross Signals block for email.

    Args:
        json_path: Path to cross_signals.json (default: outputs/cross_signals.json)

    Returns:
        Formatted email block or empty string if no data
    """
    if json_path is None:
        json_path = Path(__file__).parent.parent.parent / 'outputs' / 'cross_signals.json'

    # Check if file exists
    if not json_path.exists():
        return ""

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return ""

    # Check if there are insights
    insights = data.get('insights', [])
    if not insights:
        return ""

    # Render block
    block = "\n\n"
    block += "=" * 80 + "\n"
    block += "🔗 CROSS SIGNALS - Multi-Source Intelligence\n"
    block += "=" * 80 + "\n\n"

    # Metadata
    window = data.get('window', {})
    coverage = data.get('coverage', {})

    block += f"Analysis Window: {window.get('start_date', 'N/A')} to {window.get('end_date', 'N/A')}\n"
    block += f"Sources Used: {coverage.get('sources_used', 0)}\n"
    block += f"Insights Found: {coverage.get('total_insights', 0)}\n"
    block += f"Confidence Distribution: "
    conf_dist = coverage.get('confidence_distribution', {})
    block += f"HIGH={conf_dist.get('HIGH', 0)}, MEDIUM={conf_dist.get('MEDIUM', 0)}, LOW={conf_dist.get('LOW', 0)}\n"
    block += "\n"

    # Data quality warnings
    data_quality = data.get('data_quality', {})
    warnings = data_quality.get('warnings', [])
    if warnings:
        block += "⚠️  DATA QUALITY ALERTS:\n"
        for warning in warnings[:3]:  # Top 3 warnings
            severity = warning.get('severity', 'info').upper()
            message = warning.get('message', 'Unknown warning')
            block += f"   [{severity}] {message}\n"
        block += "\n"

    # Render insights (top N based on render_hints)
    render_hints = data.get('render_hints', {})
    max_items = render_hints.get('max_items_email', 5)

    for idx, insight in enumerate(insights[:max_items], 1):
        block += f"[{idx}] {insight['title']}\n"
        block += f"    Domain: {insight['domain']} | Confidence: {insight['confidence']}\n"
        block += f"    Regions: {', '.join(insight['regions'])}\n"

        # Event
        event = insight.get('event', {})
        block += f"    Event: {event.get('headline', 'N/A')[:100]}\n"

        # Reactions (count by source)
        reactions = insight.get('reactions', [])
        reaction_sources = {}
        for reaction in reactions:
            source = reaction.get('source_id', 'unknown')
            reaction_sources[source] = reaction_sources.get(source, 0) + 1

        block += f"    Reactions: {len(reactions)} signals from {len(reaction_sources)} sources\n"
        block += f"      Sources: {', '.join(reaction_sources.keys())}\n"

        # Top implication
        implications = insight.get('implications', [])
        if implications:
            top_impl = implications[0]
            block += f"    💡 {top_impl['category'].upper()}: {top_impl['text'][:120]}\n"

        # Recommended action (if urgent/high priority)
        actions = insight.get('recommended_actions', [])
        urgent_actions = [a for a in actions if a.get('priority') in ['urgent', 'high']]
        if urgent_actions:
            action = urgent_actions[0]
            block += f"    ⚡ ACTION: {action['action_type']} - {action['description'][:100]}\n"

        block += "\n"

    # Footer
    if len(insights) > max_items:
        block += f"... and {len(insights) - max_items} more insights in full JSON report.\n\n"

    block += "Full details: outputs/cross_signals.json\n"
    block += "=" * 80 + "\n"

    return block


def get_cross_signals_summary() -> dict:
    """
    Get summary stats for Cross Signals (for logging/monitoring).

    Returns:
        Dict with keys: exists, insights_count, observations_count, sources_used, has_warnings
    """
    json_path = Path(__file__).parent.parent.parent / 'outputs' / 'cross_signals.json'

    if not json_path.exists():
        return {
            'exists': False,
            'insights_count': 0,
            'observations_count': 0,
            'sources_used': 0,
            'has_warnings': False
        }

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        coverage = data.get('coverage', {})
        data_quality = data.get('data_quality', {})
        warnings = data_quality.get('warnings', [])

        return {
            'exists': True,
            'insights_count': coverage.get('total_insights', 0),
            'observations_count': coverage.get('total_observations', 0),
            'sources_used': coverage.get('sources_used', 0),
            'has_warnings': len(warnings) > 0
        }
    except (json.JSONDecodeError, IOError):
        return {
            'exists': True,
            'insights_count': 0,
            'observations_count': 0,
            'sources_used': 0,
            'has_warnings': True
        }


if __name__ == '__main__':
    # Test rendering
    print("Testing Cross Signals Email Renderer...")
    print()

    summary = get_cross_signals_summary()
    print(f"Summary: {summary}")
    print()

    block = render_cross_signals_block()
    if block:
        print("Rendered block:")
        print(block)
    else:
        print("No cross-signals data available for rendering.")
