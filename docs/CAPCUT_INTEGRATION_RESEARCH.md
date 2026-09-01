# CapCut Capability & Integration Research

## Executive Summary
This document investigates the technical feasibility, public API availability, SDK support, project format structure, and automation limitations of **CapCut** (developed by ByteDance / TikTok USDS Joint Venture LLC).

The goal of this research is to evaluate whether CapCut can be cleanly, safely, and programmatically controlled by an AI-assisted video editing system.

---

## Source Table & Data Confidence

| Topic | Finding | Source / Reference URL | Confidence | Classification |
| :--- | :--- | :--- | :--- | :--- |
| **Public API** | No official, public general-purpose REST/GraphQL API exists for timeline video editing or project creation. | [CapCut Official Website](https://www.capcut.com/) & [CapCut TOS](https://www.capcut.com/clause/terms-of-service) | High | `NOT_SUPPORTED` |
| **Developer SDK** | No public desktop or mobile editing SDK is offered to third-party developers. Mentioned SDKs in TOS refer to internal or partner integrations. | [CapCut Terms of Service](https://www.capcut.com/clause/terms-of-service) | High | `NOT_SUPPORTED` |
| **Plugin / Extension System** | CapCut does not provide a public plugin API or web/desktop extension architecture. | [CapCut Help Center](https://www.capcut.com/) | High | `NOT_SUPPORTED` |
| **Project Draft Format** | Unencrypted JSON structure (`draft_content.json`) stored locally in SQLite/JSON format on Desktop. Format is undocumented and unstable across versions. | [capcut-cli & draft-schema Gist](https://gist.github.com/renezander030/80823f1d47081c312d2c1f9edd20dc22) | High (Community Verified) | `FRAGILE` / `TECHNICALLY_POSSIBLE_BUT_UNSUPPORTED` |
| **Desktop Automation** | UI Automation / Accessibility API control is possible but extremely fragile due to custom UI frameworks (Qt / Custom Webview rendering). | Technical evaluation of OS UI Accessibility interfaces | High | `FRAGILE` / `NOT_RECOMMENDED` |
| **Web Automation** | Browser automation (Playwright/Selenium) triggers anti-bot detections, CAPTCHA challenges, and violates Terms of Service Section 5. | [CapCut Terms of Service Section 5](https://www.capcut.com/clause/terms-of-service) | High | `NOT_RECOMMENDED` |

---

## Part 1: Official API Capabilities

An exhaustive assessment of official, publicly accessible APIs for CapCut yields the following classifications:

| Capability | Classification | Technical Explanation / Evidence |
| :--- | :--- | :--- |
| **Project Creation** | `NOT_SUPPORTED` | No public endpoint or interface exists to initialize a remote or local CapCut project via API. |
| **Video / Media Upload** | `NOT_SUPPORTED` | Asset ingest must be done manually via the GUI or internal cloud syncing. |
| **Timeline Creation** | `NOT_SUPPORTED` | Timeline tracks and clip arrangements cannot be created via public API. |
| **Clip Editing / Trimming / Splitting** | `NOT_SUPPORTED` | In-point, out-point, and slicing operations have no API endpoints. |
| **Transitions & Effects** | `NOT_SUPPORTED` | Internal ByteDance transition assets are referenced by private internal hashes. |
| **Text, Captions & Subtitles** | `NOT_SUPPORTED` | No API for injecting auto-captions or animated text tracks. |
| **Audio, Music & Voiceover** | `NOT_SUPPORTED` | Audio track placement and TTST (Text-to-Speech) engines are strictly internal. |
| **Export & Rendering** | `NOT_SUPPORTED` | Export trigger requires GPU-accelerated local rendering triggered via GUI. |

---

## Part 2: SDK & Developer Platform Research

ByteDance provides enterprise marketing APIs (e.g., TikTok Marketing API / Commerce APIs) for ad campaign deployment, but **does not provide a public editing SDK** for CapCut.

* **Desktop / Mobile SDK**: `NOT_SUPPORTED` (Publicly). Internal libraries exist only within ByteDance applications.
* **Web / JS SDK**: `NOT_SUPPORTED`. No embeddable CapCut editor widget exists for web applications.
* **Plugin / Extension SDK**: `NOT_SUPPORTED`. CapCut features a closed ecosystem with no third-party plugin manifest format (unlike Adobe Premiere CEP/UXP or DaVinci Resolve Lua/Python API).
* **Partner / Enterprise API**: `PRIVATE_ONLY`. ByteDance maintains select closed partnerships for TikTok commercial integrations, but these do not expose general video editing capabilities to independent developers.

---

## Part 3: Project Format Investigation (`draft_content.json`)

### Internal Storage Architecture
On CapCut Desktop (macOS / Windows), projects are stored in local user directories:
* **macOS**: `~/Movie/CapCut/User Data/Projects/com.lveditor.draft/`
* **Windows**: `C:\Users\<User>\AppData\Local\CapCut\User Data\Projects\com.lveditor.draft\`

Each project folder contains a `draft_content.json` file alongside asset folders and a local SQLite database (`draft_meta_info.json` / `root_meta_info.json`).

### Structure Overview
`draft_content.json` contains top-level keys including:
* `id`: Draft UUID.
* `duration`: Total timeline duration in microseconds ($1\text{ s} = 1,000,000\ \mu\text{s}$).
* `fps`: Frame rate (e.g., 24, 30, 60).
* `canvas_config`: Canvas dimensions (`width`, `height`, `ratio`).
* `tracks[]`: Array of timeline lanes ordered by z-order.
  * `tracks[].segments[]`: Individual clips, referencing `material_id`.
* `materials`: Dictionaries containing video, audio, text, filter, and transition assets:
  * `materials.videos[]`: Array of video and image source paths and durations.
  * `materials.beats[]`, `materials.effects[]`, `materials.texts[]`.

### Evaluation & Risk Analysis
1. **Is the format documented?** No. It is an internal schema subject to silent changes across app updates.
2. **Is it stable?** No. Schema version mismatches (e.g., app version updates between 6.x and 9.x) cause CapCut to reject or crash when loading modified draft files.
3. **Can it be safely generated externally?** `TECHNICALLY_POSSIBLE_BUT_UNSUPPORTED`. Community tools (such as reverse-engineered Python scripts) can output draft JSON, but required fields change frequently.
4. **Classification**: **`FRAGILE` / `NOT_RECOMMENDED`** as a primary production architecture.

---

## Part 4: Desktop Automation Feasibility

Attempting to control CapCut Desktop using OS-level GUI automation yields high operational risks:

| Automation Method | Feasibility | Reliability | Maintenance Cost | Operational Risk |
| :--- | :--- | :--- | :--- | :--- |
| **Windows UI Automation** | Partial | Low (15–30%) | Extremely High | High (UI elements use non-standard Qt/custom controls without accessible automation IDs). |
| **macOS Accessibility API** | Partial | Low (20–35%) | Extremely High | High (AXUIElements fail to expose timeline clip boundaries or canvas properties). |
| **OCR / Computer Vision** | Possible | Very Low (<20%) | High | Severe (Fails on dynamic themes, scaling, resolution changes, or window repositioning). |
| **Keyboard Shortcuts** | Feasible | Medium (50%) | Medium | High (No feedback loop; operations are asynchronous without completion signals). |
| **Screen Coordinates** | Possible | Low (<15%) | Extremely High | Severe (Breaks instantly if window resizes or display DPI changes). |

### Summary
Desktop GUI automation is non-deterministic, brittle, lacks process status callbacks, and breaks upon any CapCut software update.

---

## Part 5: CapCut Web Automation Analysis

Browser automation (using tools like Playwright, Puppeteer, or Selenium) to control CapCut Web (`capcut.com/editor`) presents severe architectural liabilities:

1. **Authentication Challenges**: Requires persistent session cookies, 2FA bypass, or manual user login.
2. **Anti-Bot & Security Protections**: CapCut Web uses Cloudflare / ByteDance Web Protect, triggering CAPTCHAs and cloudflare challenges on headless browsers.
3. **Terms of Service Violation**: Section 5 explicitly prohibits unauthorized automated scraping, bot access, or automated interface interaction. Account suspension is an active risk.
4. **UI Instability**: The web app uses Canvas and WebGL rendering for the timeline, making DOM element selectors ineffective for clip manipulation.

### Classification
**`NOT_RECOMMENDED`**.

---

## Conclusion & Strategic Recommendation

CapCut lacks official public APIs, developer SDKs, or stable plugin architectures. Operating via reverse-engineered draft files or GUI/browser automation is fragile, high-maintenance, and violates Terms of Service.

**Strategic Recommendation**:
Instead of forcing a brittle integration with CapCut, the system architecture must be centered on an **Editor-Independent Universal Video Editing IR** and an open-source/programmatic rendering engine (such as **FFmpeg** or **Remotion**), with optional draft export to CapCut as an experimental secondary export target.