import operator
from typing import Annotated, List, Any, Optional, TypedDict, Dict

# define the schema of a single compliance issue

class ComplianceIssue(TypedDict):
    category: str
    description: str # Details of a violation
    severity: str # CRITICAL, warning etc
    timestamp: Optional[str]

class VideoAuditState(TypedDict):

    '''Defines the data schema for langgraph execution'''

    # input parameters

    video_url: str
    video_id: str

    # ingestion & extraction
    local_file_path : Optional[str]
    video_metadata: Dict[str, Any]
    transcript: Optional[str]
    ocr_text: List[str]

    # analysis output
    compliance_results : Annotated[List[ComplianceIssue], operator.add]

    # final results
    final_status: str
    final_report: str # markdown format

    # system observaability
    errors:  Annotated[List[str], operator.add]


