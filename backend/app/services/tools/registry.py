from .base import BaseTool
import random
from datetime import datetime, timedelta

class GetOrderStatusTool(BaseTool):
    name = "get_order_status"
    description = "Get the current status of a customer's order by order ID or phone number."
    parameters = {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "The order ID to look up"
            },
            "phone_number": {
                "type": "string",
                "description": "Customer phone number to look up orders"
            }
        },
        "required": []
    }
    
    async def execute(self, order_id: str = None, phone_number: str = None) -> str:
        # Simulated order lookup
        statuses = ["Processing", "Shipped", "Out for Delivery", "Delivered"]
        status = random.choice(statuses)
        eta = (datetime.now() + timedelta(days=random.randint(1, 5))).strftime("%B %d, %Y")
        
        if order_id:
            return f"Order {order_id} is currently '{status}'. Expected delivery: {eta}."
        elif phone_number:
            return f"Found 1 order for {phone_number}. Status: '{status}'. Expected delivery: {eta}."
        return "Please provide an order ID or phone number."


class CheckAccountBalanceTool(BaseTool):
    name = "check_account_balance"
    description = "Check the account balance for a customer."
    parameters = {
        "type": "object",
        "properties": {
            "account_id": {
                "type": "string",
                "description": "The account ID or customer ID"
            }
        },
        "required": ["account_id"]
    }
    
    async def execute(self, account_id: str) -> str:
        # Simulated balance check
        balance = round(random.uniform(100, 10000), 2)
        return f"Account {account_id} has a current balance of ${balance:,.2f}."


class ScheduleCallbackTool(BaseTool):
    name = "schedule_callback"
    description = "Schedule a callback from a human agent at a specified time."
    parameters = {
        "type": "object",
        "properties": {
            "preferred_time": {
                "type": "string",
                "description": "The preferred time for callback (e.g., 'tomorrow at 2pm', 'in 1 hour')"
            },
            "reason": {
                "type": "string",
                "description": "Brief reason for the callback request"
            }
        },
        "required": ["preferred_time"]
    }
    
    async def execute(self, preferred_time: str, reason: str = "General inquiry") -> str:
        return f"Callback scheduled for {preferred_time}. Reason: {reason}. A human agent will call you back."


class TransferToHumanTool(BaseTool):
    name = "transfer_to_human"
    description = "Transfer the call to a human agent when the AI cannot help or customer requests it."
    parameters = {
        "type": "object",
        "properties": {
            "department": {
                "type": "string",
                "enum": ["support", "sales", "billing", "technical"],
                "description": "Department to transfer to"
            },
            "summary": {
                "type": "string",
                "description": "Brief summary of the conversation for the human agent"
            }
        },
        "required": ["department"]
    }
    
    async def execute(self, department: str, summary: str = "") -> str:
        return f"Transferring to {department} department. Please hold while I connect you with a human agent."


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for up-to-date information, news, or specific facts."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query"
            }
        },
        "required": ["query"]
    }
    
    async def execute(self, query: str) -> str:
        # Simulated web search
        return f"Search results for '{query}': According to recent reports, the requested information is verified as of {datetime.now().strftime('%Y')}. (Detailed simulated snippet provided)."


class RefundCustomerTool(BaseTool):
    name = "refund_customer"
    description = "Initiate a refund for a customer. Requires human approval for security."
    requires_approval = True
    parameters = {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "The ID of the order to refund"
            },
            "amount": {
                "type": "number",
                "description": "Amount to refund"
            },
            "reason": {
                "type": "string",
                "description": "Reason for the refund"
            }
        },
        "required": ["order_id", "amount"]
    }
    
    async def execute(self, order_id: str, amount: float, reason: str = "") -> str:
        return f"Refund of ${amount} for order {order_id} has been submitted for approval. Approval ID: {random.randint(1000, 9999)}."


class SearchKnowledgeTool(BaseTool):
    name = "search_knowledge_base"
    description = "Search the company knowledge base for documentation, FAQs, and policies."
    parameters = {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "The topic or question to search for"
            }
        },
        "required": ["topic"]
    }
    
    async def execute(self, topic: str) -> str:
        # This would interface with the vector database / Rag service
        return f"Documentation found for '{topic}': Our current policy allows for returns within 30 days of purchase. (Simulated RAG result)."


class UpdateProfileTool(BaseTool):
    name = "update_user_profile"
    description = "Update the customer's preferred contact method, name, or other profile details."
    parameters = {
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "description": "The profile field to update (e.g., 'nickname', 'preferred_email')"
            },
            "value": {
                "type": "string",
                "description": "The new value"
            }
        },
        "required": ["key", "value"]
    }
    
    async def execute(self, key: str, value: str) -> str:
        return f"Successfully updated your {key} to {value} in our CRM records."


# Tool Registry
AVAILABLE_TOOLS = {
    "get_order_status": GetOrderStatusTool(),
    "check_account_balance": CheckAccountBalanceTool(),
    "schedule_callback": ScheduleCallbackTool(),
    "transfer_to_human": TransferToHumanTool(),
    "web_search": WebSearchTool(),
    "refund_customer": RefundCustomerTool(),
    "search_knowledge_base": SearchKnowledgeTool(),
    "update_user_profile": UpdateProfileTool(),
}

def get_tools_for_agent(tool_names: list) -> list:
    """Get tool instances for a list of tool names."""
    return [AVAILABLE_TOOLS[name] for name in tool_names if name in AVAILABLE_TOOLS]

def get_tool_schemas(tool_names: list) -> list:
    """Get tool schemas for function calling."""
    tools = get_tools_for_agent(tool_names)
    return [tool.to_schema() for tool in tools]
