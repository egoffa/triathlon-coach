"""Main FastAPI application for Triathlon Coach AI"""
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import redis
import redis.exceptions

from src.utils.config import get_settings
from src.utils.logger import setup_logging
from src.llm.ollama_handler import OllamaHandler
from src.data.strava_client import StravaClient
from src.data.models import HealthResponse

# Setup logging
settings = get_settings()
logger = setup_logging(settings.log_level, settings.log_file)

# Global instances
strava_client = None
ollama_handler = None
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup/shutdown"""
    global strava_client, ollama_handler, redis_client
    
    # Startup
    logger.info("=" * 60)
    logger.info("🏊 Triathlon Coach AI - Starting Up")
    logger.info("=" * 60)
    
    # Initialize Strava Client
    if settings.strava_client_id and settings.strava_client_secret and settings.strava_refresh_token:
        try:
            strava_client = StravaClient(
                client_id=settings.strava_client_id,
                client_secret=settings.strava_client_secret,
                refresh_token=settings.strava_refresh_token
            )
            athlete = strava_client.get_athlete()
            logger.info(f"✓ Strava connected: {athlete.firstname} {athlete.lastname}")
        except Exception as e:
            logger.error(f"✗ Strava initialization failed: {e}")
            strava_client = None
    else:
        logger.warning("⚠ Strava credentials not configured")
    
    # Initialize Ollama Handler
    try:
        ollama_handler = OllamaHandler(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout=settings.ollama_timeout
        )
        if ollama_handler.health_check():
            models = ollama_handler.list_models()
            logger.info(f"✓ Ollama ready (model: {settings.ollama_model}, available: {len(models)} models)")
        else:
            logger.error("✗ Ollama not responding")
            ollama_handler = None
    except Exception as e:
        logger.error(f"✗ Ollama initialization failed: {e}")
        ollama_handler = None
    
    # Initialize Redis Client
    try:
        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        redis_client.ping()
        logger.info("✓ Redis connected")
    except redis.exceptions.ConnectionError as e:
        logger.warning(f"⚠ Redis connection failed (caching disabled): {e}")
        redis_client = None
    except Exception as e:
        logger.error(f"✗ Redis initialization failed: {e}")
        redis_client = None
    
    logger.info("=" * 60)
    logger.info("✓ Startup complete - Ready to serve requests")
    logger.info("=" * 60)
    
    yield  # Server is running
    
    # Shutdown
    logger.info("Shutting down...")
    logger.info("✓ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Triathlon Coach AI",
    description="AI-powered triathlon coaching system with local LLMs",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/", tags=["System"])
async def root():
    """Root endpoint"""
    return {
        "message": "Triathlon Coach AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["System"], response_model=HealthResponse)
async def health_check():
    """Check system health and service status"""
    try:
        strava_status = strava_client is not None and strava_client.is_authenticated()
    except:
        strava_status = False
    
    try:
        ollama_status = ollama_handler is not None and ollama_handler.health_check()
    except:
        ollama_status = False
    
    try:
        redis_status = redis_client is not None
        if redis_status:
            redis_client.ping()
    except:
        redis_status = False
    
    all_healthy = strava_status and ollama_status and redis_status
    status = "healthy" if all_healthy else "degraded" if (strava_status or ollama_status or redis_status) else "down"
    
    return HealthResponse(
        status=status,
        timestamp=datetime.now(),
        services={
            "strava": strava_status,
            "ollama": ollama_status,
            "redis": redis_status
        }
    )


# ============================================================================
# Activity Endpoints
# ============================================================================

@app.get("/api/activities/latest", tags=["Activities"])
async def get_latest_activities(limit: int = 10, days: int = 30):
    """
    Get latest activities from Strava
    
    Args:
        limit: Maximum number of activities (1-50)
        days: Look back this many days (1-90)
    """
    if not strava_client:
        raise HTTPException(status_code=503, detail="Strava client unavailable")
    
    try:
        activities = strava_client.get_activities(limit=limit, days=days)
        return {
            "count": len(activities),
            "limit": limit,
            "days": days,
            "activities": [a.dict() for a in activities]
        }
    except Exception as e:
        logger.error(f"Error fetching activities: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching activities: {str(e)}")


@app.get("/api/activities/{activity_id}", tags=["Activities"])
async def get_activity(activity_id: int):
    """Get specific activity details"""
    if not strava_client:
        raise HTTPException(status_code=503, detail="Strava client unavailable")
    
    try:
        activity = strava_client.get_activity(activity_id)
        return activity.dict()
    except Exception as e:
        logger.error(f"Error fetching activity {activity_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching activity: {str(e)}")


@app.post("/api/activities/sync", tags=["Activities"])
async def sync_activities():
    """Sync latest activities from Strava"""
    if not strava_client:
        raise HTTPException(status_code=503, detail="Strava client unavailable")
    
    try:
        activities = strava_client.get_activities(limit=50, days=7)
        logger.info(f"Synced {len(activities)} activities from Strava")
        return {
            "status": "success",
            "synced_count": len(activities),
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error syncing activities: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# ============================================================================
# Athlete Endpoints
# ============================================================================

@app.get("/api/athlete", tags=["Athlete"])
async def get_athlete():
    """Get current authenticated athlete profile"""
    if not strava_client:
        raise HTTPException(status_code=503, detail="Strava client unavailable")
    
    try:
        athlete = strava_client.get_athlete()
        stats = strava_client.get_stats()
        
        return {
            "athlete": athlete.dict(),
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error fetching athlete: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching athlete: {str(e)}")


# ============================================================================
# Coaching Endpoints
# ============================================================================

@app.post("/api/coach/analyze", tags=["Coaching"])
async def analyze_activities(days_back: int = 7):
    """
    Analyze recent activities and provide AI coaching insights
    
    Args:
        days_back: Number of days to analyze (1-90)
    """
    if not strava_client:
        raise HTTPException(status_code=503, detail="Strava client unavailable")
    if not ollama_handler:
        raise HTTPException(status_code=503, detail="AI engine unavailable")
    
    try:
        # Fetch activities
        activities = strava_client.get_activities(days=days_back, limit=20)
        
        if not activities:
            return {
                "analysis": "No activities found in the specified period. Start training to get personalized coaching!",
                "recommendations": ["Get out there and train!", "Set a consistent training routine"],
                "focus_areas": [],
                "next_workout_suggestions": ["Go for an easy 30-minute run"],
                "warnings": []
            }
        
        # Prepare data for LLM
        activities_summary = "\n".join([
            f"- {a.name} ({a.type}): {a.distance/1000:.1f}km, {a.duration//60}min"
            for a in activities
        ])
        
        # Generate coaching response
        system_prompt = """You are an experienced triathlon coach with expertise in training methodology, 
