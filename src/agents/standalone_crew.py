"""Standalone Triathlon Coach - Multi-Agent System (No CrewAI dependency)"""
import logging
from typing import List, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from src.data.models import Activity
from src.llm.ollama_handler import OllamaHandler

logger = logging.getLogger(__name__)


class CoachAgent:
    """Coach Agent - Provides personalized coaching insights"""
    
    def __init__(self, llm_handler: OllamaHandler):
        self.llm = llm_handler
        self.role = "Head Triathlon Coach"
    
    def execute(self, activities: List[Activity], goal: str) -> str:
        """Execute coaching analysis"""
        
        # Format activities for prompt
        activities_summary = self._format_activities(activities)
        
        prompt = f"""You are an expert triathlon coach with 20+ years experience.
        
Analyze these recent training activities and provide personalized coaching insights.

{activities_summary}

Training Goal: {goal}

Provide:
1. Assessment of training discipline balance (swim/bike/run ratio)
2. Are recovery periods adequate between hard efforts?
3. Is the training specific to their goal distance?
4. How well does it follow the 80/20 rule (80% easy, 20% hard)?
5. What is their current fitness trajectory?

Then provide 3-5 specific, actionable coaching recommendations.
Finally, suggest the next 3 workouts that would best benefit this athlete.

Be encouraging but honest about areas for improvement."""

        try:
            response = self.llm.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=1000
            )
            logger.info("✓ Coach analysis complete")
            return response
        except Exception as e:
            logger.error(f"Coach analysis error: {e}")
            raise
    
    def _format_activities(self, activities: List[Activity]) -> str:
        text = f"Total activities: {len(activities)}\n\n"
        for i, a in enumerate(activities[:10], 1):
            text += f"{i}. {a.name} ({a.type}): {a.distance/1000:.1f}km in {a.duration//60}min"
            if a.avg_heart_rate:
                text += f" (HR: {a.avg_heart_rate}bpm)"
            text += "\n"
        return text


class AnalyticsAgent:
    """Analytics Agent - Analyzes performance metrics and patterns"""
    
    def __init__(self, llm_handler: OllamaHandler):
        self.llm = llm_handler
        self.role = "Performance Analytics Specialist"
    
    def execute(self, activities: List[Activity]) -> str:
        """Execute analytics analysis"""
        
        # Calculate metrics
        metrics = self._calculate_metrics(activities)
        
        prompt = f"""You are a sports data analyst specializing in triathlon metrics.

Here is the athlete's training data analysis:

{metrics}

Based on this data, provide:
1. Key performance insights (3-4 specific observations)
2. Training load assessment
3. Intensity distribution analysis
4. Consistency and volume trends
5. 3-4 data-driven recommendations for improvement

Be objective and analytical. Use the numbers to support your recommendations."""

        try:
            response = self.llm.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=1000
            )
            logger.info("✓ Analytics complete")
            return response
        except Exception as e:
            logger.error(f"Analytics error: {e}")
            raise
    
    def _calculate_metrics(self, activities: List[Activity]) -> str:
        """Calculate key metrics"""
        
        text = "TRAINING METRICS:\n"
        text += f"  Total activities: {len(activities)}\n"
        
        # By type
        by_type = {}
        for a in activities:
            if a.type not in by_type:
                by_type[a.type] = {"count": 0, "distance": 0, "duration": 0}
            by_type[a.type]["count"] += 1
            by_type[a.type]["distance"] += a.distance / 1000
            by_type[a.type]["duration"] += a.duration / 3600
        
        text += "\n  By Discipline:\n"
        for dtype, data in by_type.items():
            text += f"    {dtype}: {data['count']} sessions, {data['distance']:.1f}km, {data['duration']:.1f}hrs\n"
        
        # Totals
        total_distance = sum(a.distance for a in activities) / 1000
        total_duration = sum(a.duration for a in activities) / 3600
        total_elevation = sum(a.elevation_gain or 0 for a in activities)
        
        text += f"\n  Total Volume: {total_distance:.1f}km, {total_duration:.1f}hrs\n"
        text += f"  Total Elevation: {total_elevation:.0f}m\n"
        
        # Intensity estimation
        easy_count = sum(1 for a in activities if not a.avg_heart_rate or a.avg_heart_rate < 140)
        hard_count = sum(1 for a in activities if a.avg_heart_rate and a.avg_heart_rate > 160)
        easy_pct = (easy_count / len(activities) * 100) if activities else 0
        hard_pct = (hard_count / len(activities) * 100) if activities else 0
        
        text += f"\n  Intensity Distribution:\n"
        text += f"    Easy efforts: ~{easy_pct:.0f}%\n"
        text += f"    Hard efforts: ~{hard_pct:.0f}%\n"
        
        return text


