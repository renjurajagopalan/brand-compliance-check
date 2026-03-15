import os
import json
from typing import Any, Dict, List
import logging
import re

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

# import state schema
from backend.src.graph.state import ComplianceIssue,VideoAuditState

# import services
from backend.src.services.video_indexer import VideoIndexerService

# configure the logger
logger  = logging.getLogger("brand-guardian")
logging.basicConfig(level=logging.INFO)

# Video Indexer node

def index_video_node(state: VideoAuditState) -> Dict[str, Any]:
    '''Downloads the youtube from the URL and uploads it to Azure Video Indexer
       Extracts the insights from the viido
    '''
    video_url = state.get("video_url")
    video_id_input = state.get("video_id")

    logger.info(f"-- [Node.Indexer] Processing {video_url}")

    local_filename = "temp_audit_video.mp4"

    try:
        vi_service = VideoIndexerService()

        # download the video
        if "youtube.com" in video_url or "youtu.be" in video_url:
            local_path = vi_service.download_youtube_video(url=video_url, output_path = local_filename )
        else:
            raise Exception("Please provide a valid YouTUbe URL for this test")
        
        #upload the video
        azure_video_id = vi_service.upload_video(local_path, video_name = video_id_input )
        logger.info("---Upload success.  Azure ID: {azure_video_id}")

        # clean up
        if os.path.exists(local_path):
            os.remove(local_path)

        # wait
        raw_insights = vi_service.wait_for_processing(azure_video_id)

        #extract clean data
        clean_data = vi_service.extract_data(raw_insights)
        logger.info(f"----[Node: Indexer] Extraction complete----")
        return clean_data
    
    except Exception as e:
        logger.error(f"Video Indexer failed: {e}")
        return {
            "errors": [str(e)],
            "final_status": "FAIL",
            "transcript": "",
            "ocr_text": []
            
        }
    

# Compliance auditor node

def audit_content_node(state: VideoAuditState) -> Dict[str, Any]:
    '''
    Performs Retrieval Augemented Generation to audit the content
    
    '''
    logger.info(f"---[Node: Compliance Audtor] querying the knowledge base & LLM")
    transcript = state.get("transcript")
    if not transcript:
        logger.warning("No transcript availalbe. Skipping the audit")
        return {
            "final_status" : "FAIL",
            "final_report" : "Audit skipped as transcript is not available"
        }

    # Initialize the clients

    llm = AzureChatOpenAI(
        azure_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature = 0.0
    )

    embeddings = AzureOpenAIEmbeddings(
        azure_deployment = "text-embedding-3-small",
        openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    )

    vector_store = AzureSearch(
        azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT"),
        azure_search_key = os.getenv("AZURE_SEARCH_API_KEY"),
        index_name = os.getenv("AZURE_SEARCH_INDEX_NAME"),
        embedding_function=embeddings.embed_query
    )

    # RAG Retrieval
    ocr_text = state.get("ocr_text")
    query_text = f"{transcript} {''.join(ocr_text)}"
    docs = vector_store.similarity_search(query_text,k=3)
    retrieved_rules = "\n\n".join([doc.page_content for doc in docs])

    system_prompt = f"""
        You are a senior brand compliance auditor
        OFFICIAL REGULATORY RULES: 
        {retrieved_rules}
        INSTRUCTIONS:
        1. Analyze the trancript and OCR text below 
        2. Identify any violation of the rules
        3. Strictly return JSON in below format
        {{
            "compliance_results" : [
            {{
                "category": "Claim Validdation"
                "severity": "critical"
                "description": "Explanation of the violation"                
            }}],
            "status" : "FAIL",
            "final_report": "Summary of findings..."
        }}

        If no violations are found , set "status" to "PASS" and "compliance_results" to [].
        """
    user_message = f"""
        VIDEO_METADATA : {state.get('video_metadata', {})}
        TRANSCRIPT: {transcript}
        ON-SCREEN TEXT (OCR): {ocr_text}
        """
    
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])

        content = response.content
        if "~~~" in content:
            content = re.search(r"~~~(?:json)?(.?)~~~",content,re.DOTALL).group(1)
        audit_data = json.loads(content.strip())

        return {
            "compliance_results": audit_data.get("compliance_results",[]),
            "final_status":audit_data.get("status", "FAIL"),
            "final_report": audit_data.get("final_report","No report generated")
        }
    
    except Exception as e:
        logger.error(f"System error in Auditor node {str(e)}")

        # logging the raw response
        logger.error(f" Raw LLM Response: {response.content if 'response' in locals() else None}")
        return {
            "errors": [str(e)],
            "final_status": "FAIL"

        }