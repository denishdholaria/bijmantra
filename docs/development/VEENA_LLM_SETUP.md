# Veena AI - LLM Setup Guide

> **Making Veena intelligent for everyone, including students in developing countries**

Veena supports multiple LLM providers with automatic fallback. You only need to configure ONE provider for intelligent responses.

## Quick Start (Recommended Options)

### Option 1: Ollama (Local, FREE, Private) ⭐ RECOMMENDED

Best for: Students, researchers who want privacy, offline use

**Requirements:** 8GB RAM, ~4GB disk space

```bash
# 1. Install Ollama
# macOS/Linux:
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: Download from https://ollama.ai

# 2. Pull a small, fast model
ollama pull llama3.2:3b    # 2GB, good quality
# OR for better quality (needs 8GB+ RAM):
ollama pull llama3.1:8b    # 4.7GB, excellent quality

# 3. Ollama runs automatically on http://localhost:11434
```

**Configuration (.env):**
```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

---

### Option 2: Groq (Cloud, FREE tier) ⭐ FAST

Best for: Fast responses, no local setup needed

**Free tier:** 30 requests/minute (enough for personal use)

```bash
# 1. Get free API key from https://console.groq.com
# 2. Add to .env:
```

**Configuration (.env):**
```env
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

---

### Option 3: Google AI Studio (Cloud, FREE tier)

Best for: Good quality, generous free tier

**Free tier:** 60 requests/minute

```bash
# 1. Get free API key from https://aistudio.google.com
# 2. Add to .env:
```

**Configuration (.env):**
```env
GOOGLE_AI_KEY=your_key_here
GOOGLE_MODEL=gemini-1.5-flash
```

---

## All Provider Options

| Provider | Cost | Speed | Quality | Privacy | Setup |
|----------|------|-------|---------|---------|-------|
| **Ollama** | FREE | Fast | Good | ✅ Local | Install app |
| **Groq** | FREE tier | Very Fast | Excellent | Cloud | Get API key |
| **Google AI** | FREE tier | Fast | Very Good | Cloud | Get API key |
| **HuggingFace** | FREE tier | Slow | Good | Cloud | Get API key |
| **OpenAI** | Paid | Fast | Excellent | Cloud | Get API key |
| **Anthropic** | Paid | Fast | Excellent | Cloud | Get API key |

---

## Detailed Setup Instructions

### Ollama (Local)

Ollama lets you run LLMs locally on your computer. No internet needed after setup.

**Recommended Models:**

| Model | Size | RAM Needed | Quality | Speed |
|-------|------|------------|---------|-------|
| `llama3.2:3b` | 2GB | 8GB | Good | Fast |
| `llama3.1:8b` | 4.7GB | 16GB | Excellent | Medium |
| `phi3:mini` | 2.3GB | 8GB | Good | Fast |
| `gemma2:2b` | 1.6GB | 8GB | Good | Very Fast |
| `mistral:7b` | 4.1GB | 16GB | Excellent | Medium |

**Installation:**

```bash
# macOS
brew install ollama
# OR
curl -fsSL https://ollama.ai/install.sh | sh

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download installer from https://ollama.ai
```

**Pull a model:**
```bash
# For 8GB RAM laptops:
ollama pull llama3.2:3b

# For 16GB+ RAM:
ollama pull llama3.1:8b
```

**Test it works:**
```bash
ollama run llama3.2:3b "Hello, what is plant breeding?"
```

---

### Groq (Free Cloud)

Groq offers extremely fast inference with a generous free tier.

1. Go to https://console.groq.com
2. Sign up (free)
3. Create an API key
4. Add to your `.env` file:

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.1-8b-instant
```

**Available Models:**
- `llama-3.1-8b-instant` - Fast, good quality
- `llama-3.1-70b-versatile` - Best quality (slower)
- `mixtral-8x7b-32768` - Good for long context

---

### Google AI Studio (Free Cloud)

Google offers Gemini models with a generous free tier.

1. Go to https://aistudio.google.com
2. Sign in with Google account
3. Get API key from "Get API Key" button
4. Add to your `.env` file:

```env
GOOGLE_AI_KEY=AIzaSyxxxxxxxxxxxxxxxxxx
GOOGLE_MODEL=gemini-1.5-flash
```

**Available Models:**
- `gemini-1.5-flash` - Fast, good quality (recommended)
- `gemini-1.5-pro` - Best quality (slower)

---

### HuggingFace (Free Cloud)

HuggingFace offers free inference API with rate limits.

1. Go to https://huggingface.co/settings/tokens
2. Create a token (free)
3. Add to your `.env` file:

```env
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxxxxxxxxx
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.2
```

**Note:** HuggingFace free tier can be slow and has rate limits.

---

## Troubleshooting

### Veena shows "No LLM configured"

1. Check if at least one provider is configured in `.env`
2. Restart the backend server
3. Check `/api/v2/chat/status` endpoint

### Ollama not connecting

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it:
ollama serve
```

### API key errors

- Make sure there are no extra spaces in your API key
- Check the key is valid at the provider's dashboard
- Some providers require billing info even for free tier

### Slow responses

- Try a smaller model (e.g., `llama3.2:3b` instead of `llama3.1:8b`)
- Use Groq for fastest cloud responses
- Check your internet connection for cloud providers

---

## For Institutions

If you're setting up Bijmantra for a university or research institute:

1. **Recommended:** Set up a shared Ollama server
   - Install Ollama on a server with GPU
   - Configure `OLLAMA_HOST=http://your-server:11434`
   - All users connect to the same server

2. **Alternative:** Get institutional API keys
   - Many providers offer educational discounts
   - OpenAI and Anthropic have research programs

---

## Environment Variables Reference

```env
# === LOCAL (FREE) ===
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# === FREE CLOUD ===
GROQ_API_KEY=gsk_xxx
GROQ_MODEL=llama-3.1-8b-instant

GOOGLE_AI_KEY=AIzaSyxxx
GOOGLE_MODEL=gemini-1.5-flash

HUGGINGFACE_API_KEY=hf_xxx
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.2

# === PAID (Optional) ===
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o-mini

ANTHROPIC_API_KEY=sk-ant-xxx
ANTHROPIC_MODEL=claude-3-haiku-20240307

# === FORCE PROVIDER (Optional) ===
# VEENA_LLM_PROVIDER=ollama
```

---

## Priority Order

Veena automatically selects the best available provider:

1. **Ollama** (if running locally)
2. **Groq** (if API key configured)
3. **Google AI** (if API key configured)
4. **HuggingFace** (if API key configured)
5. **OpenAI** (if API key configured)
6. **Anthropic** (if API key configured)
7. **Template fallback** (always works, limited responses)

You can force a specific provider with `VEENA_LLM_PROVIDER=provider_name`.
