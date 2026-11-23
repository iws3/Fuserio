from localchat.models import (
    LOW_MEMORY_MODEL_ID,
    MID_MEMORY_MODEL_ID,
    MODEL_OPTIONS,
    model_option,
    recommended_model_id,
)
from localchat.terminal_tools import model_inspection_report, run_read_only_command


def test_model_catalog_has_unique_local_server_ids():
    identifiers = [option.model_id for option in MODEL_OPTIONS]

    assert len(identifiers) == len(set(identifiers))
    assert all(option.model_id for option in MODEL_OPTIONS)
    assert all(option.name and option.description and option.quantization for option in MODEL_OPTIONS)


def test_model_lookup_returns_matching_metadata():
    selected = MODEL_OPTIONS[0]

    assert model_option(selected.model_id) == selected
    assert model_option("missing/model") is None


def test_deepseek_reasoning_model_is_available_without_auto_download():
    deepseek = next(option for option in MODEL_OPTIONS if option.name.startswith("DeepSeek"))

    assert deepseek.model_id == "bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF:Q4_K_M"
    assert "1.5B" in deepseek.quantization
    assert "reasoning" in deepseek.description


def test_low_memory_profile_is_default_candidate_and_uses_q4_at_2k_context():
    low_memory_model = model_option(LOW_MEMORY_MODEL_ID)

    assert low_memory_model is not None
    assert low_memory_model.parameter_count == "1.5B"
    assert low_memory_model.quantization.endswith("Q4_K_M")
    assert low_memory_model.context_size == 2048
    assert "4 GB host" in low_memory_model.memory_guidance
    assert recommended_model_id(4.0) == LOW_MEMORY_MODEL_ID
    assert recommended_model_id(None) == LOW_MEMORY_MODEL_ID
    assert recommended_model_id(6.0) == MID_MEMORY_MODEL_ID
    assert recommended_model_id(16.0) == MODEL_OPTIONS[0].model_id


def test_model_inspection_uses_runtime_architecture_metadata_when_available():
    option = model_option(LOW_MEMORY_MODEL_ID)
    assert option is not None

    report = model_inspection_report(
        option,
        option.model_id,
        "llm_load_print_meta: n_layer = 28\nllm_load_print_meta: n_embd = 1536",
    )

    assert "Q4_K_M" in report
    assert "n_layer = 28" in report
    assert "n_embd = 1536" in report
    assert "not guessed" in report


def test_read_only_terminal_commands_do_not_execute_unknown_input():
    assert run_read_only_command("pwd")
    assert run_read_only_command("sysinfo")
    assert run_read_only_command("touch unexpected-file") is None
