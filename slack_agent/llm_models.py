from google.adk.models.lite_llm import LiteLlm

full_model = LiteLlm(
    model="vertex_ai/gemini-2.5-pro-preview-03-25",
    vertex_location="us-central1",
    num_retries=5,
    fallbacks=[
        "vertex_ai/gemini-2.5-pro-preview-03-25",
        "vertex_ai/gemini-2.0-pro-exp-02-05",
        "vertex_ai/gemini-2.5-flash-preview-04-17",
        "vertex_ai/gemini-2.0-flash",
    ],
)
flash_model = LiteLlm(
    model="vertex_ai/gemini-2.0-flash",
    vertex_location="us-central1",
    num_retries=5,
    fallbacks=[
        "vertex_ai/gemini-2.5-flash-preview-04-17",
        "vertex_ai/gemini-2.0-flash",
        "vertex_ai/gemini-2.5-pro-preview-03-25",
        "vertex_ai/gemini-2.0-pro-exp-02-05",
    ],
)
