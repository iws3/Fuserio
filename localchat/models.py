from dataclasses import dataclass


@dataclass(frozen=True)
class ModelOption:
    name: str
    model_id: str
    description: str
    quantization: str


MODEL_OPTIONS = (
    ModelOption(
        name="Nemotron 3 Nano",
        model_id="nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF:Q4_K_M",
        description="Reasoning-focused assistant for coding and analysis",
        quantization="4B · Q4_K_M",
    ),
    ModelOption(
        name="Qwen 2.5 Instruct",
        model_id="bartowski/Qwen2.5-3B-Instruct-GGUF:Q4_K_M",
        description="Compact general assistant for fast local chat",
        quantization="3B · Q4_K_M",
    ),
    ModelOption(
        name="DeepSeek R1 Distill Qwen",
        model_id="bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF:Q4_K_M",
        description="Small reasoning model for math and science questions",
        quantization="1.5B · Q4_K_M",
    ),
)


def model_option(model_id: str) -> ModelOption | None:
    return next((option for option in MODEL_OPTIONS if option.model_id == model_id), None)
