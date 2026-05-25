# Voise AI — Architecture Graphs

> **Workflow automation (Phase 1 & 2 — done):** see [WORKFLOW_AUTOMATION.md](./WORKFLOW_AUTOMATION.md) for implementation details, API, and operations.

```mermaid
---
title: System Architecture Layers
---
graph TB
    subgraph Clients ["Clients"]
        direction LR
        WEB[Web Browser\nNext.js Frontend]
        PHONE[Phone / SIP\nTwilio / Exotel]
        API[REST / WS\nExternal Integrations]
    end

    subgraph FastAPI ["FastAPI Backend (:8001)"]
        direction TB
        GATEWAY[API Gateway\nmain.py]
        
        subgraph REST ["REST Endpoints"]
            AUTH[/auth/*/]
            AGENTS[/agents/*/]
            CAMPAIGNS[/campaigns/*/]
            WORKFLOWS[/workflows/*/]
            ANALYTICS[/analytics/*/]
            HITL[/hitl/*/]
            MEMORY[/memory/*/]
            KNOWLEDGE[/knowledge/*/]
            TELEPHONY[/telephony/*/]
            MARKETPLACE[/marketplace/*/]
            MONITORING[/monitoring/*/]
            VOICES[/voices/*/]
        end

        subgraph WS ["WebSocket Endpoints"]
            WS_AGENT[ws /orchestrator/ws/{agent_id}]
            WS_MONITOR[ws /monitoring/stream/{session_id}]
            WS_GLOBAL[ws /monitoring/stream/all]
            WS_TELEPHONY[ws /telephony/ultravox-data]
        end

        subgraph Orchestration ["Orchestration Layer"]
            ORCH[AgentOrchestrator\nsentiment · confidence · escalation · self-correction]
            SWARM[SwarmOrchestrator\nLLM agent routing · autonomous discovery]
            LANGGRAPH[LangGraphOrchestrator\nStateGraph · specialist nodes]
            POLICY[PolicyEngine\nstate machine · guardrails · script enforcement]
            PLANNER[ToolPlanner\nplan before call · sequencing]
            SESSION[SessionManager\nRedis persistence · 24h TTL]
        end

        subgraph Services ["Service Layer"]
            LLM[LLM Providers\nGroq · OpenAI · Enterprise failover]
            TTS[TTS Providers\nQwen · Deepgram · Mock]
            STT[STT Providers\nDeepgram · Mock]
            TOOLS[Tool Registry\n8 tools · MCP client]
            MEMSVC[Memory Service\nmemorize · retrieve · summarize]
            COMPLIANCE[Compliance Service\nPII redaction · LLM audit]
            SHADOW[Shadow Comparison\nprimary vs cheap model]
            HITLSVC[HITL Service\npending actions · intervention]
            ANALYTICSSVC[Analytics Service\nstats · HMAC signing]
            KNOWLEDGESVC[Knowledge Service\nRAG · embeddings]
            WFENG[WorkflowEngine\nin-app automation v1]
            WFSVC[WorkflowService\nCRUD · instances · SAP ingest]
            EMAILSVC[EmailService\nSMTP or simulated]
            ULTRAVOX[Ultravox Service\nproxy voice runtime]
            VOICEUX[Voice UX Service\nbackchannels · fillers]
        end
    end

    subgraph Infra ["Infrastructure"]
        PG[(PostgreSQL\npgvector)]
        REDIS[(Redis\nsession · Pub/Sub)]
        TEMPORAL[Temporal\nworkflow orchestration]
    end

    subgraph External ["External Services"]
        GROQ[Groq Cloud\nLLM · llama-3.3-70b]
        DEEPGRAM[Deepgram\nSTT · TTS]
        OPENAI[OpenAI\nGPT-3.5-turbo]
        QWEN[Qwen3-TTS\nlocalhost:8008]
        ULTRAVOX_API[Ultravox API\nvoice calls]
        TWILIO[Twilio\ntelephony]
    end

    WEB -->|HTTP / WS| GATEWAY
    PHONE -->|SIP / Webhook| TELEPHONY
    API -->|HTTP| GATEWAY

    GATEWAY --> REST
    GATEWAY --> WS

    WS_AGENT --> ORCH
    WS_MONITOR --> MONITORING
    WS_GLOBAL --> MONITORING
    WS_TELEPHONY --> ULTRAVOX

    ORCH --> SWARM
    ORCH --> LANGGRAPH
    ORCH --> POLICY
    ORCH --> PLANNER
    ORCH --> SESSION
    ORCH --> LLM
    ORCH --> MEMSVC
    ORCH --> TOOLS
    ORCH --> KNOWLEDGESVC

    SESSION --> REDIS
    MEMSVC --> REDIS
    
    LLM --> GROQ
    LLM --> OPENAI
    TTS --> QWEN
    TTS --> DEEPGRAM
    STT --> DEEPGRAM
    ULTRAVOX --> ULTRAVOX_API
    TELEPHONY --> TWILIO

    REST --> WFENG
    REST --> WFSVC
    WFSVC --> WFENG
    WFENG --> EMAILSVC
    WFENG --> CAMP_SVC[CampaignService\ndial on voice_call]
    REST --> PG
    REST --> REDIS
    SERVICES --> PG
    HITL --> REDIS
```

