"""Audio overview: LLM writes a two-host script, edge-tts reads it, ffmpeg assembles an MP3."""
import asyncio
import os
import re
import subprocess
from typing import List

import edge_tts
from openai import OpenAI

HOST_A = "en-US-JennyNeural"      # Host A
HOST_B = "en-US-ChristopherNeural"


def _llm():
    return OpenAI(
        base_url=os.getenv("LLM_BASE", "https://api.deepseek.com/v1"),
        api_key=os.getenv("LLM_KEY", ""),
    )


_SCRIPT_PROMPT = (
    "You are writing a podcast-style audio overview between two hosts (A and B) about the "
    "material below. Write exactly 10 to 16 alternating lines. Every single line MUST start with "
    "the speaker label followed by a colon, either \"A:\" or \"B:\", then their spoken sentence. "
    "Nothing else, no headers, no markdown. Example:\n"
    "A: Welcome back to our deep dive.\n"
    "B: Today we are unpacking the key ideas in this material.\n\n"
    "Material:\n{summary}\n"
)


def build_script(nb_title: str, summary_text: str) -> List[dict]:
    prompt = _SCRIPT_PROMPT.format(summary=summary_text[:6000])
    r = _llm().chat.completions.create(
        model=os.getenv("LLM_MODEL", "deepseek-v4-pro"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=2500,
        extra_body={"thinking": {"type": "disabled"}},
    )
    raw = r.choices[0].message.content or ""

    lines = []
    for ln in raw.splitlines():
        # strip markdown bold/bullets and leading whitespace
        m = re.match(r"^\s*(?:\*\*)?\s*(?:[-•*]\s*)?(host\s*[ab]|speaker\s*[ab]|[ab])\s*[:.)\-]\s*(?:\*\*)?\s*(.*)$", ln, re.I)
        if not m:
            continue
        speaker = m.group(1).lower()
        text = (m.group(2) or "").strip().rstrip("*")
        if not text:
            continue
        voice = HOST_A if speaker.endswith("a") or speaker == "a" else HOST_B
        lines.append({"voice": voice, "text": text})

    # Fallback: if no labeled lines parsed, alternate raw sentences between the two hosts.
    if not lines:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", raw) if s.strip()][:16]
        for i, s in enumerate(sentences):
            lines.append({"voice": HOST_A if i % 2 == 0 else HOST_B, "text": s})

    if not lines:
        raise RuntimeError("LLM produced no usable script lines")
    return lines


def _render(wav_dir: str, lines: List[dict]) -> List[str]:
    async def one(i, voice, text):
        out = f"{wav_dir}/part{i:03d}.mp3"
        await edge_tts.Communicate(text, voice).save(out)
        return out

    async def run():
        return await asyncio.gather(*(one(i, l["voice"], l["text"]) for i, l in enumerate(lines)))

    return asyncio.run(run())


def assemble(parts: List[str], out_mp3: str):
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", "concat:" + "|".join(parts), out_mp3],
        check=True,
    )


def render_audio(nb_id: str, nb_title: str, summary_text: str) -> str:
    data = os.getenv("DATA_DIR", "/data")
    nb_dir = os.path.join(data, "audio", nb_id)
    os.makedirs(nb_dir, exist_ok=True)
    parts = _render(nb_dir, build_script(nb_title, summary_text))
    out = os.path.join(nb_dir, "overview.mp3")
    assemble(parts, out)
    return out