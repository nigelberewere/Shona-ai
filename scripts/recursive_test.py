import os
import re

SHONA_PROCLITICS = ["ne", "na", "pe", "pa", "se", "sa", "ye", "ya", "we", "wa", "ve", "va", "ze", "za", "re", "ra", "che", "cha", "zve", "zva", "gwe", "gwa", "kwe", "kwa"]
SHONA_PREFIXES = ["ma", "mi", "mu", "va", "chi", "zvi", "ru", "ri", "ka", "tu", "hu", "pa", "ku", "lu"]
SHONA_CONCORDS = ["ndino", "ndiri", "ndaka", "ndicha", "ndisinga", "ndine", "uno", "uno", "uri", "waka", "ucha", "usinga", "une", "ano", "ari", "aka", "acha", "asinga", "ane", "tino", "tiri", "taka", "ticha", "tisinga", "tine", "muno", "muri", "maka", "mucha", "musinga", "mune", "vano", "vari", "vaka", "vacha", "vasinga", "vane", "kuno", "kuri", "kwaka", "kucha", "kusinga", "kune", "chino", "chiri", "chaka", "chicha", "chisinga", "chine", "zvino", "zviri", "zvaka", "zvicha", "zvisinga", "zvine", "ino", "iri", "yaka", "icha", "isinga", "ine", "dzino", "dziri", "dzaka", "dzicha", "dzisinga", "dzine"]

SHONA_SUFFIXES = ["wa", "iwa", "isa", "esa", "ana", "ira", "era", "ura", "ora"]

def load_dictionary(path):
    words = set()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if w:
                    words.add(w)
    return words

def clean_word(w):
    return re.sub(r'[^a-z]', '', w.lower())

def is_lemma_in_dict(word, shona_words, depth=0):
    if len(word) < 2:
        return False
    if word in shona_words:
        return True
    if ("ku" + word) in shona_words:
        return True
        
    if depth > 4:
        return False
        
    # Try stripping concord
    for conc in SHONA_CONCORDS:
        if word.startswith(conc) and len(word) > len(conc):
            stem = word[len(conc):]
            if is_lemma_in_dict(stem, shona_words, depth+1):
                return True
                
    # Try stripping proclitics
    for proc in SHONA_PROCLITICS:
        if word.startswith(proc) and len(word) > len(proc):
            stem = word[len(proc):]
            if is_lemma_in_dict(stem, shona_words, depth+1):
                return True
                
    # Try stripping noun prefixes
    for pref in SHONA_PREFIXES:
        if word.startswith(pref) and len(word) > len(pref):
            stem = word[len(pref):]
            if is_lemma_in_dict(stem, shona_words, depth+1):
                return True
                
    # Try stripping suffixes
    for suf in SHONA_SUFFIXES:
        if word.endswith(suf) and len(word) > len(suf):
            stem = word[:-len(suf)]
            if is_lemma_in_dict(stem, shona_words, depth+1):
                return True
                
    return False

def test_recursive():
    dict_path = "data/dictionaries/shona_words.txt"
    backup_path = "data/processed/all_clean.bak.txt"
    
    shona_words = load_dictionary(dict_path)
    print(f"Loaded {len(shona_words):,} words from {dict_path}")
    
    with open(backup_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
        
    passes = 0
    total = len(lines)
    
    sampled_passed = []
    
    for idx, line in enumerate(lines[:1000]):  # Test on first 1000 lines
        words = [clean_word(w) for w in line.split() if clean_word(w)]
        if not words:
            continue
        absent = sum(1 for w in words if not is_lemma_in_dict(w, shona_words))
        ratio = absent / len(words)
        if ratio <= 0.25:
            passes += 1
            if len(sampled_passed) < 5:
                sampled_passed.append((line, ratio))
                
    print(f"Recursive parsing: Passed {passes} / 1000 ({passes/1000*100:.2f}%)")
    for s, r in sampled_passed:
        print(f"Pass: ratio={r:.2f} | {s}")

if __name__ == "__main__":
    test_recursive()
