"""Triathlon coach agent using CrewAI"""
import logging
from typing import List, Optional
from src.agents.base_agent import BaseAgent
from src.data.models import Activity, CoachingAnalysis

logger = logging.getLogger(__name__)


class CoachAgent(BaseAgent):
    """
    Main triathlon coaching agent
    
    This agent analyzes training activities and provides personalized
    coaching recommendations based on performance data.
    """
    
    def __init__(self):
        """Initialize coach agent"""
        super().__init__(
            role="Triathlon Coach",
            goal="Provide personalized training guidance and coaching insights based on athlete performance",
            backstory="""You are an experienced triathlon coach with 15+ years of coaching experience.
            You have trained athletes across all levels from beginner to professional.
            You specialize in periodization, training load management, and race preparation.
            Your coaching style is supportive yet data-driven, always backed by evidence."""
        )
    
    def analyze_activities(self, activities: List[Activity]) -> dict:
        """
        Analyze a list of activities
        
        Args:
            activities: List of Activity objects
        
        Returns:
            Analysis summary
        """
        if not activities:
            return {
                "total_activities": 0,
                "summary": "No activities to analyze"
            }
        
        # Calculate basic metrics
        total_distance = sum(a.distance for a in activities)
        total_duration = sum(a.duration for a in activities)
        avg_hr = sum(a.avg_heart_rate or 0 for a in activities if a.avg_heart_rate) / len([a for a in activities if a.avg_heart_rate]) if any(a.avg_heart_rate for a in activities) else 0
        
        # Group by activity type
        by_type = {}
        for activity in activities:
            if activity.type not in by_type:
                by_type[activity.type] = []
            by_type[activity.type].append(activity)
        
        return {
            "total_activities": len(activities),
            "total_distance": total_distance,
            "total_duration": total_duration,
            "average_hr": avg_hr,
            "by_type": {
                activity_type: {
                    "count": len(acts),
                    "distance": sum(a.distance for a in acts),
                    "duration": sum(a.duration for a in acts)
                }
                for activity_type, acts in by_type.items()
            }
        }
    
    def get_coaching_recommendation(self, analysis: dict) -> str:
        """
        Generate coaching recommendation based on analysis
        
        Args:
            analysis: Activity analysis dict
        
        Returns:
            Coaching recommendation string
        """
        activities_count = analysis.get("total_activities", 0)
        
        if activities_count == 0:
            return "You haven't logged any activities yet. Start with 3-4 sessions per week to build your fitness foundation."
        
        by_type = analysis.get("by_type", {})
        
        # Check balance across disciplines
        swim_count = len(by_type.get("swim", []))
        bike_count = len(by_type.get("bike", []))
        run_count = len(by_type.get("run", []))
        
        recommendations = []
        
        # Check discipline balance
        if swim_count == 0:
            recommendations.append("You're missing swimming workouts. Add 2-3 swim sessions per week.")
        elif swim_count < 2:
            recommendations.append("Increase swimming frequency to at least 2 sessions per week.")
        
        if bike_count == 0:
            recommendations.append("Add cycling to your training routine. 2-3 sessions per week is ideal.")
        elif bike_count < 2:
            recommendations.append("Increase cycling frequency to at least 2 sessions per week.")
        
        if run_count == 0:
            recommendations.append("You're missing running workouts. Add 2-3 run sessions per week.")
        elif run_count < 2:
            recommendations.append("Increase running frequency to at least 2 sessions per week.")
        
        # Check training variety
        if not recommendations:
            recommendations.append("Your discipline balance looks good! Focus on intensity variation.")
            recommendations.append("Add one high-intensity session per discipline per week.")
        
        return " ".join(recommendations)
    
    def execute(self, activities: List[Activity]) -> CoachingAnalysis:
        """
        Execute coach agent analysis
        
        Args:
            activities: List of activities to analyze
        
        Returns:
            CoachingAnalysis object
        """
        try:
            # Analyze activities
            analysis = self.analyze_activities(activities)
            
            # Generate recommendations
            recommendation = self.get_coaching_recommendation(analysis)
            
            # Identify focus areas
            focus_areas = []
            by_type = analysis.get("by_type", {})
            
            if not by_type.get("swim"):
                focus_areas.append("Swimming technique and endurance")
            if not by_type.get("bike"):
                focus_areas.append("Cycling power and aerodynamics")
            if not by_type.get("run"):
                focus_areas.append("Running economy and speed")
            
            # Generate next workout suggestions
            next_suggestions = []
            if not any(a.type == "swim" for a in activities[-3:] if len(activities) >= 3):
                next_suggestions.append("Swim session: 1500m progressive main set")
            if not any(a.type == "bike" for a in activities[-3:] if len(activities) >= 3):
                next_suggestions.append("Bike session: 60min with 4x3min at tempo")
            if not any(a.type == "run" for a in activities[-3:] if len(activities) >= 3):
                next_suggestions.append("Run session: 30min easy + 6x400m at 5K pace")
            
            if not next_suggestions:
                next_suggestions = [
                    "Long swim: 2000m endurance building",
                    "Long bike: 90min steady state",
                    "Long run: 60min easy pace"
                ]
            
            coaching_response = CoachingAnalysis(
                analysis=recommendation,
                recommendations=[recommendation],
                focus_areas=focus_areas or ["Overall fitness building"],
                next_workout_suggestions=next_suggestions,
                warnings=[]
            )
            
            # Store in memory
            self.add_to_memory({
                "type": "analysis",
                "input_count": len(activities),
                "output": coaching_response.dict()
            })
            
            logger.info(f"✓ Coach agent analyzed {len(activities)} activities")
            return coaching_response
            
        except Exception as e:
            logger.error(f"Error in coach agent execution: {e}")
            raise