physiology, and athlete development. Analyze the training data and provide practical, actionable coaching advice."""
        
        prompt = f"""Analyze these training activities from the past {days_back} days and provide coaching insights:

{activities_summary}

Provide your response as ONLY a JSON object (no markdown) with these exact fields:
- analysis: string (2-3 sentences summarizing the training)
- recommendations: list of 3-5 specific, actionable recommendations
- focus_areas: list of 2-3 areas to focus on
- next_workout_suggestions: list of 2-3 specific next workout ideas
- warnings: list of any concerns (empty list if none)"""
        
        response = ollama_handler.generate_json(prompt, system_prompt=system_prompt)
        
        # Cache result if Redis available
        if redis_client and activities:
            try:
                redis_client.setex(
                    f"analysis:{activities[0].id}",
                    settings.redis_ttl,
                    str(response)
                )
            except Exception as e:
                logger.warning(f"Failed to cache result: {e}")
        
        logger.info("✓ Generated coaching analysis")
        return response
        
    except Exception as e:
        logger.error(f"Error in coaching analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ============================================================================
# Model/Info Endpoints
# ============================================================================

@app.get("/api/models", tags=["System"])
async def get_available_models():
    """Get list of available Ollama models"""
    if not ollama_handler:
        raise HTTPException(status_code=503, detail="Ollama unavailable")
    
    try:
        models = ollama_handler.list_models()
        return {
            "current_model": settings.ollama_model,
            "available_models": models,
            "count": len(models)
        }
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        raise HTTPException(status_code=500, detail="Error fetching models")


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP Exception: {exc.detail}")
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now()
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "error": "Internal server error",
        "status_code": 500,
        "timestamp": datetime.now()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=(settings.environment == "development")
    )
