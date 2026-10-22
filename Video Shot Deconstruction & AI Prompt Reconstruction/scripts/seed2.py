#!/usr/bin/env python3
"""TokenHub/火山方舟 Seed2.0 CLI helper for video/image/text multimodal analysis."""

import argparse
import base64
import json
import mimetypes
import sys

import requests


MAX_BODY_BYTES = 60 * 1024 * 1024  # 60MB


def print_text(text: str, end: str = "\n") -> None:
    sys.stdout.buffer.write((text + end).encode("utf-8"))
    sys.stdout.buffer.flush()


def file_to_data_url(path: str) -> str:
    with open(path, "rb") as f:
        raw = f.read()
    b64 = base64.b64encode(raw).decode("utf-8")
    mime_type, _ = mimetypes.guess_type(path)
    return f"data:{mime_type or 'application/octet-stream'};base64,{b64}"


def main() -> None:
    parser = argparse.ArgumentParser(description="TokenHub/火山方舟 Seed2.0 CLI")
    parser.add_argument("prompt", nargs="?", help="用户输入")
    parser.add_argument("--api-key", required=True, help="本次请求使用的 API Key；不会从环境变量读取")
    parser.add_argument("--base-url", required=True, help="本次请求使用的 API Base URL，例如 https://example.com/v1")
    parser.add_argument("--model", default="doubao-seed-2-0-lite-260215", help="模型名或 Endpoint ID")
    parser.add_argument("--system", "-s", help="System prompt")
    parser.add_argument("--stream", "-S", action="store_true", help="流式输出")
    parser.add_argument("--temperature", "-t", type=float, default=0.7, help="温度，默认 0.7")
    parser.add_argument("--max-tokens", "-m", type=int, default=25600, help="最大 token 数，默认 25600")
    parser.add_argument("--multi-line", "-M", action="store_true", help="多行输入，Ctrl+D 结束")
    parser.add_argument("--video-url", help="视频 URL")
    parser.add_argument("--video-file", help="本地视频文件；将以 base64 data URL 发送，请求体不超过 60MB")
    parser.add_argument("--fps", type=int, default=2, help="视频抽帧频率，默认 2")
    parser.add_argument("--image-url", help="图片 URL")
    parser.add_argument("--image-file", help="本地图片文件；将以 base64 data URL 发送，请求体不超过 60MB")
    parser.add_argument("--text-file", help="从文件读取 prompt")
    parser.add_argument("--output-file", help="将非流式响应写入 UTF-8 BOM 文件")

    args = parser.parse_args()

    api_key = args.api_key
    model = args.model
    chat_endpoint = f"{args.base_url.rstrip('/')}/chat/completions"

    prompt = args.prompt
    if args.text_file:
        with open(args.text_file, encoding="utf-8") as f:
            prompt = f.read()
    elif not prompt and args.multi_line:
        print("请输入内容，Ctrl+D 结束:", file=sys.stderr, end=" ", flush=True)
        prompt = sys.stdin.read()

    has_video = bool(args.video_url or args.video_file)
    has_image = bool(args.image_url or args.image_file)
    if not prompt and not has_video and not has_image:
        print("错误: 请输入 prompt 或提供视频/图片", file=sys.stderr)
        sys.exit(1)

    messages = []
    if args.system:
        messages.append({"role": "system", "content": args.system})

    if has_video or has_image:
        content = []
        if has_video:
            url = args.video_url if args.video_url else file_to_data_url(args.video_file)
            content.append({"type": "video_url", "video_url": {"url": url}, "fps": str(args.fps)})
        if has_image:
            url = args.image_url if args.image_url else file_to_data_url(args.image_file)
            content.append({"type": "image_url", "image_url": {"url": url}})
        if prompt:
            content.append({"type": "text", "text": prompt})
        messages.append({"role": "user", "content": content})
    else:
        messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "stream": args.stream,
    }

    body = json.dumps(payload, ensure_ascii=False)
    if len(body.encode("utf-8")) > MAX_BODY_BYTES:
        print("错误: 请求体超过 60MB 限制，请压缩文件或改用视频 URL", file=sys.stderr)
        sys.exit(1)

    if args.stream:
        resp = requests.post(chat_endpoint, headers=headers, json=payload, stream=True, timeout=300)
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data = line[6:].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if content:
                        print_text(content, end="")
                except json.JSONDecodeError:
                    continue
        print_text("")
    else:
        resp = requests.post(chat_endpoint, headers=headers, json=payload, timeout=300)
        try:
            resp.raise_for_status()
        except requests.HTTPError:
            print(f"错误: 接口请求失败，状态码 {resp.status_code}: {resp.text[:500]}", file=sys.stderr)
            raise
        try:
            result = resp.json()
        except json.JSONDecodeError:
            print(f"错误: 接口返回非 JSON 内容，状态码 {resp.status_code}: {resp.text[:500]}", file=sys.stderr)
            sys.exit(1)
        content = result["choices"][0]["message"]["content"]
        if args.output_file:
            with open(args.output_file, "w", encoding="utf-8-sig", newline="\n") as f:
                f.write(content)
                f.write("\n")
        else:
            print_text(content)


if __name__ == "__main__":
    main()
