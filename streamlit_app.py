"""Streamlit interface for Triathlon Coach AI - Standalone Multi-Agent System"""
import streamlit as st
import logging
from datetime import datetime
import redis
import redis.exceptions

from src.utils.config import get_settings
from src.utils.logger import setup_logging
from src.llm.ollama_handler import OllamaHandler
from src.data.strava_client import StravaClient
from src.agents.standalone_crew import TriathlonCoachCrew

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
if "coaching_crew" not in st.session_state:
    st.session_state.coaching_crew = None


@st.cache_resource
def init_services():
    """Initialize all services"""
    results = {
        "strava": False,
        "ollama": False,
        "redis": False,
        "crew": False,
        "errors": []
    }
    
    # Initialize Strava Client
    if settings.strava_client_id and settings.strava_client_secret and settings.strava_refresh_token:
        try:
            st.session_state.strava_client = StravaClient(
                client_id=settings.strava_client_id,
                client_secret=settings.strava_client_secret,
                refresh_token=settings.strava_refresh_token,
                access_token=settings.strava_access_token
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
    except redis.exceptions.ConnectionError:
        st.session_state.redis_client = None
        results["redis"] = False
        logger.warning("Redis connection failed (caching disabled)")
    except Exception as e:
        st.session_state.redis_client = None
        results["redis"] = False
        logger.error(f"Redis initialization failed: {e}")
    
    # Initialize Coaching Crew
    if results["ollama"]:
        try:
            st.session_state.coaching_crew = TriathlonCoachCrew(st.session_state.ollama_handler)
            results["crew"] = True
            logger.info("✓ Coaching crew initialized (3 agents - standalone)")
        except Exception as e:
            logger.error(f"Coaching crew init error: {e}")
            results["errors"].append(f"Crew error: {str(e)}")
    
    return results


def display_header():
    """Display app header"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🏊 Triathlon Coach AI")
        st.markdown("*AI-powered triathlon coaching with 3 concurrent agents*")
    with col2:
        st.metric("Model", settings.ollama_model)


def display_health_status(health_results):
    """Display service health status"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
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
        status = "✅ OK" if health_results["crew"] else "❌ Failed"
        st.metric("Crew", status)
    
    with col5:
        all_ok = health_results["strava"] and health_results["ollama"] and health_results["crew"]
        status = "✅ Ready" if all_ok else "❌ Error"
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
        with st.spinner(f"🔄 Fetching activities from last {days} days..."):
            activities = st.session_state.strava_client.get_activities(
                limit=limit,
                days=days
            )
        return activities
    except Exception as e:
        st.error(f"Error fetching activities: {e}")
        logger.error(f"Error fetching activities: {e}")
        return None


def run_crew_analysis(activities, goal: str = "olympic"):
    """Run coaching crew analysis"""
    if not st.session_state.coaching_crew:
        st.error("Coaching crew not initialized")
        return None
    
    try:
        with st.spinner("🧠 Running concurrent crew analysis (Coach + Analytics + Planning)..."):
            analysis = st.session_state.coaching_crew.analyze_activities(
                activities=activities,
                goal=goal
            )
        return analysis
    except Exception as e:
        st.error(f"Error in crew analysis: {e}")
        logger.error(f"Error in crew analysis: {e}")
        return None


def display_crew_status():
    """Display crew status in sidebar"""
    if st.session_state.coaching_crew:
        status = st.session_state.coaching_crew.get_crew_info()
        with st.expander("🤖 Crew Status"):
            st.write(f"**Crew:** {status.get('crew_name', 'Unknown')}")
            st.write(f"**Agents:** {status.get('agents', 0)}")
            st.write(f"**Mode:** {status.get('execution_mode', 'Unknown')}")
            
            agent_roles = status.get("agent_roles", [])
            if agent_roles:
                st.write("**Agent Roles:**")
                for i, role in enumerate(agent_roles, 1):
                    st.write(f"  {i}. {role}")


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
    if not (health_results["strava"] and health_results["crew"]):
        st.error("⚠️ Essential services not available. Please check .env configuration.")
        st.info("""
        To fix:
        1. Ensure Strava credentials are in .env
        2. Make sure Ollama is running: docker-compose up or ollama serve
        3. Restart the app
        """)
        return
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        display_crew_status()
        
        st.markdown("---")
        
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
        
        # Training goal
        goal = st.selectbox(
            "Training goal",
            ["sprint", "olympic", "halfim", "ironman"],
            index=1
        )
        
        st.markdown("---")
        st.markdown("### 📊 System Info")
        st.write(f"**Model:** {settings.ollama_model}")
        st.write(f"**Agents:** 3 (concurrent)")
        st.write(f"**Framework:** Standalone (no CrewAI)")
        st.write(f"**Environment:** {settings.environment}")
    
    # Main content
    st.header("📊 Multi-Agent Coaching Analysis")
    
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
        
        # Run crew analysis button
        if st.button("🧠 Run Crew Analysis (Coach + Analytics + Planning)", use_container_width=True):
            crew_analysis = run_crew_analysis(activities, goal)
            
            if crew_analysis and crew_analysis.get("status") == "success":
                st.session_state.crew_analysis = crew_analysis

                st.subheader("📊 Analytics")
                analytics_output = crew_analysis.get("analytics_analysis", "Pending...")
                st.info(analytics_output)
                
                # Status information
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Agents Executed", crew_analysis.get("agents_executed", 0))
                with col2:
                    st.metric("Activities Analyzed", crew_analysis.get("activities_analyzed", 0))
                with col3:
                    st.metric("Mode", crew_analysis.get("execution_mode", "Unknown").split("(")[0].strip())
                
                # Timestamp
                timestamp = crew_analysis.get("timestamp", "Unknown")
                st.caption(f"Analysis completed at: {timestamp}")
    
    else:
        st.info("👆 Click 'Fetch Activities' to get started!")
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.caption("🏊 Triathlon Coach AI v2.0")
    with col2:
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with col3:
        st.caption("3-Agent Standalone | Coach + Analytics + Planning")


if __name__ == "__main__":
    main()