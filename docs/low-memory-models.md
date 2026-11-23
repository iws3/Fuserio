# Low-memory local models

Fuserio's 4 GB profile uses the existing DeepSeek-R1-Distill-Qwen 1.5B GGUF in
`Q4_K_M` quantization. It is the default when no model preference has been
saved. The launcher and in-app server use a 2,048-token context, CPU inference,
one parallel slot, and smaller prompt batches to limit peak memory use.

The model catalog also includes 3B and 4B Q4 profiles. Their weight files and
runtime state need more memory, so they are not recommended on a 4 GB computer.
Actual usage varies with the llama.cpp build, operating system, and prompt size;
the estimate shown in the app is guidance, not a hard guarantee.

These are already-quantized GGUF files, not models quantized by Fuserio at
startup. The app runs with Hugging Face offline mode enabled and does not fetch
weights automatically. The selected GGUF must already exist in the local model
cache before the server can load it.

In the terminal, `models` lists the available profiles and `model inspect`
shows the selected profile. After loading, the inspection also includes
architecture, layer, embedding, vocabulary, context, and tensor metadata that
llama.cpp reports while reading the GGUF. Values are not inferred from the
model's display name.