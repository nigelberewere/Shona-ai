import json
import re
import os
import sys

# Import the morphological engine from morphology_engine.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from morphology_engine import pluralize_noun, generate_verbal_extensions
except ImportError:
    print("WARNING: Could not import from morphology_engine.py. Defining fallbacks.")
    def pluralize_noun(word, noun_class): return None
    def generate_verbal_extensions(word): return []

def clean_word(word):
    """
    Cleans a Shona word by lowercasing, stripping leading/trailing whitespace,
    and removing any non-alphabetic/non-standard characters except hyphens and spaces.
    """
    if not word:
        return ""
    word_clean = word.lower().strip()
    # Remove any characters that are not lowercase latin letters, spaces, or hyphens
    word_clean = re.sub(r'[^a-z\s-]', '', word_clean)
    return word_clean.strip()

def normalize_pos(pos):
    """
    Normalizes part of speech tags to a standard set.
    """
    if not pos:
        return "unknown"
    pos = pos.lower().strip()
    if pos in ["noun", "n", "mupanda"]:
        return "noun"
    elif pos in ["verb", "v", "ku"]:
        return "verb"
    elif pos in ["adjective", "adj", "a"]:
        return "adjective"
    elif pos in ["adverb", "adv"]:
        return "adverb"
    elif pos in ["pronoun", "pron", "p"]:
        return "pronoun"
    elif pos in ["interjection", "int"]:
        return "interjection"
    elif pos in ["conjunction", "conj"]:
        return "conjunction"
    elif pos in ["preposition", "prep"]:
        return "preposition"
    return "unknown"

def normalize_noun_class(class_str):
    """
    Standardizes raw noun class labels to 'Class X' or 'Class Xa'.
    """
    if not class_str:
        return ""
    class_str = class_str.lower().strip()
    if "1a" in class_str:
        return "Class 1a"
    if "2a" in class_str:
        return "Class 2a"
    nums = re.findall(r'\d+', class_str)
    if nums:
        return f"Class {nums[0]}"
    if "mu" in class_str and "mi" in class_str:
        return "Class 3"
    return class_str.capitalize()

def clean_definition(definition):
    """
    Cleans up English definitions by splitting, stripping, deduplicating,
    and removing common wikitext clutter or blank segments.
    """
    if not definition:
        return ""
    # Split by semicolon to deduplicate individual senses
    parts = [p.strip() for p in re.split(r'[;]', definition) if p.strip()]
    unique_parts = []
    seen = set()
    for p in parts:
        # Avoid redundant entries, placeholders, or self-definitions
        p_lower = p.lower()
        if p_lower in seen or p_lower in ["=", "", "-", "n/a", "unknown"]:
            continue
        seen.add(p_lower)
        unique_parts.append(p)
    return "; ".join(unique_parts)

def strip_to(def_en):
    """
    Strips the leading 'to ' from verbs in definitions to make conjugations read naturally.
    e.g. 'to speak; to talk' -> 'speak; talk'
    """
    parts = [p.strip() for p in def_en.split(";") if p.strip()]
    cleaned = []
    for p in parts:
        if p.lower().startswith("to "):
            cleaned.append(p[3:].strip())
        else:
            cleaned.append(p)
    return "; ".join(cleaned)

def get_auxiliary(subject):
    """
    Returns appropriate auxiliary verb 'am', 'is', or 'are' for English progressive tense.
    """
    if subject == "I":
        return "am"
    elif subject == "he/she/it":
        return "is"
    return "are"

