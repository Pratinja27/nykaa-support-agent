from typing import Literal, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class AgentResponseSchema(BaseModel):
    """Schema defining the strict structure for all agent responses."""

    thread_id: str = Field(..., description="Unique thread identifier")
    query: str = Field(..., description="The user query processed in this turn")
    route: Literal["rag", "order"] = Field(..., description="Execution path chosen ('rag' or 'order')")
    final_response: str = Field(..., description="Text response generated for user")
    source: str = Field(..., description="Source engine or tool used")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Execution metadata")

    @field_validator("final_response")
    @classmethod
    def response_must_not_be_empty(cls, value: str) -> str:
        """Ensure response string is not empty or whitespace only."""
        if not value or not value.strip():
            raise ValueError("final_response cannot be empty")
        return value


if __name__ == "__main__":
    print("=== TASK 9 SCHEMA VALIDATION DEMO ===")
    
    # Test valid response
    valid_res = AgentResponseSchema(
        thread_id="thread_001",
        query="What is the status of my order?",
        route="order",
        final_response="Order ORD1001 is currently Placed.",
        source="order_tool"
    )
    print("\n[Passed] Valid Model:")
    print(valid_res.model_dump_json(indent=2))

    # Test schema validation failure (empty final_response)
    try:
        AgentResponseSchema(
            thread_id="thread_001",
            query="Status?",
            route="order",
            final_response="   ",
            source="order_tool"
        )
    except Exception as e:
        print("\n[Passed] Caught Expected Validation Error:")
        print(e)