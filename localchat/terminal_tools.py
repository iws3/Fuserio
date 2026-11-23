import getpass
import os
import platform
import re
from pathlib import Path

from localchat.models import MODEL_OPTIONS, ModelOption


def memory_info_gb() -> tuple[float | None, float | None]:
    total_kb = None
    available_kb = None
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition(":")
            if key == "MemTotal":
                total_kb = int(value.split()[0])
            elif key == "MemAvailable":
                available_kb = int(value.split()[0])
    except (OSError, ValueError):
        if hasattr(os, "sysconf"):
            try:
                total_kb = (
                    os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") // 1024
                )
            except (OSError, ValueError):
                pass

    to_gb = lambda value: round(value / 1_048_576, 1) if value is not None else None
    return to_gb(total_kb), to_gb(available_kb)


def system_report() -> str:
    total_memory, available_memory = memory_info_gb()
    memory_line = (
        f"{total_memory:.1f} GB total; {available_memory:.1f} GB available"
        if total_memory is not None and available_memory is not None
        else f"{total_memory:.1f} GB total" if total_memory is not None else "unavailable"
    )
    return "\n".join(
        (
            "**Local system**",
            f"- User: `{getpass.getuser()}`",
            f"- OS: `{platform.platform()}`",
            f"- CPU architecture: `{platform.machine() or 'unknown'}`",
            f"- Physical memory: `{memory_line}`",
            f"- Working directory: `{Path.cwd()}`",
        )
    )


def run_read_only_command(command: str) -> str | None:
    normalized = command.strip().lower()
    if normalized == "pwd":
        return str(Path.cwd())
    if normalized == "whoami":
        return getpass.getuser()
    if normalized == "uname":
        return platform.platform()
    if normalized in {"free", "free -h", "sysinfo", "system"}:
        return system_report()
    if normalized in {"ls", "dir"}:
        try:
            entries = sorted(Path.cwd().iterdir(), key=lambda entry: (not entry.is_dir(), entry.name.lower()))
        except OSError as error:
            return f"Cannot list the current directory: {error}"
        visible = [f"{entry.name}/" if entry.is_dir() else entry.name for entry in entries[:60]]
        suffix = f"\n... {len(entries) - 60} more entries" if len(entries) > 60 else ""
        return "\n".join(visible) + suffix if visible else "(empty directory)"
    return None


def model_catalog_report() -> str:
    rows = ["**Available local model profiles**"]
    rows.extend(
        f"- **{option.name}** · {option.parameter_count} · {option.quantization} · "
        f"{option.memory_guidance}\n  `{option.model_id}`"
        for option in MODEL_OPTIONS
    )
    return "\n".join(rows)


def model_inspection_report(
    option: ModelOption,
    active_model: str,
    runtime_output: str,
) -> str:
    runtime_lines = [
        line.strip()
        for line in runtime_output.splitlines()
        if re.search(
            r"architecture|model type|model params|n_layer|n_head|n_embd|n_vocab|n_ctx|quant|tensor",
            line,
            re.IGNORECASE,
        )
    ]
    runtime_lines = list(dict.fromkeys(runtime_lines))[-24:]
    running = active_model == option.model_id
    details = [
        f"**{option.name} · model inspection**",
        f"- Model ID: `{option.model_id}`",
        f"- Parameters: `{option.parameter_count}`",
        f"- File format / quantization: `GGUF · {option.quantization}`",
        f"- Inference context: `{option.context_size:,} tokens`",
        f"- Memory guidance: {option.memory_guidance}",
        f"- Runtime: `{'loading or running' if running else 'not loaded'}`",
        "- Architecture: taken from llama.cpp's GGUF loader output; not guessed from the model name.",
    ]
    if runtime_lines:
        details.extend(("", "**Runtime-reported architecture and tensor metadata**", "```text"))
        details.extend(runtime_lines)
        details.append("```")
    else:
        details.extend(
            (
                "",
                "Detailed layer, embedding, vocabulary, and tensor-type values appear here after the model loads.",
            )
        )
    return "\n".join(details)