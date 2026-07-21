import logging
from functools import lru_cache
from config import SUMMARIZER_MODEL, MAX_SUMMARY_TOKENS
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------------------------------------------
# ⚡ OPTIMIZATIONS:
# 1. Lazy loading & caching of summarizer
# 2. Handles single combined text for concise summary
# 3. Truncates input text if too long for efficiency
# 4. Fallback to short snippet if summarization fails
# ---------------------------------------------------

@lru_cache(maxsize=1)
def _load_summarizer():
    tokenizer = AutoTokenizer.from_pretrained(SUMMARIZER_MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        SUMMARIZER_MODEL,
        device_map="auto",
        torch_dtype="auto",
    )
    model.eval()
    return tokenizer, model


def summarize(text, max_input_chars=3000, max_summary_tokens=MAX_SUMMARY_TOKENS):
    """
    Summarizes long text efficiently into a concise output.

    Args:
        text (str): Combined text from multiple sources
        max_input_chars (int): Truncate input to avoid very long texts
        max_summary_tokens (int): Maximum number of tokens in the summary

    Returns:
        str: Concise summary
    """
    tokenizer, model = _load_summarizer()

    if not text or len(text.strip()) < 60:
        return text.strip()

    # Truncate extremely long input
    text = text[:max_input_chars]

    try:
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=1024,  # BART's maximum input length
        )

        # Move inputs to the model's device
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_summary_tokens,
                min_new_tokens=30,
                num_beams=4,
                length_penalty=2.0,
                no_repeat_ngram_size=3,
                early_stopping=True,
            )

        summary = tokenizer.decode(
            output_ids[0],
            skip_special_tokens=True
        ).strip()

        return summary

    except Exception as e:
        logging.warning(f"Summarization failed: {e}")

        # Fallback: first 300 chars
        fallback = text[:300]
        if "." in fallback:
            fallback = fallback.rsplit(".", 1)[0]
        return fallback + "..."