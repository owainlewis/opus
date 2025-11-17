# LLM Provider Implementation Guide

This directory contains LLM provider implementations for Opus. All providers must implement the `LLMProvider` abstract base class defined in `base.py`.

## Critical Requirements

### ⚠️ MUST Use Async Clients

**All providers MUST use async API clients to avoid blocking the event loop.**

Using synchronous API clients will:
- Block the entire event loop during API calls
- Break UI elements like progress spinners
- Cause poor user experience and unresponsive behavior

### ✅ Correct Implementation

```python
from anthropic import AsyncAnthropic  # ✓ Async client

class MyProvider(LLMProvider):
    def _setup(self):
        self.client = AsyncAnthropic(api_key=self.api_key)  # ✓ Correct

    async def call(self, messages):
        response = await self.client.messages.create(...)  # ✓ Use await
        return response
```

### ❌ Incorrect Implementation

```python
from anthropic import Anthropic  # ✗ Sync client - DON'T USE

class MyProvider(LLMProvider):
    def _setup(self):
        self.client = Anthropic(api_key=self.api_key)  # ✗ Wrong!

    async def call(self, messages):
        response = self.client.messages.create(...)  # ✗ Blocks event loop!
        return response
```

## Common Async Clients

| Library | Sync Client (❌) | Async Client (✅) |
|---------|-----------------|-------------------|
| Anthropic | `Anthropic` | `AsyncAnthropic` |
| OpenAI | `OpenAI` | `AsyncOpenAI` |
| LiteLLM | `litellm.completion()` | `litellm.acompletion()` |

## What If No Async Client Exists?

If the SDK only provides a synchronous client (like Oracle OCI SDK), wrap the sync call with `asyncio.to_thread()`:

```python
import asyncio

class OracleProvider(LLMProvider):
    def _setup(self):
        # OCI SDK is sync-only
        self.client = GenerativeAiInferenceClient(...)

    async def call(self, messages):
        # Wrap sync call to avoid blocking
        response = await asyncio.to_thread(
            self.client.chat,
            chat_details
        )
        return response
```

## Built-in Validation

The base class includes automatic validation that will log a warning if it detects you're using a synchronous client. If you see this warning during development:

```
⚠️  Provider MyProvider may be using a synchronous client (Anthropic).
This can block the event loop and break UI elements like progress spinners.
```

**Fix it immediately** by switching to the async client!

## Example Providers

- `anthropic_provider.py` - Uses AsyncAnthropic
- `openai_provider.py` - Uses AsyncOpenAI
- `litellm_provider.py` - Uses litellm.acompletion()
- `oracle_provider.py` - Uses asyncio.to_thread() wrapper

## Testing Your Provider

When testing your provider, verify that:
1. Progress spinners continue to update during API calls
2. The UI remains responsive
3. No warnings appear about synchronous clients

## Questions?

See the base class documentation in `base.py` for detailed method signatures and requirements.
