# Contributing

Thanks for your interest in Voise AI!

## Getting started

1. Fork the repo
2. Follow the [README](./README.md#quick-start) to get the platform running locally
3. Pick an open issue or propose a feature

## Development workflow

```bash
git checkout -b feature/your-feature
# Make changes
cd backend && pytest -v
cd frontend && npm run lint && npm run build
git commit -m "description of your change"
git push origin feature/your-feature
```

Then open a pull request on GitHub.

## Guidelines

- Keep PRs focused on a single concern
- Add tests for new functionality
- Update `.env.example` if you add new environment variables
- Follow existing code style (the repo has no strict formatter — match the surrounding code)
- For significant changes, open an issue first to discuss

## Telephony providers

If you're adding a new telephony provider (Vonage, Plivo, Telnyx, etc.), follow the pattern in `backend/app/services/telephony/`. Each provider implements a common interface.

## STT / TTS / LLM providers

Add new providers via `backend/app/services/stt/factory.py` or `backend/app/services/tts/factory.py`. For LiveKit agents, add them to `backend/livekit_agent.py`.

## Contact

Open a GitHub issue for questions or discussions.
