import os
import re

SHONA_PREFIXES = [
    # Verbs / Concords
    "ndino", "ndiri", "ndaka", "ndicha", "ndisinga", "ndine",
    "uno", "uri", "waka", "ucha", "usinga", "une",
    "ano", "ari", "aka", "acha", "asinga", "ane",
    "tino", "tiri", "taka", "ticha", "tisinga", "tine",
    "muno", "muri", "maka", "mucha", "musinga", "mune",
    "vano", "vari", "vaka", "vacha", "vasinga", "vane",
    "kuno", "kuri", "kwaka", "kucha", "kusinga", "kune",
    "chino", "chiri", "chaka", "chicha", "chisinga", "chine",
    "zvino", "zviri", "zvaka", "zvicha", "zvisinga", "zvine",
    "ino", "iri", "yaka", "icha", "isinga", "ine",
    "dzino", "dziri", "dzaka", "dzicha", "dzisinga", "dzine",
    # Proclitics
    "ne", "na", "pe", "pa", "se", "sa", "ye", "ya", "we", "wa", "ve", "ze", "za", "re", "ra", "che", "cha", "zve", "zva", "gwe", "gwa", "kwe", "kwa",
    # Noun class prefixes
    "ma", "mi", "mu", "va", "chi", "zvi", "ru", "ri", "ka", "tu", "hu"
]

SHONA_SUFFIXES = [
    "wa", "iwa", "isa", "esa", "ana", "ira", "era", "ura", "ora"
]

def load_dictionary(path):
    words = set()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if w:
                    words.add(w)
    return words

def is_word_in_dict_fuzzy(word, shona_words):
    if word in shona_words:
        return True
        
    # Try stripping prefixes
    for pref in SHONA_PREFIXES:
        if word.startswith(pref) and len(word) > len(pref) + 2:
            stem = word[len(pref):]
            if stem in shona_words:
                return True
            # Also try prefix + infinitive (e.g. ndinoda -> ndino + da -> da / kuda)
            if stem.startswith("ku") and len(stem) > 4:
                infinitive_stem = stem[2:]
                if infinitive_stem in shona_words or stem in shona_words:
                    return True
            # Try stripping suffix of stem
            for suf in SHONA_SUFFIXES:
                if stem.endswith(suf) and len(stem) > len(suf) + 2:
                    substem = stem[:-len(suf)]
                    if substem in shona_words:
                        return True
                    # Try adding 'ku' to substem (since dictionary has infinitives)
                    if not substem.startswith("ku"):
                        if ("ku" + substem) in shona_words:
                            return True
                            
    # Try stripping suffixes directly
    for suf in SHONA_SUFFIXES:
        if word.endswith(suf) and len(word) > len(suf) + 2:
            stem = word[:-len(suf)]
            if stem in shona_words:
                return True
            if not stem.startswith("ku"):
                if ("ku" + stem) in shona_words:
                    return True
                    
    return False

def clean_dry_run():
    dict_path = "data/dictionaries/shona_words.txt"
    all_clean_path = "data/processed/all_clean.txt"
    
    shona_words = load_dictionary(dict_path)
    print(f"Loaded {len(shona_words):,} words from {dict_path}")
    
    if not os.path.exists(all_clean_path):
        print(f"File not found: {all_clean_path}")
        return
        
    with open(all_clean_path, "r", encoding="utf-8") as f:
        raw_lines = [line.strip() for line in f if line.strip()]
        
    print(f"Total lines in all_clean.txt: {len(raw_lines):,}")
    
    passes = 0
    fails_pattern = 0
    fails_length = 0
    fails_dict = 0
    duplicates_removed = 0
    
    seen_lines = set()
    sampled_passed = []
    
    for idx, line in enumerate(raw_lines):
        cleaned_line = line.replace("</s>", "").strip()
        cleaned_line = re.sub(r'\s+', ' ', cleaned_line).strip()
        
        if "chemunhu:" in cleaned_line:
            fails_pattern += 1
            continue
            
        if len(cleaned_line) < 15:
            fails_length += 1
            continue
            
        words = re.findall(r'[a-zA-Z]+', cleaned_line.lower())
        if not words:
            fails_dict += 1
            continue
            
        absent_count = 0
        for w in words:
            if not is_word_in_dict_fuzzy(w, shona_words):
                absent_count += 1
                
        absent_ratio = absent_count / len(words)
        
        if absent_ratio > 0.25:
            fails_dict += 1
            continue
            
        line_key = cleaned_line.casefold()
        if line_key in seen_lines:
            duplicates_removed += 1
            continue
            
        seen_lines.add(line_key)
        passes += 1
        
        if len(sampled_passed) < 10:
            sampled_passed.append(cleaned_line)
            
    print("\n=== LINGUISTIC DRY RUN RESULTS ===")
    print(f"Fails 'chemunhu:' pattern:    {fails_pattern:,}")
    print(f"Fails < 15 chars:             {fails_length:,}")
    print(f"Fails 25% dict check:         {fails_dict:,}")
    print(f"Fails duplicate check:        {duplicates_removed:,}")
    print(f"Passes all filters:           {passes:,} ({passes/len(raw_lines)*100:.2f}%)")
    print("==================================\n")
    
    if sampled_passed:
        print("--- First 5 samples passed ---")
        for i, s in enumerate(sampled_passed[:5]):
            print(f"{i+1}: {s}")

if __name__ == "__main__":
    clean_dry_run()
