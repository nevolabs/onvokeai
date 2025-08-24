# app/utils/database.py
from supabase import Client
from app.config.logging import get_logger

logger = get_logger(__name__)

def update_document_status(supabase: Client, job_id: str, status: str) -> None:
    """
    Helper function to update the status column in the generated_docs table.
    
    Args:
        supabase: Supabase client instance
        job_id: The ID of the document to update
        status: The new status ('success' or 'failed')
    """
    try:
        logger.info(f"Updating status to '{status}' for document ID {job_id}")
        response = supabase.table("generated_docs").update(
            {"status": status}
        ).eq("id", job_id).execute()

        if not response.data or len(response.data) == 0:
            logger.warning(f"No record found to update status for ID {job_id}")
    except Exception as e:
        logger.error(f"Failed to update status for document ID {job_id}: {e}")
        raise ValueError(f"Failed to update document status: {e}")