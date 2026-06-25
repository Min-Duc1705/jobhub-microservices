# app/services/ai_assistant_service/vertex_initializer.py
import os
import logging
from app.config import settings

logger = logging.getLogger(__name__)
_vertex_initialized = False

def _init_vertex_ai():
    global _vertex_initialized
    if _vertex_initialized:
        return
    try:
        import vertexai
        from google.oauth2 import service_account
        
        project = settings.VERTEX_PROJECT_ID
        location = settings.VERTEX_LOCATION
        creds_path = settings.VERTEX_CREDENTIALS_JSON
        
        credentials = None
        if creds_path:
            clean_creds = creds_path.strip()
            if clean_creds.startswith("{"):
                import json
                creds_dict = json.loads(clean_creds)
                credentials = service_account.Credentials.from_service_account_info(creds_dict)
                logger.info("[VertexAI] Khởi tạo Vertex AI bằng raw JSON string credentials từ environment")
            elif os.path.exists(creds_path):
                credentials = service_account.Credentials.from_service_account_file(creds_path)
                logger.info(f"[VertexAI] Khởi tạo Vertex AI với service account từ file: {creds_path}")
            else:
                logger.warning(f"[VertexAI] VERTEX_CREDENTIALS_JSON được cấu hình nhưng file không tồn tại: {creds_path}")
        else:
            logger.info("[VertexAI] Khởi tạo Vertex AI với credentials mặc định (ADC) hoặc môi trường")
            
        vertexai.init(project=project, location=location, credentials=credentials)
        _vertex_initialized = True
    except Exception as e:
        logger.error(f"[VertexAI] Lỗi khởi tạo Vertex AI: {e}")
        raise e
