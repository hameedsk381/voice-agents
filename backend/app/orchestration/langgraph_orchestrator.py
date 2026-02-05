from typing import Annotated, Dict, TypedDict, List, Union, Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq

from app.core.config import settings
from loguru import logger
import json

# Define the state for the graph
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The conversation messages"]
    next_agent: str
    session_id: str
    current_agent_id: str
    language: str

class LangGraphOrchestrator:
    def __init__(self, agent_id: str, session_id: str, language: str = "en-US"):
        self.agent_id = agent_id
        self.session_id = session_id
        self.language = language
        
        # Initialize LLM
        if settings.GROQ_API_KEY:
            self.llm = ChatGroq(
                groq_api_key=settings.GROQ_API_KEY,
                model_name="llama-3.3-70b-versatile",
                temperature=0.2
            )
        else:
            logger.error("No GROQ_API_KEY found. LangGraph requires Groq.")
            self.llm = ChatGroq(
                groq_api_key=settings.GROQ_API_KEY,
                model_name="llama-3.1-8b-instant"
            )
            
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        # Define nodes
        workflow.add_node("router", self.router_node)
        workflow.add_node("support_agent", self.support_node)
        workflow.add_node("sales_agent", self.sales_node)
        workflow.add_node("compliance_agent", self.compliance_node)

        # Define edges
        workflow.set_entry_point("router")
        
        workflow.add_conditional_edges(
            "router",
            lambda x: x["next_agent"],
            {
                "support": "support_agent",
                "sales": "sales_agent",
                "compliance": "compliance_agent",
                "end": END
            }
        )

        workflow.add_edge("support_agent", END)
        workflow.add_edge("sales_agent", END)
        workflow.add_edge("compliance_agent", END)

        return workflow.compile()

    async def router_node(self, state: AgentState):
        """Decides which specialist should handle the query."""
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        system_prompt = (
            "You are a supervisor for a voice AI platform. "
            "Analyze the user query and route it to the correct specialist.\n"
            "Options: \n"
            "- 'support': For general help, account issues, or FAQs.\n"
            "- 'sales': For pricing, plans, or buying interests.\n"
            "- 'compliance': For sensitive data, complaints, or legally required disclosures.\n"
            "Return ONLY the word: support, sales, or compliance."
        )
        
        response = await self.llm.ainvoke([SystemMessage(content=system_prompt)] + messages)
        route = response.content.lower().strip()
        
        if "sales" in route:
            next_agent = "sales"
        elif "compliance" in route:
            next_agent = "compliance"
        else:
            next_agent = "support"
            
        return {"next_agent": next_agent}

    async def support_node(self, state: AgentState):
        system_prompt = (
            f"You are a helpful Support Voice Assistant. Language: {state['language']}. "
            "Keep responses concise and natural for voice conversation."
        )
        response = await self.llm.ainvoke([SystemMessage(content=system_prompt)] + state["messages"])
        return {"messages": [response]}

    async def sales_node(self, state: AgentState):
        system_prompt = (
            f"You are a pro-active Sales Voice Assistant. Language: {state['language']}. "
            "Your goal is to explain value and drive conversion. Keep it conversational."
        )
        response = await self.llm.ainvoke([SystemMessage(content=system_prompt)] + state["messages"])
        return {"messages": [response]}

    async def compliance_node(self, state: AgentState):
        system_prompt = (
            f"You are a formal Compliance Officer Voice Assistant. Language: {state['language']}. "
            "Ensure you address sensitive concerns professionally and mention hitl if needed."
        )
        response = await self.llm.ainvoke([SystemMessage(content=system_prompt)] + state["messages"])
        return {"messages": [response]}

    async def get_response(self, user_input: str, history: List[Dict[str, str]] = None):
        """Standard entry point for the orchestrator."""
        messages = []
        if history:
            for h in history:
                if h["role"] == "user":
                    messages.append(HumanMessage(content=h["content"]))
                else:
                    messages.append(AIMessage(content=h["content"]))
        
        messages.append(HumanMessage(content=user_input))
        
        initial_state = {
            "messages": messages,
            "next_agent": "router",
            "session_id": self.session_id,
            "current_agent_id": self.agent_id,
            "language": self.language
        }
        
        final_state = await self.graph.ainvoke(initial_state)
        return final_state["messages"][-1].content
