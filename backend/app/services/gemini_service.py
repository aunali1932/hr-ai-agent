import google.generativeai as genai
from app.config import settings

# Configure API key
# Note: google.generativeai is deprecated but still functional
# TODO: Migrate to google.genai when stable
genai.configure(api_key=settings.GEMINI_API_KEY)


def get_gemini_model(model_name: str = None):
    """Get a Gemini model instance"""
    if model_name is None:
        model_name = settings.GEMINI_MODEL
    return genai.GenerativeModel(model_name)


def get_embedding_model():
    """Get Gemini embedding model - not used directly, use embed_content instead"""
    pass


def generate_text(prompt: str, model_name: str = None) -> str:
    """Generate text using Gemini"""
    if model_name is None:
        model_name = settings.GEMINI_MODEL
    model = get_gemini_model(model_name)
    response = model.generate_content(prompt)
    return response.text


def generate_embedding(text: str) -> list:
    """Generate embedding for text using Gemini"""
    try:
        result = genai.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"Error generating embedding: {e}")
        # Return empty list - dimension will be detected from first successful embedding
        return []