```mermaid
---
title: Voice Session Lifecycle
---
sequenceDiagram
    participant User as Caller
    participant WS as WebSocket
    participant Sentiment as Sentiment Tracker
    participant Policy as PolicyEngine
    participant Agent as AgentOrchestrator
    participant Memory as MemoryService
    participant LLM as EnterpriseLLM
    participant Tools as ToolPlanner
    participant Comp as ComplianceValidator
    participant TTS as TTS Provider
    participant Audit as AuditLog

    User->>WS: Audio / Transcript
    WS->>Sentiment: Update slope
    Sentiment-->>WS: Moving average
    
    alt Fast Path
        WS->>WS: Respond with cached greeting
    end

    alt HITL Takeover Mode
        WS->>Redis: Read human response
        Redis-->>WS: Human text
    end

    WS->>Policy: Validate input
    Policy-->>WS: Allowed + next state

    alt Swarm Mode
        WS->>Agent: route_task()
        Agent->>Swarm: Select specialist
        Swarm-->>WS: Agent role
    end

    WS->>Memory: get_context_for_call()
    Memory-->>WS: User profile + history

    WS->>LLM: generate_response()
    LLM-->>WS: Response text

    alt Tool Needed
        WS->>Tools: generate_plan()
        Tools-->>WS: Plan statement + tool calls
        WS->>Tools: execute_tool()
        Tools-->>WS: Tool result
    end

    WS->>Policy: Validate response
    Policy-->>WS: Enforced / blocked / escalated

    alt Low Confidence
        WS->>Agent: reflect_and_correct()
        Agent-->>WS: Corrected response
    end

    alt Escalation Needed
        WS->>Agent: should_escalate()
        Agent-->>WS: Escalate to human
    end

    WS->>TTS: synthesize_stream()
    TTS-->>WS: Audio chunks
    WS-->>User: text_chunk + audio_chunk

    par Compliance Audit
        WS->>Comp: validate_turn()
        Comp-->>Audit: Log violation
    end

    par Shadow Comparison
        WS->>Shadow: compare_turn()
        Shadow-->>ShadowLog: Store comparison
    end

    alt Post-Call
        WS->>Memory: summarize_conversation()
        WS->>Memory: memorize_from_conversation()
        WS->>Analytics: log_call_completion()
    end
```

