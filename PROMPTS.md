# Best Prompt: Generate Your Own Jetson Setup

Use this as a starting prompt for your assistant:

"I have a Jetson Orin Nano Super 8GB running JetPack 6.2. I want a production local LLM setup optimized for coding + tool calling with minimum 8 tok/s generation. Keep host clean (container-only runtime), provide safe reviewable bash scripts (no curl-bash), include benchmark harness, and explain every design tradeoff with memory math and fallback profiles. Output: startup scripts, systemd unit, benchmark procedure, and troubleshooting matrix."

Maintainer workflow note:
- This project was iterated using **Opus 4.6 High with GitHub Copilot**.
