# Voise AI SDK

Python client for the Voise AI voice agent platform API.

```python
from voise import VoiseClient

client = VoiseClient(base_url="http://localhost:8001", api_key="...")

# List agents
agents = client.agents.list()

# Trigger an outbound call
client.telephony.call(agent_id="...", to="+15551234567")

# Create a campaign
campaign = client.campaigns.create(name="Collections Q3", agent_id="...")
```
