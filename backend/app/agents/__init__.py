from .base import BaseAgent
from .planner import PlannerAgent
from .data_agent import DataAgent
from .risk_analyst import RiskAnalysisAgent
from .recommendation import RecommendationAgent
from .critic import CriticAgent

# Backwards compatibility aliases
WeatherAnalystAgent = DataAgent
ActivityPlannerAgent = RecommendationAgent
RiskAssessorAgent = RiskAnalysisAgent

__all__ = [
    "BaseAgent",
    "PlannerAgent",
    "DataAgent",
    "RiskAnalysisAgent",
    "RecommendationAgent",
    "CriticAgent",
    "WeatherAnalystAgent",
    "ActivityPlannerAgent",
    "RiskAssessorAgent",
]
