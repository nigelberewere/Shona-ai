import sentencepiece as spm
from pathlib import Path
import json
from datetime import datetime

PROCESSED_DIR = Path("data/processed")
TOKENIZER_DIR = Path("tokenizer")
TOKENIZER_DIR.mkdir(exist_ok=True)


def train():
    input_file = PROCESSED_DIR / "all_clean.txt"
    output_prefix = str(TOKENIZER_DIR / "shona_bpe")
    spm.SentencePieceTrainer.train(
        input=str(input_file),
        model_prefix=output_prefix,
        vocab_size=32000,
        character_coverage=0.9995,
        model_type="bpe",
        pad_id=0, bos_id=1, eos_id=2, unk_id=3,
        # normalization_rule_name="nfc",  # removed: not available in this sentencepiece build
        num_threads=4,
        input_sentence_size=5000000,
        shuffle_input_sentence=True,
    )
    print(f"Tokenizer saved to {output_prefix}.model")


def measure_fertility(model_path, test_sentences):
    sp = spm.SentencePieceProcessor()
    sp.load(str(model_path))
    total_tokens = 0
    total_words = 0
    for sentence in test_sentences:
        words = sentence.split()
        tokens = sp.encode(sentence)
        total_words += len(words)
        total_tokens += len(tokens)
    return total_tokens / max(total_words, 1)


if __name__ == "__main__":
    train()
    model_path = TOKENIZER_DIR / "shona_bpe.model"
    test_sentences = [
        "Mhoro makadii",
        "Ndinoda Zimbabwe",
        "Mwana akaenda kuchikoro",
        "Tinoenda kumba nhasi",
        "Zita rako ndiani",
    ]
    fertility = measure_fertility(model_path, test_sentences)
    print(f"Fertility score: {fertility:.3f} tokens/word (target < 1.8)")
    stats = {"fertility": fertility, "vocab_size": 32000, 
             "trained_at": datetime.now().isoformat()}
    with open(TOKENIZER_DIR / "tokenizer_stats.json", "w") as f:
        json.dump(stats, f, indent=2)