def main():
    print("Phase 2 — Starting cleaning, merging, and orthography normalization...")
    
    # 1. Load Raw Datasets
    wiktionary_entries = []
    spacy_entries = []
    historical_entries = []
    
    if os.path.exists("wiktionary_raw.json"):
        with open("wiktionary_raw.json", "r", encoding="utf-8") as f:
            wiktionary_entries = json.load(f)
        print(f"Loaded {len(wiktionary_entries)} entries from Wiktionary raw file.")
    else:
        print("WARNING: wiktionary_raw.json not found!")
        
    if os.path.exists("shona_lexicon.json"):
        with open("shona_lexicon.json", "r", encoding="utf-8") as f:
            spacy_entries = json.load(f)
        print(f"Loaded {len(spacy_entries)} entries from spaCy lexicon file.")
    else:
        print("WARNING: shona_lexicon.json not found!")
        
    if os.path.exists("historical_raw.json"):
        with open("historical_raw.json", "r", encoding="utf-8") as f:
            historical_entries = json.load(f)
        print(f"Loaded {len(historical_entries)} entries from historical raw file.")
    else:
        print("WARNING: historical_raw.json not found!")
        
    # 2. Merge and Deduplicate Entries
    # Keyed by (cleaned_word, standardized_pos)
    merged = {}
    
    # A. Process spaCy Lexicon
    for entry in spacy_entries:
        # spaCy entries use 'token' or 'lemma'
        word = clean_word(entry.get("token", ""))
        pos = normalize_pos(entry.get("pos", ""))
        
        if not word:
            continue
            
        noun_class = normalize_noun_class(entry.get("category_detail", ""))
        definition_en = clean_definition(entry.get("gloss", ""))
        definition_sn = entry.get("definition_sn", "").strip()
        example_sentence = entry.get("example_sentence", "").strip()
        
        # If POS is verb, ensure it is represented as an infinitive starting with 'ku'
        if pos == "verb":
            if not word.startswith("ku"):
                word = "ku" + word
            if not word.endswith("a"):
                word = word + "a"
                
        key = (word, pos)
        if key not in merged:
            merged[key] = {
                "word": word,
                "part_of_speech": pos,
                "class": noun_class,
                "definition_en": definition_en,
                "definition_sn": definition_sn,
                "example_sentence": example_sentence,
                "synonyms": [],
                "antonyms": [],
                "source": "spaCy Lexicon"
            }
            
    # B. Process Wiktionary
    for entry in wiktionary_entries:
        word = clean_word(entry.get("word", ""))
        pos = normalize_pos(entry.get("part_of_speech", ""))
        
        if not word:
            continue
            
        noun_class = normalize_noun_class(entry.get("class", ""))
        definition_en = clean_definition(entry.get("definition_en", ""))
        definition_sn = entry.get("definition_sn", "").strip()
        example_sentence = entry.get("example_sentence", "").strip()
        synonyms = entry.get("synonyms", [])
        antonyms = entry.get("antonyms", [])
        
        if pos == "verb":
            if word.startswith("-"):
                word = word[1:]
            if not word.startswith("ku"):
                word = "ku" + word
            if not word.endswith("a"):
                word = word + "a"
                
        key = (word, pos)
        if key not in merged:
            merged[key] = {
                "word": word,
                "part_of_speech": pos,
                "class": noun_class,
                "definition_en": definition_en,
                "definition_sn": definition_sn,
                "example_sentence": example_sentence,
                "synonyms": list(synonyms),
                "antonyms": list(antonyms),
                "source": "Wiktionary"
            }
        else:
            # Merge fields
            existing = merged[key]
            if not existing["class"] and noun_class:
                existing["class"] = noun_class
            if definition_en:
                existing["definition_en"] = clean_definition(existing["definition_en"] + "; " + definition_en)
            if not existing["definition_sn"] and definition_sn:
                existing["definition_sn"] = definition_sn
            if not existing["example_sentence"] and example_sentence:
                existing["example_sentence"] = example_sentence
            for s in synonyms:
                if s not in existing["synonyms"]: existing["synonyms"].append(s)
            for a in antonyms:
                if a not in existing["antonyms"]: existing["antonyms"].append(a)
            if "Wiktionary" not in existing["source"]:
                existing["source"] = existing["source"] + ", Wiktionary"
                
    # C. Process Historical & Swadesh
    for entry in historical_entries:
        word = clean_word(entry.get("word", ""))
        pos = normalize_pos(entry.get("part_of_speech", ""))
        
        if not word:
            continue
            
        noun_class = normalize_noun_class(entry.get("class", ""))
        definition_en = clean_definition(entry.get("definition_en", ""))
        definition_sn = entry.get("definition_sn", "").strip()
        example_sentence = entry.get("example_sentence", "").strip()
        synonyms = entry.get("synonyms", [])
        antonyms = entry.get("antonyms", [])
        source = entry.get("source", "Historical Core")
        
        if pos == "verb":
            if word.startswith("-"):
                word = word[1:]
            if not word.startswith("ku"):
                word = "ku" + word
            if not word.endswith("a"):
                word = word + "a"
                
        key = (word, pos)
        if key not in merged:
            merged[key] = {
                "word": word,
                "part_of_speech": pos,
                "class": noun_class,
                "definition_en": definition_en,
                "definition_sn": definition_sn,
                "example_sentence": example_sentence,
                "synonyms": list(synonyms),
                "antonyms": list(antonyms),
                "source": source
            }
        else:
            existing = merged[key]
            if not existing["class"] and noun_class:
                existing["class"] = noun_class
            if definition_en:
                existing["definition_en"] = clean_definition(existing["definition_en"] + "; " + definition_en)
            if not existing["definition_sn"] and definition_sn:
                existing["definition_sn"] = definition_sn
            if not existing["example_sentence"] and example_sentence:
                existing["example_sentence"] = example_sentence
            for s in synonyms:
                if s not in existing["synonyms"]: existing["synonyms"].append(s)
            for a in antonyms:
                if a not in existing["antonyms"]: existing["antonyms"].append(a)
            if source not in existing["source"]:
                existing["source"] = existing["source"] + f", {source}"
                
    # Filter out entries with empty English definitions
    merged = {k: v for k, v in merged.items() if v["definition_en"].strip()}
    
    print(f"Merging completed. Total unique base dictionary lemmas: {len(merged)}")
    
    # 3. Apply Morphological Engine to Expand Dictionary
    expanded_list = list(merged.values())
    
    # Set of existing words to prevent exact duplicates (lowercase representation)
    existing_words = set(e["word"].lower().strip() for e in expanded_list)
    
    # A. Noun Pluralization
    print("Generating Bantu Noun Plurals...")
    plural_count = 0
    new_plurals = []
    
    for entry in expanded_list:
        if entry["part_of_speech"] == "noun" and entry["class"]:
            singular_word = entry["word"]
            noun_class = entry["class"]
            
            plural_word = pluralize_noun(singular_word, noun_class)
            if plural_word:
                plural_word = clean_word(plural_word)
                if plural_word and plural_word not in existing_words:
                    # Determine the plural noun class
                    plural_class = ""
                    if "class 1" in noun_class.lower(): plural_class = "Class 2"
                    elif "class 3" in noun_class.lower(): plural_class = "Class 4"
                    elif "class 5" in noun_class.lower(): plural_class = "Class 6"
                    elif "class 7" in noun_class.lower(): plural_class = "Class 8"
                    elif "class 11" in noun_class.lower(): plural_class = "Class 10"
                    elif "class 14" in noun_class.lower(): plural_class = "Class 6"
                    else: plural_class = "Class 10"  # default plural
                    
                    definition_en = f"plural of {singular_word} (meaning: {entry['definition_en']})"
                    definition_sn = f"uwandu hwe {singular_word}"
                    if entry["definition_sn"]:
                        definition_sn += f" (kureva: {entry['definition_sn']})"
                        
                    new_plurals.append({
                        "word": plural_word,
                        "part_of_speech": "noun",
                        "class": plural_class,
                        "definition_en": definition_en,
                        "definition_sn": definition_sn,
                        "example_sentence": "",
                        "synonyms": [],
                        "antonyms": [],
                        "source": f"Morphological Engine (Plural of {singular_word})"
                    })
                    existing_words.add(plural_word)
                    plural_count += 1
                    
    expanded_list.extend(new_plurals)
    print(f"Successfully generated {plural_count} new plural noun lemmas.")
    
    # B. Verbal Extensions
    print("Generating Bantu Verbal Extensions...")
    extensions_count = 0
    new_extensions = []
    
    # Temporary copy of current list to avoid modifying size during loop
    current_verbs = [e for e in expanded_list if e["part_of_speech"] == "verb"]
    
    for entry in current_verbs:
        verb_word = entry["word"]
        # Generate extensions
        exts = generate_verbal_extensions(verb_word)
        for ext in exts:
            ext_word = clean_word(ext["word"])
            if ext_word and ext_word not in existing_words:
                ext_type = ext["ext_type"]
                definition_suffix = ext["definition_suffix"]
                
                # Combine base definition with extension meaning
                cleaned_base_def = strip_to(entry["definition_en"])
                definition_en = f"to {cleaned_base_def} ({definition_suffix})"
                
                definition_sn = f"chiito chekupfuurira kubva pane: {verb_word} ({ext_type})"
                
                new_extensions.append({
                    "word": ext_word,
                    "part_of_speech": "verb",
                    "class": "",
                    "definition_en": definition_en,
                    "definition_sn": definition_sn,
                    "example_sentence": "",
                    "synonyms": [],
                    "antonyms": [],
                    "source": f"Morphological Engine ({ext_type.capitalize()} of {verb_word})"
                })
                existing_words.add(ext_word)
                extensions_count += 1
                
    expanded_list.extend(new_extensions)
    print(f"Successfully generated {extensions_count} new verbal extensions lemmas.")
    
    # C. Conjugated Verb Forms (Unimorph-style)
    # This expands our vocabulary substantially and represents standard grammatical forms.
    print("Generating Unimorph-style Conjugational Verb Forms...")
    conjugations_count = 0
    new_conjugations = []
    
    # Get all verbs currently in our expanded list (both original roots and verbal extensions)
    all_verbs = [e for e in expanded_list if e["part_of_speech"] == "verb"]
    
    # Subject prefixes and their details
    subjects = [
        {"prefix": "ndi", "subject": "I", "past_prefix": "nda", "remote_past_prefix": "ndaka"},
        {"prefix": "u", "subject": "you (singular)", "past_prefix": "wa", "remote_past_prefix": "waka"},
        {"prefix": "a", "subject": "he/she/it", "past_prefix": "a", "remote_past_prefix": "aka"},
        {"prefix": "ti", "subject": "we", "past_prefix": "ta", "remote_past_prefix": "taka"},
        {"prefix": "mu", "subject": "you (plural)", "past_prefix": "ma", "remote_past_prefix": "maka"},
        {"prefix": "va", "subject": "they", "past_prefix": "va", "remote_past_prefix": "vaka"}
    ]
    
    for entry in all_verbs:
        verb_word = entry["word"]
        # Only process verbs starting with 'ku' and ending with 'a'
        if not (verb_word.startswith("ku") and verb_word.endswith("a")):
            continue
            
        root = verb_word[2:-1]
        if not root:
            continue
            
        cleaned_base_def = strip_to(entry["definition_en"])
        
        for sub in subjects:
            prefix = sub["prefix"]
            subject = sub["subject"]
            past_pref = sub["past_prefix"]
            remote_pref = sub["remote_past_prefix"]
            aux = get_auxiliary(subject)
            
            # 1. Present Habitual (e.g. ndinobvuma)
            pres_word = prefix + "no" + root + "a"
            if pres_word not in existing_words:
                def_en = f"{subject} {cleaned_base_def} (conjugation: present habitual tense)"
                new_conjugations.append({
                    "word": pres_word,
                    "part_of_speech": "verb",
                    "class": "",
                    "definition_en": def_en,
                    "definition_sn": f"chiito chokusimbisa chemunhu: {subject} kubva pane: {verb_word}",
                    "example_sentence": "",
                    "synonyms": [],
                    "antonyms": [],
                    "source": f"Morphological Engine (Conjugation of {verb_word})"
                })
                existing_words.add(pres_word)
                conjugations_count += 1
                
            # 2. Present Progressive (e.g. ndirikubvuma)
            prog_word = prefix + "riku" + root + "a"
            if prog_word not in existing_words:
                def_en = f"{subject} {aux} currently {cleaned_base_def} (conjugation: progressive tense)"
                new_conjugations.append({
                    "word": prog_word,
                    "part_of_speech": "verb",
                    "class": "",
                    "definition_en": def_en,
                    "definition_sn": f"chiito chiri kuitika iye zvino chemunhu: {subject} kubva pane: {verb_word}",
                    "example_sentence": "",
                    "synonyms": [],
                    "antonyms": [],
                    "source": f"Morphological Engine (Conjugation of {verb_word})"
                })
                existing_words.add(prog_word)
                conjugations_count += 1
                
            # 3. Near Past / HOD (e.g. ndabvuma)
            past_word = past_pref + root + "a"
            if past_word not in existing_words:
                def_en = f"{subject} {cleaned_base_def} recently (conjugation: near past tense)"
                new_conjugations.append({
                    "word": past_word,
                    "part_of_speech": "verb",
                    "class": "",
                    "definition_en": def_en,
                    "definition_sn": f"chiito chakaitika achangobva chemunhu: {subject} kubva pane: {verb_word}",
                    "example_sentence": "",
                    "synonyms": [],
                    "antonyms": [],
                    "source": f"Morphological Engine (Conjugation of {verb_word})"
                })
                existing_words.add(past_word)
                conjugations_count += 1
                
            # 4. Remote Past (e.g. ndakabvuma)
            remote_word = remote_pref + root + "a"
            if remote_word not in existing_words:
                def_en = f"{subject} {cleaned_base_def} (conjugation: remote past tense)"
                new_conjugations.append({
                    "word": remote_word,
                    "part_of_speech": "verb",
                    "class": "",
                    "definition_en": def_en,
                    "definition_sn": f"chiito chakaitika kare chemunhu: {subject} kubva pane: {verb_word}",
                    "example_sentence": "",
                    "synonyms": [],
                    "antonyms": [],
                    "source": f"Morphological Engine (Conjugation of {verb_word})"
                })
                existing_words.add(remote_word)
                conjugations_count += 1
                
            # 5. Future (e.g. ndichabvuma)
            fut_word = prefix + "cha" + root + "a"
            if fut_word not in existing_words:
                def_en = f"{subject} will {cleaned_base_def} (conjugation: future tense)"
                new_conjugations.append({
                    "word": fut_word,
                    "part_of_speech": "verb",
                    "class": "",
                    "definition_en": def_en,
                    "definition_sn": f"chiito chichazoitika chemunhu: {subject} kubva pane: {verb_word}",
                    "example_sentence": "",
                    "synonyms": [],
                    "antonyms": [],
                    "source": f"Morphological Engine (Conjugation of {verb_word})"
                })
                existing_words.add(fut_word)
                conjugations_count += 1
                
    expanded_list.extend(new_conjugations)
    print(f"Successfully generated {conjugations_count} new conjugational verb lemmas.")
    print(f"Morphological expansion completed. Total final unique lemmas: {len(expanded_list)}")
    
    # Save the fully merged & expanded dataset
    output_path = "shona_dictionary_expanded.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(expanded_list, f, ensure_ascii=False, indent=2)
    print(f"Saved expanded dictionary with {len(expanded_list)} entries to {output_path}!")

if __name__ == "__main__":
    main()
