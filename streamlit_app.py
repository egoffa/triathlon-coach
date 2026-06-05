"""Streamlit interface for Triathlon Coach AI"""
import streamlit as st
import logging
from datetime import datetime, timedelta
from typing import Optional
import redis
import redis.exceptions

from src.utils.config import get_settings
from src.utils.logger import setup_logging
from src.llm.ollama_handler import OllamaHandler
from src.data.strava_client import StravaClient
from src.agents.coach_agent import CoachAgent

# Configure page
st.set_page_config(
    page_title="Triathlon Coach AI",
    page_icon="🏊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Setup logging
settings = get_settings()
logger = setup_logging(settings.log_level, settings.log_file)

# Initialize session state
if "strava_client" not in st.session_state:
    st.session_state.strava_client = None
if "ollama_handler" not in st.session_state:
    st.session_state.ollama_handler = None
if "redis_client" not in st.session_state:
    st.session_state.redis_client = None
if "coach_agent" not in st.session_state:
    st.session_state.coach_agent = None
if "athlete_data" not in st.session_state:
    st.session_state.athlete_data = None


@st.cache_resource
def init_services():
    """Initialize all services"""
    results = {
        "strava": False,
        "ollama": False,
        "redis": False,
        "errors": []
    }
    
    # Initialize Strava Client
    if settings.strava_client_id and settings.strava_client_secret and settings.strava_refresh_token:
        try:
            st.session_state.strava_client = StravaClient(
                client_id=settings.strava_client_id,
                client_secret=settings.strava_client_secret,
                refresh_token=settings.strava_refresh_token
            )
            results["strava"] = True
            logger.info("✓ Strava initialized")
        except Exception as e:
            results["strava"] = False
            results["errors"].append(f"Strava error: {str(e)}")
            logger.error(f"Strava init error: {e}")
    else:
        results["errors"].append("Strava credentials not configured in .env")
    
    # Initialize Ollama Handler
    try:
        st.session_state.ollama_handler = OllamaHandler(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout=settings.ollama_timeout
        )
        if st.session_state.ollama_handler.health_check():
            results["ollama"] = True
            logger.info("✓ Ollama initialized")
        else:
            results["ollama"] = False
            results["errors"].append("Ollama not responding")
    except Exception as e:
        results["ollama"] = False
        results["errors"].append(f"Ollama error: {str(e)}")
        logger.error(f"Ollama init error: {e}")
    
    # Initialize Redis Client
    try:
        st.session_state.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        st.session_state.redis_client.ping()
        results["redis"] = True
        logger.info("✓ Redis initialized")
    except Exception as e:
        st.session_state.redis_client = None
        results["redis"] = False
        logger.warning(f"Redis connection failed: {e}")
    
    # Initialize Coach Agent
    try:
        st.session_state.coach_agent = CoachAgent()
        logger.info("✓ Coach agent initialized")
    except Exception as e:
        logger.error(f"Coach agent init error: {e}")
    
    return results


def display_header():
    """Display app header"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🏊 Triathlon Coach AI")
        st.markdown("*AI-powered triathlon coaching with local LLMs*")
    with col2:
        st.metric("Model", settings.ollama_model)


def display_health_status(health_results):
    """Display service health status"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status = "✅ OK" if health_results["strava"] else "❌ Failed"
        st.metric("Strava", status)
    
    with col2:
        status = "✅ OK" if health_results["ollama"] else "❌ Failed"
        st.metric("Ollama", status)
    
    with col3:
        status = "✅ OK" if health_results["redis"] else "⚠️ Offline"
        st.metric("Redis", status)
    
    with col4:
        status = "✅ Ready" if health_results["strava"] and health_results["ollama"] else "❌ Error"
        st.metric("Overall", status)
    
    # Display errors if any
    if health_results["errors"]:
        with st.expander("⚠️ Issues"):
            for error in health_results["errors"]:
                st.error(error)


def fetch_activities(days: int, limit: int):
    """Fetch activities from Strava"""
    if not st.session_state.strava_client:
        st.error("Strava client not initialized")
        return None
    
    try:
        with st.spinner(f"Fetching activities from last {days} days..."):
            activities = st.session_state.strava_client.get_activities(
                limit=limit,
                days=days
            )
        return activities
    except Exception as e:
        st.error(f"Error fetching activities: {e}")
        logger.error(f"Error fetching activities: {e}")
        return None


def analyze_activities(activities):
    """Analyze activities with coach agent"""
    if not st.session_state.coach_agent:
        st.error("Coach agent not initialized")
        return None
    
    try:
        with st.spinner("Analyzing activities..."):
            analysis = st.session_state.coach_agent.execute(activities)
        return analysis
    except Exception as e:
        st.error(f"Error analyzing activities: {e}")
        logger.error(f"Error analyzing activities: {e}")
        return None


def get_ai_insights(activities):
    """Get AI insights from Ollama"""
    if not st.session_state.ollama_handler:
        st.error("Ollama not initialized")
        return None
    
    try:
        with st.spinner("Generating AI insights..."):
            # Prepare activity summary
            activities_summary = "\n".join([
                f"- {a.name} ({a.type}): {a.distance/1000:.1f}km, {a.duration//60}min"
                for a in activities
            ])
            
            system_prompt = """You are an expert triathlon coach. Analyze training and provide coaching insights."""
            
            prompt = f"""Analyze these recent triathlon training activities:

{activities_summary}

Provide a brief coaching analysis with 2-3 key recommendations. Be concise and actionable.
Respond in plain text, no JSON needed."""
            
            response = st.session_state.ollama_handler.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=500
            )
        return response
    except Exception as e:
        st.error(f"Error generating insights: {e}")
        logger.error(f"Error generating insights: {e}")
        return None


