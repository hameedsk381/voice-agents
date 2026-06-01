# Voise AI — TypeScript SDK

```typescript
import { VoiseClient } from "voise";

const client = new VoiseClient({
  baseUrl: "http://localhost:8001",
  apiKey: "your-api-key",
});

// List agents
const agents = await client.agents.list();

// Trigger an outbound call
await client.telephony.call({ agentId: "...", to: "+15551234567" });

// Create a campaign
const campaign = await client.campaigns.create({
  name: "Collections Q3",
  agentId: "...",
});
```
