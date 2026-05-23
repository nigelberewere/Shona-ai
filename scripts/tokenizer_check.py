import sentencepiece as spm
p='tokenizer/shona_bpe.model'
sp=spm.SentencePieceProcessor()
sp.Load(p)
print('vocab_size=',sp.GetPieceSize())
text='Mhoro, makadii?'
ids=sp.EncodeAsIds(text)
print('ids=',ids)
dec=sp.DecodeIds(ids)
print('dec=',dec)
# check for pad token
pad = None
try:
    pad_id = sp.PieceToId('<pad>')
    pad = pad_id
except Exception:
    pad = None
print('pad id =', pad)
