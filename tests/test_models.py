from localchat.models import MODEL_OPTIONS, model_option


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