class PlanningAgent:
    """Planning Agent - Creates adaptive training plans"""
    
    def __init__(self, llm_handler: OllamaHandler):
        self.llm = llm_handler
        self.role = "Training Plan Developer"
    
    def execute(self, activities: List[Activity], goal: str) -> str:
        """Execute planning analysis"""
        
        fitness_level = self._assess_fitness(activities)
        
        prompt = f"""You are an expert in periodized training and race preparation.

Athlete Profile:
- Fitness Level: {fitness_level}
- Training Goal: {goal}
- Recent Volume: {sum(a.distance for a in activities)/1000:.0f}km in {sum(a.duration for a in activities)/3600:.1f}hrs
- Activity Count: {len(activities)}

Create a 12-week periodized training plan that includes:

1. TRAINING PHASES:
   - Base phase (aerobic development)
   - Build phase (volume and intensity)
   - Specific phase (race-specific work)
   - Taper and Peak (race preparation)

2. WEEKLY STRUCTURE:
   - Suggested swim, bike, run frequency
   - Easy/moderate/hard distribution (80/20 rule)
   - Recovery days

3. PROGRESSION STRATEGY:
   - How to gradually increase volume
   - When to add intensity
   - Recovery and deload weeks

4. NEXT STEPS:
   - 3-4 immediate action items for the next week
   - Key focus areas
   - Milestones to track

Make it realistic, sustainable, and specific to their {goal} goal."""

        try:
            response = self.llm.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=1200
            )
            logger.info("✓ Planning complete")
            return response
        except Exception as e:
            logger.error(f"Planning error: {e}")
            raise
    
    def _assess_fitness(self, activities: List[Activity]) -> str:
        """Assess fitness level"""
        
        if not activities:
            return "Beginner"
        
        # Estimate TSS
        tss = 0
        for a in activities:
            duration_min = a.duration / 60
            if a.avg_heart_rate and a.max_heart_rate:
                intensity = a.avg_heart_rate / a.max_heart_rate
            else:
                intensity = 0.75
            tss += duration_min * intensity
        
        if tss < 100:
            return "Beginner"
        elif tss < 200:
            return "Intermediate"
        elif tss < 350:
            return "Advanced"
        else:
            return "Elite"


class TriathlonCoachCrew:
    """Standalone Multi-Agent Triathlon Coaching System"""
    
    def __init__(self, llm_handler: OllamaHandler):
        """Initialize the coaching crew"""
        self.llm = llm_handler
        
        self.coach = CoachAgent(llm_handler)
        self.analytics = AnalyticsAgent(llm_handler)
        self.planning = PlanningAgent(llm_handler)
        
        logger.info("✓ Coaching crew initialized (3 agents)")
    
    def analyze_activities(
        self,
        activities: List[Activity],
        goal: str = "olympic"
    ) -> Dict[str, Any]:
        """Run concurrent analysis with all three agents"""
        
        if not activities:
            return {
                "status": "error",
                "message": "No activities provided"
            }
        
        logger.info(f"🏊 Crew analyzing {len(activities)} activities...")
        
        # Run agents concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            
            # Submit all tasks
            coach_future = executor.submit(self.coach.execute, activities, goal)
            analytics_future = executor.submit(self.analytics.execute, activities)
            planning_future = executor.submit(self.planning.execute, activities, goal)
            
            # Collect results
            coach_result = None
            analytics_result = None
            planning_result = None
            errors = []
            
            try:
                coach_result = coach_future.result(timeout=60)
                logger.info("✓ Coach agent complete")
            except Exception as e:
                logger.error(f"Coach failed: {e}")
                errors.append(f"Coach: {str(e)}")
            
            try:
                analytics_result = analytics_future.result(timeout=60)
                logger.info("✓ Analytics agent complete")
            except Exception as e:
                logger.error(f"Analytics failed: {e}")
                errors.append(f"Analytics: {str(e)}")
            
            try:
                planning_result = planning_future.result(timeout=60)
                logger.info("✓ Planning agent complete")
            except Exception as e:
                logger.error(f"Planning failed: {e}")
                errors.append(f"Planning: {str(e)}")
        
        # Synthesize results
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "activities_analyzed": len(activities),
            "goal": goal,
            "agents_executed": 3,
            "execution_mode": "concurrent",
            "coach_analysis": coach_result,
            "analytics_analysis": analytics_result,
            "planning_analysis": planning_result,
            "errors": errors
        }
    
    def get_crew_info(self) -> Dict[str, Any]:
        """Get crew information"""
        return {
            "crew_name": "Triathlon Coach AI",
            "agents": 3,
            "agent_roles": [
                "Head Triathlon Coach",
                "Performance Analytics Specialist",
                "Training Plan Developer"
            ],
            "execution_mode": "concurrent (ThreadPoolExecutor)",
            "status": "ready"
        }