import random
from datetime import datetime, timedelta
from .base import BaseTool, ToolResult


class VerifyAadhaarTool(BaseTool):
    name = "verify_aadhaar"
    simulated = True
    description = "Verify the last 4 digits of an Aadhaar number against the registered mobile number for identity confirmation."
    parameters = {
        "type": "object",
        "properties": {
            "aadhaar_last4": {
                "type": "string",
                "description": "Last 4 digits of the Aadhaar number"
            },
            "registered_mobile": {
                "type": "string",
                "description": "Registered mobile number (10 digits)"
            }
        },
        "required": ["aadhaar_last4"]
    }
    cost_per_call = 0.5

    async def execute(self, aadhaar_last4: str = None, registered_mobile: str = None) -> ToolResult:
        if not aadhaar_last4 or len(aadhaar_last4) != 4 or not aadhaar_last4.isdigit():
            return ToolResult(
                result="Please provide a valid 4-digit Aadhaar suffix.",
                confidence=1.0
            )
        # Simulated OTP-based verification
        verified = random.random() > 0.2  # 80% simulated success
        if verified:
            return ToolResult(
                result=f"Aadhaar ending with {aadhaar_last4} verified successfully.",
                confidence=0.95,
                metadata={"verified": True, "method": "otp"}
            )
        return ToolResult(
            result=f"Could not verify Aadhaar ending with {aadhaar_last4}. The details may not match our records.",
            confidence=0.7,
            metadata={"verified": False}
        )


class VerifyPANCardTool(BaseTool):
    name = "verify_pan"
    simulated = True
    description = "Verify an Indian PAN card number and check its validity status with the income tax department."
    parameters = {
        "type": "object",
        "properties": {
            "pan_number": {
                "type": "string",
                "description": "The 10-character PAN card number (e.g., ABCDE1234F)"
            }
        },
        "required": ["pan_number"]
    }
    cost_per_call = 0.3

    async def execute(self, pan_number: str) -> ToolResult:
        pan = (pan_number or "").upper().strip()
        if len(pan) != 10 or not pan[:5].isalpha() or not pan[5:9].isdigit() or not pan[9].isalpha():
            return ToolResult(
                result="Invalid PAN format. A valid PAN has 10 characters: first 5 letters, next 4 digits, last 1 letter (e.g., ABCDE1234F).",
                confidence=1.0
            )
        # Simulated PAN verification
        return ToolResult(
            result=f"PAN {pan} is active and valid as per income tax records.",
            confidence=0.9,
            metadata={"pan_status": "active", "pan_category": pan[3]}
        )


class CheckUPIPaymentTool(BaseTool):
    name = "check_upi_payment"
    simulated = True
    description = "Check the status of a UPI transaction by UPI transaction ID or reference number."
    parameters = {
        "type": "object",
        "properties": {
            "transaction_id": {
                "type": "string",
                "description": "UPI transaction ID or reference number"
            },
            "upi_id": {
                "type": "string",
                "description": "UPI ID (e.g., name@upi) to check recent transactions"
            }
        },
        "required": []
    }
    cost_per_call = 0.2

    async def execute(self, transaction_id: str = None, upi_id: str = None) -> ToolResult:
        statuses = ["Success", "Pending", "Failed", "Refunded"]
        status = random.choices(statuses, weights=[65, 15, 15, 5])[0]
        amount = round(random.uniform(100, 50000), 2)

        if transaction_id:
            if status == "Success":
                return ToolResult(
                    result=f"UPI transaction {transaction_id} of ₹{amount:,.2f} completed successfully.",
                    confidence=0.98,
                    metadata={"status": status, "amount": amount}
                )
            return ToolResult(
                result=f"UPI transaction {transaction_id} is currently {status}. Amount: ₹{amount:,.2f}.",
                confidence=0.85,
                metadata={"status": status, "amount": amount}
            )
        elif upi_id:
            return ToolResult(
                result=f"Found {random.randint(1, 5)} recent transactions for {upi_id}. Last transaction: ₹{amount:,.2f} ({status}).",
                confidence=0.8,
                metadata={"upi_id": upi_id, "recent_status": status}
            )
        return ToolResult(
            result="Please provide a UPI transaction ID or UPI ID to check payment status.",
            confidence=1.0
        )


