---
name: video-shot-deconstruction
description: "Deconstruct/拉片 a video file, URL, or detailed video description into global analysis, core visual elements, shot-by-shot breakdown, and a production-ready Chinese AI video-generation config (core settings, scene, product, character, shots, audio)."
compatibility: "opencode"
metadata:
  language: "zh-CN"
  output_format: "markdown"
---

# Video Shot Deconstruction & AI Prompt Generation

## API Credentials Policy

When a video or image must be sent to an external multimodal model, do not start the model call automatically. First ask the user explicitly for:

1. The complete API base URL, for example `https://example.com/v1`.
2. The API Key.
3. The model name or endpoint ID, if it is not already specified.

Do not read `TOKENHUB_API_KEY`, `ARK_API_KEY`, `TOKENHUB_BASE_URL`, `ARK_BASE_URL`, or `ARK_MODEL_ID` from the environment. Do not reuse credentials supplied in a previous request. Do not place the user's Key in files, logs, reports, or generated prompts. If the user does not provide the URL and Key for the current request, do not call any external model.

This skill is for converting a video, video URL, or detailed video description into a professional short-video deconstruction report and AI-generation prompt set. It should behave like a senior short-video director, commercial photography analyst, and AI visual prompt engineer.

## When to Use

Use this skill when the user wants to:

- 对视频进行逐镜拉片、分镜拆解、镜头语言分析。
- 从视频中反推拍摄手法、景别、机位、运镜、光影、节奏。
- 将视频拆解成可复刻的 AI 视频/图像大模型中文提示词。
- 基于视频文件、视频链接，或一段详细的视频描述，输出结构化 Markdown 分析。
- 生成可进一步转成 JSON、自动化脚本、批量生图/生视频工作流的镜头提示词。

Do **not** use this skill for:

- 只做普通视频转写、简单摘要或字幕提取。
- 视频剪辑、转码、压缩、去水印等处理任务。
- 只做评分/投流策略诊断的任务；此类任务应使用评估类 skill。

## Runtime Options

If the user provides only a text description, execute the workflow directly from the description.

If the user provides a video file or URL and the runtime has access to a multimodal model, use the model to inspect the video. If using TokenHub-compatible Seed2.0, the helper script in `scripts/seed2.py` can be used.

### Required Confirmation Before Model Calls

Before every external model call, ask:

```text
请提供本次调用使用的 API Base URL、API Key，以及模型名或 Endpoint ID（如有）。
本次请求不会读取环境变量，也不会复用之前的 Key；未提供完整信息前不会调用模型。
```

Do not invent observations from an unreadable video. If the user declines or provides incomplete information, stop before making any network request.

## Directory Structure

```text
video-shot-deconstruction/
├── SKILL.md
├── references/
│   └── prompt-video-shot-deconstruction.md
└── scripts/
    └── seed2.py
```

## Recommended CLI Usage

For a local video file:

```bash
python3 scripts/seed2.py \
  --model doubao-seed-2-0-pro-260215 \
  --text-file references/prompt-video-shot-deconstruction.md \
  --video-file /path/to/video.mp4 \
  --fps 2 \
  --max-tokens 25600 \
  --base-url "<本次由用户提供的 API Base URL>" \
  --api-key "<本次由用户提供的 API Key>"
```

For a video URL:

```bash
python3 scripts/seed2.py \
  --model doubao-seed-2-0-pro-260215 \
  --text-file references/prompt-video-shot-deconstruction.md \
  --video-url "https://example.com/video.mp4" \
  --fps 2 \
  --max-tokens 25600 \
  --base-url "<本次由用户提供的 API Base URL>" \
  --api-key "<本次由用户提供的 API Key>"
```

To save a Markdown report directly as UTF-8 BOM:

```bash
python3 scripts/seed2.py \
  --model doubao-seed-2-0-pro-260215 \
  --text-file references/prompt-video-shot-deconstruction.md \
  --video-url "https://example.com/video.mp4" \
  --fps 2 \
  --max-tokens 25600 \
  --output-file /path/to/report.md
```

For a detailed text description, pass the description after the reference prompt:

```bash
python3 scripts/seed2.py \
  --model doubao-seed-2-0-pro-260215 \
  --text-file references/prompt-video-shot-deconstruction.md \
  --multi-line \
  --max-tokens 25600
```

## Core Workflow

Always follow the workflow in `references/prompt-video-shot-deconstruction.md` unless the user explicitly asks for a different output structure.

The required output has four sections:

1. **Step 1: 视频全局基因拆解 (Global Deconstruction)**  
   Extract duration, content type/positioning, core copy/voiceover, rhythm, global visual style, and BGM/SFX design.

2. **Step 2: 核心视觉元素前置拆解 (Core Elements Extraction)**  
   Define stable product/props, characters/actors, and scenes/environments before any shot-by-shot breakdown. These definitions are the source of truth for consistency.

3. **Step 3: 逐镜精细拉片 (Shot-by-Shot Breakdown)**  
   Break down the video by logical shots. Each shot must include shot number, visual content, cinematography, copy/duration, and must reference the stable elements from Step 2.

4. **Step 4: AI 提示词重构——工程化生产配置 (AI Production Config Generation)**  
   Reorganize the deconstruction into a production-ready config with six blocks: 【核心配置】negative prompt / video duration / aspect ratio, 【场景】reference assets / location, 【产品】reference images / must-show points, 【人物】reference images / character setup, 【镜头】each shot with a台词 (dialogue) line plus one pure-Chinese prompt wrapped in a Markdown code block under a `### Shot XX` heading, and 【音频】Voice / 读音备注 / BGM / SFX. Follow the exact template in `references/prompt-video-shot-deconstruction.md`. Output immediately without preamble or explanation between blocks.

## Output Requirements

- Output in Markdown.
- Use clear headings, tables, and numbered shots.
- Step 4 must follow the production-config template in `references/prompt-video-shot-deconstruction.md`: blocks 【核心配置】【场景】【产品】【人物】【镜头】【音频】, with `### Shot XX` headings, a台词 line before each shot, and **pure Chinese** prompts in code blocks.
- Each Step 4 shot prompt must include:
  - 主体一致性：把 Step 2 的角色、产品、场景设定放在提示词主语位置。
  - 极度写实与画质参数：如“极度写实、电影级光影、8K分辨率、单反实拍质感”。
  - 摄影与运镜术语：如“索尼威尼斯摄影机拍摄、85mm定焦镜头、缓慢向右平摇、浅景深”。
- The core config negative prompt must default to 【画面中不得出现任何可见字幕/花字/水印等】; shots must not render visible subtitles, on-screen text, or watermarks unless the source video itself contains such elements.
- In the audio block, include a 读音备注 field with correct pinyin for proper nouns (brand/product names) to prevent the video model from mispronouncing them.
- If a video is partially unreadable, state which observations are inferred from visible frames, audio, subtitles, or the user's description.
- Do not fabricate exact timestamps when only approximate timing is available; mark them as approximate.
- Maintain terminology suitable for short-video production and AI visual generation.

## Required Final Interaction

At the very end of every completed report, append the following question without changing its meaning:

> 💡 **提示：** 是否需要将以上拆解内容及提示词输出为 **JSON 格式**，以便您对接程序化脚本或自动化工作流？