def main():
    """Main Streamlit app"""
    # Display header
    display_header()
    
    # Initialize services
    health_results = init_services()
    
    # Display health status
    st.markdown("---")
    display_health_status(health_results)
    st.markdown("---")
    
    # Check if essential services are available
    if not (health_results["strava"] and health_results["ollama"]):
        st.error("⚠️ Essential services not available. Please check .env configuration and try again.")
        st.info("""
        To fix:
        1. Ensure Strava credentials are in .env
        2. Make sure Ollama is running: `docker-compose logs ollama`
        3. Check that docker-compose up completed successfully
        """)
        return
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Fetch configuration
        days_back = st.slider(
            "Days to analyze",
            min_value=1,
            max_value=90,
            value=7,
            step=1
        )
        
        limit = st.slider(
            "Number of activities",
            min_value=5,
            max_value=50,
            value=10,
            step=5
        )
        
        # Fixed: Use index instead of value
        analysis_options = ["Coach Analysis", "AI Insights", "Both"]
        analysis_type = st.radio(
            "Analysis type",
            options=analysis_options,
            index=2  # Default to "Both" (index 2)
        )
        
        st.markdown("---")
        st.markdown("### 📊 System Info")
        st.write(f"**Model**: {settings.ollama_model}")
        st.write(f"**Environment**: {settings.environment}")
        st.write(f"**Verbose**: {settings.crew_ai_verbose}")
    
    # Main content
    st.header("📊 Training Analysis")
    
    # Fetch activities button
    if st.button("🔄 Fetch Activities", key="fetch_btn", use_container_width=True):
        activities = fetch_activities(days_back, limit)
        st.session_state.activities = activities
    
    # Display activities if available
    if "activities" in st.session_state and st.session_state.activities:
        activities = st.session_state.activities
        
        # Activities overview
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Activities", len(activities))
        with col2:
            total_km = sum(a.distance for a in activities) / 1000
            st.metric("Total Distance", f"{total_km:.1f} km")
        with col3:
            total_hours = sum(a.duration for a in activities) / 3600
            st.metric("Total Time", f"{total_hours:.1f} h")
        
        # Display activity list
        with st.expander("📋 Recent Activities", expanded=True):
            for activity in activities[:5]:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{activity.name}** ({activity.type})")
                with col2:
                    st.write(f"{activity.distance/1000:.1f}km")
                with col3:
                    st.write(f"{activity.duration//60}m")
        
        st.markdown("---")
        
        # Coach Analysis
        if analysis_type in ["Coach Analysis", "Both"]:
            st.header("🏆 Coach Analysis")
            
            if st.button("Analyze with Coach Agent", key="coach_btn", use_container_width=True):
                analysis = analyze_activities(activities)
                
                if analysis:
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.subheader("Analysis")
                        st.info(analysis.analysis)
                    
                    with col2:
                        st.subheader("Focus Areas")
                        for area in analysis.focus_areas:
                            st.write(f"• {area}")
                    
                    st.subheader("Recommendations")
                    for i, rec in enumerate(analysis.recommendations, 1):
                        st.write(f"{i}. {rec}")
                    
                    st.subheader("Next Workouts")
                    for workout in analysis.next_workout_suggestions:
                        st.write(f"• {workout}")
                    
                    if analysis.warnings:
                        st.warning("⚠️ Warnings: " + ", ".join(analysis.warnings))
        
        # AI Insights
        if analysis_type in ["AI Insights", "Both"]:
            st.markdown("---")
            st.header("🤖 AI Insights")
            
            if st.button("Generate AI Insights", key="ai_btn", use_container_width=True):
                insights = get_ai_insights(activities)
                
                if insights:
                    st.markdown(insights)
    
    else:
        st.info("👆 Click 'Fetch Activities' to get started!")
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.caption("🏊 Triathlon Coach AI v1.0")
    with col2:
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with col3:
        st.caption("Powered by Ollama & FastAPI")


if __name__ == "__main__":
    main()