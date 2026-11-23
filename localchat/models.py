from dataclasses import dataclass


@dataclass(frozen=True)
class ModelOption:
    name: str
    model_id: str
    description: str
    quantization: str
    tag: str = "Assistant"
    icon: str = "⚡"
    parameter_count: str = "Unknown"
    memory_guidance: str = "Memory use depends on context size and backend."
    context_size: int = 2048


LOW_MEMORY_MODEL_ID = "bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF:Q4_K_M"
MID_MEMORY_MODEL_ID = "bartowski/Qwen2.5-3B-Instruct-GGUF:Q4_K_M"


MODEL_OPTIONS = (
    ModelOption(
        name="Nemotron 3 Nano",
        model_id="nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF:Q4_K_M",
        description="Reasoning-focused assistant for coding and analysis",
        quantization="4B · Q4_K_M",
        tag="Logic & Code",
        icon="🧠",
        parameter_count="4B",
        memory_guidance="4 GB+ model/runtime; 8 GB host memory recommended.",
    ),
    ModelOption(
        name="Qwen 2.5 Instruct",
        model_id="bartowski/Qwen2.5-3B-Instruct-GGUF:Q4_K_M",
        description="Compact general assistant for fast local chat",
        quantization="3B · Q4_K_M",
        tag="Fast General",
        icon="⚡",
        parameter_count="3B",
        memory_guidance="3 GB+ model/runtime; 6 GB host memory recommended.",
    ),
    ModelOption(
        name="DeepSeek R1 Distill Qwen",
        model_id="bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF:Q4_K_M",
        description="Small reasoning model for low-memory math and science use",
        quantization="1.5B · Q4_K_M",
        tag="Math & Science",
        icon="🔬",
        parameter_count="1.5B",
        memory_guidance="About 2 GB at 2K context; best fit for a 4 GB host.",
    ),
)


def model_option(model_id: str) -> ModelOption | None:
    return next((option for option in MODEL_OPTIONS if option.model_id == model_id), None)


def recommended_model_id(total_memory_gb: float | None) -> str:
    if total_memory_gb is None or total_memory_gb <= 4.5:
        return LOW_MEMORY_MODEL_ID
    if total_memory_gb <= 8:
        return MID_MEMORY_MODEL_ID
    return MODEL_OPTIONS[0].model_id