class LookupPincodeTool(BaseTool):
    name = "lookup_pincode"
    description = "Look up Indian pincode details including city, district, and state."
    parameters = {
        "type": "object",
        "properties": {
            "pincode": {
                "type": "string",
                "description": "6-digit Indian pincode"
            }
        },
        "required": ["pincode"]
    }
    cost_per_call = 0.1

    async def execute(self, pincode: str) -> ToolResult:
        pin = (pincode or "").strip()
        if len(pin) != 6 or not pin.isdigit():
            return ToolResult(
                result="Invalid pincode. A valid Indian pincode has exactly 6 digits.",
                confidence=1.0
            )
        # Simulated pincode DB
        cities = {
            "110": {"city": "New Delhi", "state": "Delhi"},
            "400": {"city": "Mumbai", "state": "Maharashtra"},
            "560": {"city": "Bengaluru", "state": "Karnataka"},
            "600": {"city": "Chennai", "state": "Tamil Nadu"},
            "700": {"city": "Kolkata", "state": "West Bengal"},
            "500": {"city": "Hyderabad", "state": "Telangana"},
            "380": {"city": "Ahmedabad", "state": "Gujarat"},
            "302": {"city": "Jaipur", "state": "Rajasthan"},
            "226": {"city": "Lucknow", "state": "Uttar Pradesh"},
            "800": {"city": "Patna", "state": "Bihar"},
        }
        prefix = pin[:3]
        if prefix in cities:
            info = cities[prefix]
            return ToolResult(
                result=f"Pincode {pin}: {info['city']}, District: {info['city']}, State: {info['state']}.",
                confidence=0.95,
                metadata={"city": info["city"], "state": info["state"]}
            )
        return ToolResult(
            result=f"Pincode {pin} is a valid Indian pincode but details could not be found in our database.",
            confidence=0.5,
            metadata={"pincode": pin}
        )


class CheckGSTTool(BaseTool):
    name = "check_gst"
    simulated = True
    description = "Look up GST registration details for an Indian business using its GSTIN."
    parameters = {
        "type": "object",
        "properties": {
            "gstin": {
                "type": "string",
                "description": "15-character GST Identification Number (GSTIN)"
            }
        },
        "required": ["gstin"]
    }
    cost_per_call = 0.4

    async def execute(self, gstin: str) -> ToolResult:
        gst = (gstin or "").upper().strip()
        if len(gst) != 15:
            return ToolResult(
                result="Invalid GSTIN. A valid GSTIN has 15 characters.",
                confidence=1.0
            )
        # Simulated GST lookup
        return ToolResult(
            result=f"GSTIN {gst} is active. Business name: (simulated) Trading Co. Pvt. Ltd. Status: Registered and compliant.",
            confidence=0.85,
            metadata={"gstin": gst, "status": "active"}
        )


class TranslateToHindiTool(BaseTool):
    name = "translate_to_hindi"
    simulated = True
    description = "Translate English text to Hindi in real-time for bilingual conversations with Indian users."
    parameters = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "English text to translate to Hindi"
            }
        },
        "required": ["text"]
    }
    cost_per_call = 0.05

    async def execute(self, text: str) -> ToolResult:
        # Simulated Hindi translation
        return ToolResult(
            result=f"हिंदी अनुवाद: {text} (Simulated Hindi translation of the provided text.)",
            confidence=0.8,
            metadata={"source_language": "en", "target_language": "hi"}
        )


class CheckLoanEMITool(BaseTool):
    name = "check_loan_emi"
    description = "Calculate monthly EMI for a loan amount with Indian interest rates and tenure options."
    parameters = {
        "type": "object",
        "properties": {
            "loan_amount": {
                "type": "number",
                "description": "Principal loan amount in rupees"
            },
            "interest_rate": {
                "type": "number",
                "description": "Annual interest rate in percentage (e.g., 10.5 for 10.5%)"
            },
            "tenure_months": {
                "type": "number",
                "description": "Loan tenure in months"
            }
        },
        "required": ["loan_amount", "interest_rate", "tenure_months"]
    }
    cost_per_call = 0.1

    async def execute(self, loan_amount: float, interest_rate: float, tenure_months: float) -> ToolResult:
        if loan_amount <= 0 or interest_rate <= 0 or tenure_months <= 0:
            return ToolResult(
                result="Loan amount, interest rate, and tenure must be positive values.",
                confidence=1.0
            )
        monthly_rate = interest_rate / 12 / 100
        emi = loan_amount * monthly_rate * (1 + monthly_rate) ** tenure_months / ((1 + monthly_rate) ** tenure_months - 1)
        total_payment = emi * tenure_months
        total_interest = total_payment - loan_amount

        return ToolResult(
            result=f"For a loan of ₹{loan_amount:,.2f} at {interest_rate}% for {int(tenure_months)} months: "
                   f"Monthly EMI: ₹{emi:,.2f}, Total Interest: ₹{total_interest:,.2f}, "
                   f"Total Payment: ₹{total_payment:,.2f}.",
            confidence=0.99,
            metadata={"emi": round(emi, 2), "total_interest": round(total_interest, 2), "total_payment": round(total_payment, 2)}
        )