```mermaid
---
title: Database Entity Relationships
---
erDiagram
    Organization ||--o{ Agent : has
    Organization ||--o{ User : has
    Organization ||--o{ MemoryItem : owns
    Organization ||--o{ CallLog : owns
    Organization ||--o{ Campaign : owns
    Organization ||--o{ AuditLog : owns

    Agent ||--o{ AgentVersion : versions
    Agent ||--o{ AgentKnowledge : knowledge
    Agent ||--o{ CallLog : participates
    Agent ||--o{ Campaign : assigned
    Agent ||--o{ ConversationSummary : summarized

    Campaign ||--o{ CampaignContact : contains
    Campaign }o--|| Agent : uses
    Campaign }o--o| Workflow : optional_automation

    Workflow ||--o{ WorkflowInstance : runs
    WorkflowInstance }o--o| Campaign : optional
    WorkflowInstance }o--o| CampaignContact : optional
    WorkflowInstance ||--o{ EmailMessage : may_send

    User ||--o{ PendingAction : processes
    User ||--o{ SessionIntervention : controls
    User ||--o{ Campaign : creates

    CallLog }o--|| Agent : belongs_to
    CallLog }o--o| Campaign : optional
    CallLog ||--o{ AuditLog : audited
    CallLog ||--o{ ShadowLog : shadowed

    MemoryItem }o--|| UserProfile : belongs_to
    UserProfile ||--o{ ConversationSummary : has

    SessionIntervention ||--|| CallLog : intervenes_in
    PendingAction ||--|| CallLog : targets

    AuditLog }o--|| CallLog : references
    ShadowLog }o--|| CallLog : references
```

```mermaid
---
title: Frontend Page Structure
---
graph TB
    subgraph Public ["Public Routes"]
        LANDING["/ — Landing\nHero · Features · CTA"]
        LOGIN["/login\nEmail/password login"]
        REGISTER["/register\nRegistration form"]
    end

    subgraph Dashboard ["/dashboard — Auth Required"]
        OVERVIEW["/ — Overview\nStats cards · trend chart · shadow model"]
        
        subgraph Agents ["Agents"]
            AGENTS["/agents\nList + create modal"]
            AGENT["/agents/[id]\nConfig · Playground · Knowledge Base"]
        end

        subgraph Campaigns ["Campaigns"]
            CAMP_LIST["/campaigns\nList with progress cards"]
            CAMP_NEW["/campaigns/new\nCreate + workflow picker"]
            CAMP_DETAIL["/campaigns/[id]\nCSV upload · start/pause · stats"]
        end

        subgraph Workflows ["Workflows ✅ Ph1+2"]
            WF_LIST["/workflows\nList · templates"]
            WF_NEW["/workflows/new\nFrom template"]
            WF_EDIT["/workflows/[id]\nVisual · JSON · SAP · Test"]
        end

        subgraph Monitoring ["Monitoring"]
            MON_LIST["/monitoring\nActive sessions (5s poll)"]
            MON_SESSION["/monitoring/[id]\nLive WS transcript · decision trace"]
        end

        subgraph Misc ["Other"]
            VOICES["/voices\nVoice Lab · Gallery · Designer · Cloner"]
            SETTINGS["/settings\nTelephony · Profile · Compliance · Billing · Appearance"]
            MARKETPLACE["/marketplace\nAgent templates · install"]
            LOGS["/logs\nCall log table · detail panel"]
            APPROVALS["/approvals\nHITL pending · approve/reject"]
            ANALYTICS["/analytics\nCharts · agent performance"]
        end
    end

    LANDING --> LOGIN
    LANDING --> REGISTER
    LOGIN --> OVERVIEW
    REGISTER --> OVERVIEW
```

