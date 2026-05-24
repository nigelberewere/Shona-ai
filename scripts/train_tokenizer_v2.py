import sentencepiece as spm
import random
import os

def main():
    print("JOB 1: Starting tokenizer retraining...")
    
    # 1. Train the new tokenizer on the full corpus
    spm.SentencePieceTrainer.train(
        input='data/processed/all_clean.txt',
        model_prefix='tokenizer/shona_bpe_v2',
        vocab_size=32000,
        character_coverage=0.9995,
        model_type='bpe',
        pad_id=0,
        bos_id=1,
        eos_id=2,
        unk_id=3,
        pad_piece='<pad>',
        bos_piece='<s>',
        eos_piece='</s>',
        unk_piece='<unk>',
    )
    print("Tokenizer trained successfully")

    # 2. Load the old and new tokenizers
    sp_old = spm.SentencePieceProcessor()
    sp_old.load('tokenizer/shona_bpe.model')

    sp_new = spm.SentencePieceProcessor()
    sp_new.load('tokenizer/shona_bpe_v2.model')

    # 3. Measure fertility on 200 random lines
    with open('data/processed/all_clean.txt', encoding='utf-8') as f:
        lines = [l.strip() for l in f if l.strip()]

    # Seed for reproducibility of evaluation
    random.seed(42)
    sample = random.sample(lines, 200)

    old_tokens = sum(len(sp_old.encode(l)) for l in sample)
    new_tokens = sum(len(sp_new.encode(l)) for l in sample)
    old_words = sum(len(l.split()) for l in sample)

    old_fertility = old_tokens / old_words
    new_fertility = new_tokens / old_words
    improvement = ((old_tokens - new_tokens) / old_tokens) * 100

    print(f"Old tokenizer fertility: {old_fertility:.4f}")
    print(f"New tokenizer fertility: {new_fertility:.4f}")
    print(f"Improvement: {improvement:.2f}% fewer tokens")

if __name__ == "__main__":
    main()