class ScheduleCallbackTool(BaseTool):
    name = "schedule_callback"
    description = "Schedule a callback from a human agent at a specified time."
    parameters = {
        "type": "object",
        "properties": {
            "preferred_time": {
                "type": "string",
                "description": "Preferred callback time in IST (e.g., 'tomorrow at 2pm', 'in 1 hour')"
            },
            "reason": {
                "type": "string",
                "description": "Brief reason for the callback (e.g., 'loan inquiry', 'account issue')"
            }
        },
        "required": ["preferred_time"]
    }
    cost_per_call = 0.0

    async def execute(self, preferred_time: str, reason: str = "General inquiry") -> ToolResult:
        return ToolResult(
            result=f"Callback scheduled for {preferred_time} IST. Reason: {reason}. Our team will call you back.",
            confidence=0.95,
            metadata={"scheduled_time": preferred_time, "reason": reason}
        )


class TransferToHumanTool(BaseTool):
    name = "transfer_to_human"
    description = "Transfer the call to a human agent for support in English or Hindi."
    parameters = {
        "type": "object",
        "properties": {
            "department": {
                "type": "string",
                "enum": ["support", "sales", "billing", "technical", "loans", "complaints"],
                "description": "Department to transfer to"
            },
            "language": {
                "type": "string",
                "enum": ["english", "hindi", "hinglish"],
                "description": "Preferred language for the human agent"
            },
            "summary": {
                "type": "string",
                "description": "Brief conversation summary for the human agent"
            }
        },
        "required": ["department"]
    }
    cost_per_call = 0.0

    async def execute(self, department: str, language: str = "english", summary: str = "") -> ToolResult:
        lang_hint = f" in {language}" if language != "english" else ""
        return ToolResult(
            result=f"Transferring to {department} department{lang_hint}. Please hold while I connect you.",
            confidence=1.0,
            metadata={"department": department, "language": language}
        )


class SearchKnowledgeBaseTool(BaseTool):
    name = "search_knowledge_base"
    description = "Search this agent's knowledge base (policies, FAQs, product/loan details, documentation) for facts relevant to the customer's question. Use whenever the customer asks something that may be answered by company documentation."
    parameters = {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "The question or topic to look up (e.g., 'late payment fee', 'foreclosure charges', 'EMI restructuring options')"
            }
        },
        "required": ["topic"]
    }
    cost_per_call = 0.05
    needs_context = True

    async def execute(self, topic: str, _db=None, _session_id=None, _agent_id=None) -> ToolResult:
        if not _db or not _agent_id:
            return ToolResult(
                result="I don't have a knowledge base available for this query right now.",
                confidence=0.4,
                metadata={"topic": topic, "reason": "no_context"},
            )
        try:
            from app.services.knowledge_service import KnowledgeService

            chunks = await KnowledgeService(_db).query_knowledge(
                _agent_id, topic, limit=3, min_score=0.45
            )
        except Exception as exc:
            from loguru import logger
            logger.error(f"Knowledge search failed for agent {_agent_id}: {exc}")
            return ToolResult(
                result="I couldn't reach the knowledge base just now.",
                confidence=0.3,
                metadata={"topic": topic, "error": str(exc)},
            )

        if not chunks:
            return ToolResult(
                result=f"I don't have anything in my knowledge base about '{topic}'.",
                confidence=0.5,
                metadata={"topic": topic, "matches": 0},
            )

        combined = " ".join(c.get("content", "").strip() for c in chunks if c.get("content"))
        top_score = max((c.get("score", 0) for c in chunks), default=0.0)
        return ToolResult(
            result=combined or f"I found related material on '{topic}' but couldn't extract a clear answer.",
            confidence=round(float(top_score), 2) if top_score else 0.7,
            metadata={"topic": topic, "matches": len(chunks)},
        )


class RecordPromiseToPayTool(BaseTool):
    name = "record_promise_to_pay"
    description = (
        "Record a borrower's commitment to pay an overdue amount by a specific date. "
        "Call this the moment the customer agrees to pay — it marks the call a success."
    )
    parameters = {
        "type": "object",
        "properties": {
            "amount": {
                "type": "number",
                "description": "Amount the customer promised to pay, in rupees"
            },
            "date": {
                "type": "string",
                "description": "Date the customer promised to pay by (e.g. '2026-07-05' or 'next Friday')"
            }
        },
        "required": ["amount", "date"]
    }
    cost_per_call = 0.0
    needs_context = True

    async def execute(self, amount: float = 0, date: str = "", _db=None, _session_id=None, _agent_id=None) -> ToolResult:
        from app.orchestration.session_manager import session_manager

        if _session_id:
            await session_manager.update_session_metadata(_session_id, {
                "collections_outcome": {
                    "type": "promise_to_pay",
                    "amount": amount,
                    "date": date,
                }
            })
        return ToolResult(
            result=f"Noted. I've recorded your commitment to pay ₹{amount:,.0f} by {date}. Thank you.",
            confidence=0.98,
            metadata={"outcome": "promise_to_pay", "amount": amount, "date": date},
        )