```mermaid
---
title: Key Data Flows
---
flowchart LR
    subgraph Inbound-Call ["Inbound Call Flow"]
        A1[Phone Rings] --> A2[Twilio Webhook\n/telephony/voice]
        A2 --> A3{Ultravox?\nUSE_ULTRAVOX_RUNTIME}
        A3 -->|Yes| A4[Ultravox Proxy\nhandles real-time]\n
        A3 -->|No| A5[Self-Hosted WS\nSTT + LLM + TTS]
        A5 --> A6[Agent Response]
        A4 --> A6
    end

    subgraph RAG-Flow ["RAG Knowledge Flow"]
        B1[Agent Knowledge\nCRUD API] --> B2[(PostgreSQL\npgvector)]
        B3[User Query] --> B4[Embedding\nall-MiniLM-L6-v2]
        B4 --> B5[Cosine Search\nagent_knowledge]
        B5 --> B6[Relevant Chunks\n→ LLM Context]
        B2 --> B5
    end

    subgraph Memory-Flow ["Memory Flow"]
        C1[Conversation] --> C2[LLM Extraction\nmemorize_from_conversation]
        C2 --> C3{Consent Check\nuser_claim detection}
        C3 -->|Granted| C4[Store MemoryItem\nwith embedding]
        C3 -->|Withdrawn| C5[Skip]
        C4 --> C6[Future Calls\nget_context_for_call]
    end

    subgraph Compliance-Flow ["Compliance Flow"]
        D1[User Input] --> D2[PolicyEngine\nintent + guardrails]
        D2 --> D3[State Machine\nGREETING → DATA_COLLECTION...]
        D3 --> D4[LLM Response]
        D4 --> D5[PolicyEngine\nscript + output guardrails]
        D5 --> D6[ComplianceValidator\nshadow LLM audit]
        D6 --> D7[(AuditLog\nrisk_score + violations)]
    end
```

```mermaid
---
title: Tool System Architecture
---
graph TB
    subgraph Tool-Planner ["Tool Planning"]
        TP[ToolPlanner\nllama-3.3-70b] -->|Analyze input| PLAN{Plan}
        PLAN -->|"I'll check your order first"| PLAN_STMT[Plan Statement\nspoken to user]
        PLAN -->|Tool sequence| CALLS[Tool Calls\nin order]
    end

    subgraph Tool-Registry ["Tool Registry"]
        ORDER[GetOrderStatusTool\norder_id → status]
        BALANCE[CheckAccountBalanceTool\naccount_id → balance]
        SCHEDULE[ScheduleCallbackTool\ntime + reason → confirmation]
        TRANSFER[TransferToHumanTool\nreason → escalation]
        WEB_SEARCH[WebSearchTool\nquery → search results]
        REFUND[RefundCustomerTool\nrequires supervisor approval]
        KNOWLEDGE[SearchKnowledgeTool\nquery → RAG results]
        PROFILE[UpdateProfileTool\nuser_id + data → updated profile]
    end

    subgraph MCP ["External MCP Servers"]
        MCP_CLIENT[MCPClient\nModel Context Protocol]
        EXT1[CRM Server\ntools]
        EXT2[Payment Server\ntools]
        EXT3[Custom Server\nany MCP-compatible]
    end

    TP --> Tool-Registry
    Tool-Registry --> ORDER
    Tool-Registry --> BALANCE
    Tool-Registry --> KNOWLEDGE
    
    REFUND -->|approval gate| HITL[PendingAction\nsupervisor must approve]
    TRANSFER --> HITL
    
    Tool-Registry --> MCP_CLIENT
    MCP_CLIENT --> EXT1
    MCP_CLIENT --> EXT2
    MCP_CLIENT --> EXT3
```

```mermaid
---
title: In-App Workflow Automation (Phase 1 & 2 — Done)
---
flowchart TB
    subgraph Triggers ["Triggers"]
        T1[Campaign start\nworkflow_id set]
        T2[SAP CSV ingest\nPOST /workflows/ingest/sap-csv]
        T3[Manual test instance\nPOST /instances]
        T4[Cron / Temporal activity\nPOST /process-due]
    end

    subgraph Engine ["WorkflowEngine"]
        N1[condition]
        N2[voice_call → CampaignService.dial]
        N3[wait → wait_until]
        N4[email → EmailService]
        N5[hitl_approval → PendingAction]
        N6[escalate / end]
    end

    subgraph Store ["PostgreSQL"]
        WI[(workflow_instances)]
        EM[(email_messages)]
    end

    T1 --> WI
    T2 --> WI
    T3 --> WI
    T4 --> WI
    WI --> Engine
    N4 --> EM
```

See [WORKFLOW_AUTOMATION.md](./WORKFLOW_AUTOMATION.md) for API and operations.
