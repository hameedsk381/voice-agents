# 🎙️ Qwen vs. ElevenLabs: Strategic Gap Analysis

This document analyzes the current state of our **Qwen-based** voice stack compared to industry leader **ElevenLabs**, focusing on how we can bridge the quality gap while staying on our own infrastructure.

---

## 🔍 Core Benchmark: Qwen (Current) vs. ElevenLabs

| Capability | Qwen3-TTS (v2.1) | ElevenLabs (Turbo v2.5) | Strategy to Bridge |
| :--- | :--- | :--- | :--- |
| **Latency** | ~100-200ms (High Speed) | ~400ms (Slower) | **Win**: We already beat them in raw speed. |
| **Emotional Depth** | Neutral / Professional | High (Laughs, Cries, Whispers) | **Fine-tuning**: Implement "Instruct" based style transfers in Qwen. |
| **Multilingual** | Moderate (Lang switches) | Seamless (29+ Languages) | **Unified Embedding**: Adopt cross-lingual voice embeddings. |
| **Availability** | Local / Self-hosted | Cloud / Pay-per-char | **Privacy**: We win on data sovereignty & cost control. |

---

## 🚧 Gap 1: Contextual Prosody (The "Robotic" Feel)
*   **The Problem:** Qwen synthesizes each sentence independently. It doesn't know the "mood" of the conversation.
*   **ElevenLabs Edge:** They use a large context window to maintain tone across a paragraph.
*   **Our Solution:** Pass "Conversation Sentiment" as an `instruct` tag to the Qwen synthesis engine (Already partially implemented in our `Orchestrator`).

## 🚧 Gap 2: Non-Verbal Artifacts
*   **The Problem:** Our Qwen model doesn't handle filler words ("um," "ah") or emotional sounds naturally.
*   **Our Solution:** Implement a lightweight "Backchanneling" layer that plays pre-rendered audio cues (gasps, nods) while the LLM is thinking.

## 🚧 Gap 3: Voice Consistency (Cloning)
*   **The Problem:** Zero-shot cloning in Qwen can sometimes lose the "texture" of the voice under stress.
*   **Our Solution:** Move from Zero-shot to **few-shot fine-tuning** for enterprise clients who need perfect voice identity.

---

## 🏆 Decision: Why We Stick with Qwen
1.  **Latency**: Our <200ms TTFA is critical for seamless "barge-in" conversations. ElevenLabs creates a noticeable lag that breaks user immersion in interactive phone calls.
2.  **Cost Sovereignty**: We pay $0 per character. Scaling to 1M minutes on ElevenLabs would be prohibitive.
3.  **Data Security**: No user audio ever leaves our VPC, a non-negotiable requirement for our BFSI and Healthcare clients.

---

## 🛠️ Roadmap to "ElevenLabs Quality" on Qwen
1.  **Sentiment-Injection**: Deeply integrate our `PolicyEngine`'s sentiment analysis with Qwen's `instruct` tags.
2.  **Sentence Overlapping**: Implement "Look-ahead synthesis" where sentence $(n+1)$ starts synthesizing before sentence $(n)$ finishes playing.
3.  **Refined Cloner**: Upgrade our internal `Voices` API to support tiered cloning (Speed vs. Quality).
