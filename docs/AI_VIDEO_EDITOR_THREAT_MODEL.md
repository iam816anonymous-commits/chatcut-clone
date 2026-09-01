# AI Video Editor Threat Model & Security Architecture

## Executive Summary
This document establishes the security, privacy, and safety threat model for the AI-assisted video editing system. It addresses risks associated with local media asset storage, LLM prompt injection, arbitrary command execution, authentication token theft, copyright issues, and cloud exposure.

---

## Local-First Security Principles

To maximize user privacy and safeguard media intellectual property, the system implements a **Local-First Architecture**:

1. **Local Media Storage**: All original video/audio assets remain on the user's local disk (`./workspace/media/`). Assets are never uploaded to cloud storage unless explicitly authorized by the user.
2. **Local AI Inference Option**: Supports local LLMs (e.g., via Ollama/vLLM) and local speech-to-text engines (Whisper.cpp) for complete offline privacy.
3. **Strict Path Sandboxing**: The execution engine enforces strict canonical directory checks (`/workspace/media/`, `/workspace/renders/`) to prevent path traversal attacks (`../`).

---

## Threat Matrix & Mitigation Strategies

| Threat Vector | Risk Description | Severity | Mitigation Architecture |
| :--- | :--- | :--- | :--- |
| **Path Traversal / Arbitrary File Access** | Malicious AI prompt or corrupted IR payload attempts to read sensitive OS files (e.g., `/etc/passwd` or `~/.ssh/id_rsa`) via FFmpeg input flags. | **CRITICAL** | Strict URL/path validation gate inside the Editing Validator layer. Whitelist input paths only within project sandboxes. |
| **Command / Shell Injection** | Subprocess execution of FFmpeg or CLI tools constructed via string concatenation allows arbitrary shell command injection. | **CRITICAL** | Never use `shell=True` or raw shell string interpolation. Use sanitized argument arrays (`subprocess.run(["ffmpeg", "-i", input_path, ...])`). |
| **Indirect Prompt Injection** | Embedded text in transcriptions or metadata tricks the LLM into executing unintended actions (e.g., "Delete all clips"). | **HIGH** | Strict JSON schema validation on LLM output. System instructions disallow destructive system commands; require human approval for deletions. |
| **Browser Credential Theft (If Automation Used)** | Exposing browser session cookies or OAuth tokens to headless automation scripts. | **HIGH** | Avoid browser automation entirely (CapCut Web automation rejected). Use local-first rendering backends. |
| **Biometric & Face Data Exposure** | Voiceover cloning and facial recognition data leaked to third-party cloud APIs. | **MEDIUM** | Process audio waveforms and facial detection locally using open-source models (Whisper, MediaPipe). |
| **Resource Exhaustion (DoS)** | Requesting infinite loop renders, multi-terabyte allocation, or 1000fps encoding that freezes user machine. | **HIGH** | Hard resource limits on render processes: max resolution (4K), max FPS (60), timeout thresholds, and disk space pre-checks. |

---

## Data Privacy Architecture

```text
  ┌────────────────────────────────────────────────────────┐
  │                    Local Machine                       │
  │                                                        │
  │  ┌───────────────┐   (Local Speech)   ┌─────────────┐  │
  │  │ User Video    │ ─────────────────► │ Whisper.cpp │  │
  │  │ Files         │                    └─────────────┘  │
  │  └───────┬───────┘                                     │
  │          │                                             │
  │          ▼ (Metadata Only: Durations, Transcript JSON)   │
  │  ┌──────────────────────────────────────────────────┐  │
  │  │ Sanitized Prompt & Metadata                      │  │
  │  └───────────────────────┬──────────────────────────┘  │
  └──────────────────────────┼─────────────────────────────┘
                             │
                             ▼ (Optional Cloud API Call)
                 ┌───────────────────────┐
                 │  LLM Provider         │
                 │  (JSON Response Only) │
                 └───────────────────────┘
```

### Privacy Guarantees
* **Media Neutrality**: Video pixels are **never sent to cloud LLM APIs**. Only text transcripts, duration markers, and spatial coordinates are transmitted in prompts.
* **Deterministic Output**: Cloud LLMs receive no executable code; they return JSON IR operations validated locally before execution.
* **Zero Telemetry Lock**: Opt-in telemetry logging only; zero tracking of private video content or filename paths.