"""
AI-powered route optimization API endpoints
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.ai import AIError, RouteOptimizeRequest, RouteOptimizeResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/route-optimize",
    response_model=RouteOptimizeResponse,
    summary="AI-powered route optimization",
    description="""
    **AI Route Optimization**

    Use OpenAI's GPT models to analyze and optimize route data with natural language instructions.

    **Features:**
    - ✅ Natural language prompts for route optimization
    - ✅ Flexible data input (string or structured)
    - ✅ Customizable response format
    - ✅ Support for fixed stops and constraints
    - ✅ Comprehensive error handling

    **Use Cases:**
    - Optimize stop order based on custom criteria
    - Analyze route efficiency and suggest improvements
    - Handle complex routing constraints with natural language
    - Generate human-readable route summaries

    **Example Request:**
    ```json
    {
      "prompt": "Create the right order of the route, assuming that start and end are book-endings, and stops are ordered in the optimized route. If a stop is marked as fixed, order for that specific stop should not change.",
      "data": "Type | Location | Address\\nStart | 32.1878296, 34.9354013 | מיכל, כפר סבא, ישראל\\nEnd | 32.067444, 34.7936703 | יגאל אלון, 6789731 תל־אביב–יפו, ישראל\\nStop | 32.1962854, 34.8766859 | רננים, רעננה, ישראל\\nStop | 32.1739447, 34.8081801 | הרצליה פיתוח, הרצליה, ישראל\\nStop | 32.1879896, 34.8934844 | כפר סבא הירוקה, כפר סבא, ישראל",
      "response_structure": "Start: מיכל, כפר סבא (32.1878296, 34.9354013)\\nStop 1: כפר סבא הירוקה (32.1879896, 34.8934844)\\nStop 2: רננים, רעננה (32.1962854, 34.8766859)\\nStop 3: הרצליה פיתוח (32.1739447, 34.8081801)\\nEnd: יגאל אלון, תל אביב–יפו (32.067444, 34.7936703)"
    }
    ```

    **Authentication Required:** Bearer token
    """,
    responses={
        400: {"model": AIError, "description": "Invalid request data"},
        401: {"description": "Authentication required"},
        429: {"model": AIError, "description": "Rate limit exceeded"},
        500: {"model": AIError, "description": "Internal server error"},
    },
)
async def optimize_route_with_ai(
    request: RouteOptimizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Optimize route order using OpenAI's AI models with natural language instructions.
    """

    # Validate OpenAI API key is configured
    if not settings.OPENAI_API_KEY:
        logger.error("OpenAI API key not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service not configured. Please contact support.",
        )

    try:
        # Import OpenAI client
        from openai import OpenAI

        # Initialize OpenAI client
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # Prepare data for AI processing
        data_str = request.data if isinstance(request.data, str) else str(request.data)

        # Construct the system message
        system_message = """You are a route optimization assistant. Your task is to analyze route data and provide optimized stop orders based on the given instructions.

Key principles:
- Always respect fixed stops and constraints mentioned in the prompt
- Consider geographical proximity and logical travel patterns
- Maintain start and end points as specified
- Provide clear, structured responses in the requested format
- Focus on practical, efficient routing solutions"""

        # Construct the user message
        user_message = f"""
**Instructions:** {request.prompt}

**Route Data:**
{data_str}

**Required Response Format:**
{request.response_structure}

Please analyze the route data and provide an optimized order following the instructions and response format above.
"""

        logger.info(f"Making OpenAI API call for user {current_user.id}")

        # Make the OpenAI API call
        response = client.chat.completions.create(
            model="gpt-4",  # Use GPT-4 for better reasoning
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            max_tokens=1000,
            temperature=0.1,  # Low temperature for consistent, logical responses
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        # Extract the result
        ai_result = response.choices[0].message.content.strip()

        # Prepare metadata
        metadata = {
            "model": response.model,
            "tokens_used": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            "finish_reason": response.choices[0].finish_reason,
        }

        logger.info(
            f"OpenAI API call successful for user {current_user.id}. "
            f"Tokens used: {response.usage.total_tokens}"
        )

        # Prepare response
        return RouteOptimizeResponse(
            result=ai_result,
            raw_response=response.model_dump() if settings.DEBUG else None,
            metadata=metadata,
        )

    except ImportError as e:
        logger.error("OpenAI package not installed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service dependencies not available. Please contact support.",
        ) from e

    except Exception as e:
        # Handle OpenAI API errors
        if hasattr(e, "response") and hasattr(e.response, "status_code"):
            if e.response.status_code == 401:
                logger.error("OpenAI API authentication failed")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="AI service authentication failed. Please contact support.",
                ) from e
            elif e.response.status_code == 429:
                logger.warning("OpenAI API rate limit exceeded")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="AI service temporarily unavailable due to high demand. Please try again in a few moments.",
                ) from e
            elif e.response.status_code >= 500:
                logger.error(f"OpenAI API server error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI service temporarily unavailable. Please try again later.",
                ) from e

        # Handle other errors
        logger.error(f"Unexpected error in AI route optimization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request. Please try again.",
        ) from e


@router.get("/health")
async def ai_health():
    """Health check for AI endpoints"""
    return {
        "status": "healthy",
        "service": "ai-route-optimization",
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "endpoints": ["/ai/route-optimize"],
    }
