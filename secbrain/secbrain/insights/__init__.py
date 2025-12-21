"""Insights module for aggregating and analyzing SecBrain data."""

from secbrain.insights.aggregator import InsightsAggregator
from secbrain.insights.analyzer import InsightsAnalyzer
from secbrain.insights.reporter import InsightsReporter

__all__ = ["InsightsAggregator", "InsightsAnalyzer", "InsightsReporter"]
