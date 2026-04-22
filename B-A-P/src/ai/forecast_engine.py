from src.models.analytics_models import ForecastRequest, ForecastResponse
from src.ai.llm_client import generate_text
from src.utils.logger import get_logger

logger = get_logger()

async def generate_forecast(request: ForecastRequest) -> ForecastResponse:
    """Generate a forecast asynchronously using the configured Gemini model.
    
    Args:
        request: Forecast request with data to analyze
        
    Returns:
        Forecast response with generated forecast
        
    Raises:
        RuntimeError: If forecast generation fails
    """
    try:
        prompt = f"Forecast the following data: {request.data}"
        forecast = await generate_text(prompt)
        logger.info(f"Forecast generated for data: {request.data[:100]}...")
        return ForecastResponse(forecast=forecast)
    except Exception as e:
        logger.error(f"Failed to generate forecast: {e}")
        raise RuntimeError(f"Failed to generate forecast: {e}") from e