class SendPaymentLinkTool(BaseTool):
    name = "send_payment_link"
    description = (
        "Generate a secure payment link for the outstanding amount and send it to the "
        "customer over SMS so they can pay immediately. Use after the customer agrees to pay now."
    )
    parameters = {
        "type": "object",
        "properties": {
            "amount": {
                "type": "number",
                "description": "Amount to collect, in rupees"
            }
        },
        "required": ["amount"]
    }
    cost_per_call = 0.0
    needs_context = True

    async def execute(self, amount: float = 0, _db=None, _session_id=None, _agent_id=None) -> ToolResult:
        from app.orchestration.session_manager import session_manager
        from app.services.razorpay_service import RazorpayService
        from app.services.sms_service import SmsService

        customer_phone = None
        organization_id = None
        if _session_id:
            session = await session_manager.get_session(_session_id)
            if session:
                customer_phone = session.get("caller_id")
                organization_id = (session.get("metadata") or {}).get("org_id")

        rzp = RazorpayService()
        link = rzp.create_payment_link(
            amount,
            customer_phone=customer_phone,
            description="EMI payment",
            notes={
                "session_id": _session_id or "",
                "agent_id": _agent_id or "",
                "organization_id": organization_id or "",
            },
        )
        short_url = link.get("short_url")

        # Payment provider not configured / failed — do not pretend a link was sent.
        if not short_url:
            return ToolResult(
                result="I'm unable to generate a payment link right now. I'll have someone follow up with payment instructions.",
                confidence=0.3,
                metadata={"payment_link_error": link.get("error", "unavailable"), "amount": amount},
            )

        # Send the link over SMS.
        if customer_phone and short_url:
            try:
                SmsService(_db).send_message(
                    to_phone=customer_phone,
                    message=f"Pay your EMI of ₹{amount:,.0f} securely here: {short_url}",
                    organization_id=organization_id,
                )
            except Exception:
                pass

        if _session_id:
            await session_manager.update_session_metadata(_session_id, {
                "payment_link_id": link.get("id"),
                "payment_link_amount": amount,
            })

        return ToolResult(
            result=f"I've sent a secure payment link for ₹{amount:,.0f} to your phone by SMS. "
                   "Please tap it to pay.",
            confidence=0.97,
            metadata={"payment_link_id": link.get("id"), "short_url": short_url, "amount": amount},
        )


# Tool Registry
AVAILABLE_TOOLS = {
    "verify_aadhaar": VerifyAadhaarTool(),
    "verify_pan": VerifyPANCardTool(),
    "check_upi_payment": CheckUPIPaymentTool(),
    "lookup_pincode": LookupPincodeTool(),
    "check_gst": CheckGSTTool(),
    "translate_to_hindi": TranslateToHindiTool(),
    "check_loan_emi": CheckLoanEMITool(),
    "schedule_callback": ScheduleCallbackTool(),
    "transfer_to_human": TransferToHumanTool(),
    "search_knowledge_base": SearchKnowledgeBaseTool(),
    "record_promise_to_pay": RecordPromiseToPayTool(),
    "send_payment_link": SendPaymentLinkTool(),
}


def get_collections_toolset() -> list:
    """Tools for a collections / EMI-recovery agent."""
    return [
        "check_loan_emi",
        "record_promise_to_pay",
        "send_payment_link",
        "search_knowledge_base",
        "schedule_callback",
        "transfer_to_human",
    ]

ALL_TOOL_NAMES = list(AVAILABLE_TOOLS.keys())

def get_tools_for_agent(tool_names: list) -> list:
    """Get tool instances for a list of tool names."""
    return [AVAILABLE_TOOLS[name] for name in tool_names if name in AVAILABLE_TOOLS]

def get_tool_schemas(tool_names: list) -> list:
    """Get tool schemas for function calling."""
    tools = get_tools_for_agent(tool_names)
    return [tool.to_schema() for tool in tools]

def get_default_toolset() -> list:
    """Return the default set of tool names for new agents.

    Excludes simulated tools (Aadhaar/PAN/GST/UPI verification, machine
    translation) so agents are not attached to fake-data tools by default.
    """
    return [
        "lookup_pincode",
        "check_loan_emi",
        "search_knowledge_base",
        "schedule_callback",
        "transfer_to_human",
    ]
