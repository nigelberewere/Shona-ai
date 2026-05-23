import json, random
import sys
try:
    import sentencepiece as spm
except Exception as e:
    print('MISSING_SENTENCEPIECE', e)
    sys.exit(2)
sp=spm.SentencePieceProcessor()
if not sp.Load('tokenizer/shona_bpe.model'):
    print('FAILED_LOAD')
    sys.exit(3)
with open('shona dictionary/shona_dictionary_expanded.json','r',encoding='utf-8') as f:
    data=json.load(f)
sents=[e.get('definition_sn') for e in data if e.get('definition_sn')]
sents=[s.strip() for s in sents if s and s.strip()]
random.seed(42)
sample=sents[:200] if len(sents)>=200 else sents
tokens=sum(len(sp.EncodeAsPieces(s)) for s in sample)
words=sum(len(s.split()) for s in sample)
print('sample_size',len(sample))
print('tokens',tokens)
print('words',words)
print('fertility', tokens/words if words else 0.0)
