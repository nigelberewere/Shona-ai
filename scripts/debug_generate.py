import sys
import os
import traceback

# ensure repo root is on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from inference.generate import load_tokenizer, build_model_from_checkpoint, generate

def main():
    try:
        tokenizer = load_tokenizer('tokenizer/shona_bpe.model')
        model, device = build_model_from_checkpoint('training/checkpoints/shona_ai_final.pt', tokenizer, device='cpu')
        text = generate(model, tokenizer, 'Ndinoda Zimbabwe', max_tokens=20, device='cpu')
        print('Generated:', text)
    except Exception as e:
        print('Exception during generation:')
        traceback.print_exc()

if __name__ == '__main__':
    main()
