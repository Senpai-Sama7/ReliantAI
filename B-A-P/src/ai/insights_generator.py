from src.ai.llm_client import generate_text
from src.utils.logger import get_logger

logger = get_logger()

async def generate_insights(dataset_id: str, user: str) -> str:
    """Generate business insights for a dataset asynchronously.
    
    Args:
        dataset_id: The dataset to analyze
        user: User requesting insights
        
    Returns:
        Generated insights text
        
    Raises:
        RuntimeError: If insight generation fails
    """
    try:
        prompt = f"Generate business insights for dataset {dataset_id}."
        insights = await generate_text(prompt)
        logger.info(f"Insights for {dataset_id} by {user}: {insights[:100]}...")
        return insights
    except Exception as e:
        logger.error(f"Failed to generate insights for {dataset_id} by {user}: {e}")
        raise RuntimeError(f"Failed to generate insights: {e}") from e
