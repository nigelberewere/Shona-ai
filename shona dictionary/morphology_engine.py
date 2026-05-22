import re

def get_last_vowel(root):
    # Find the last vowel in the root to apply vowel harmony rules
    vowels = re.findall(r'[aeiou]', root.lower())
    if vowels:
        return vowels[-1]
    return 'a'

def pluralize_noun(word, noun_class):
    """
    Applies Bantu noun class singular-to-plural transformations.
    Linguistically handles prefix substitutions and Class 5 consonant mutations.
    """
    word_lower = word.lower().strip()
    cls = noun_class.lower().strip()
    
    # Exact or safe substring checks to avoid "class 1" matching "class 11"
    # Checking Class 11 and 14 first handles potential prefix collisions
    if "class 11" in cls or "mupanda 11" in cls or cls == "11":
        if word_lower == "rurimi":
            return "ndimi"
        elif word_lower.startswith("ruo"):
            return "mao" + word[3:]
        elif word_lower.startswith("rwi"):
            return "nzwi" + word[3:]
        elif word_lower.startswith("ru"):
            return "ma" + word[2:]
        else:
            return "ma" + word
            
    elif "class 14" in cls or "mupanda 14" in cls or cls == "14":
        if word_lower.startswith("u"):
            return "ma" + word[1:]
        else:
            return "ma" + word
            
    elif "class 1" in cls or "mupanda 1" in cls or cls == "1":
        if word_lower.startswith("mwana"):
            return "vana"
        elif word_lower.startswith("mw"):
            return "v" + word[2:]
        elif word_lower.startswith("mu"):
            return "va" + word[2:]
        else:
            return "va" + word
            
    # Class 3 (mu-) -> Class 4 (mi-)
    elif "class 3" in cls or "mupanda 3" in cls or cls == "3":
        if word_lower.startswith("mu"):
            return "mi" + word[2:]
        elif word_lower.startswith("mw"):
            return "mi" + word[2:]
        else:
            return "mi" + word
            
    # Class 5 (ri-/zero-) -> Class 6 (ma-)
    # Handles consonant mutations: voiceless to voiced alternations
    elif "class 5" in cls or "mupanda 5" in cls or cls == "5":
        if word_lower.startswith("i"):
            # e.g., ibwe -> mabwe
            return "ma" + word[1:]
        elif word_lower.startswith("g"):
            # e.g., gomo -> makomo (voicing mutation g -> k)
            return "mak" + word[1:]
        elif word_lower.startswith("b") and len(word_lower) > 1 and word_lower[1] in 'aeiou':
            # e.g., badza -> mapadza, banga -> mapanga (voicing mutation b -> p)
            return "map" + word[1:]
        elif word_lower.startswith("d") and len(word_lower) > 1 and word_lower[1] in 'aeiou':
            # e.g., danda -> matanda (voicing mutation d -> t)
            return "mat" + word[1:]
        else:
            # e.g., zuva -> mazuva, jira -> majira
            return "ma" + word
            
    # Class 7 (chi-) -> Class 8 (zvi-)
    elif "class 7" in cls or "mupanda 7" in cls or cls == "7":
        if word_lower.startswith("chi"):
            return "zvi" + word[3:]
        elif word_lower.startswith("ch"):
            return "zv" + word[2:]
        else:
            return "zvi" + word
            
    return None

def generate_verbal_extensions(word):
    """
    Generates standard Bantu verbal extensions for a Shona verb root.
    Uses vowel harmony rules for applied/causative/reversive extensions.
    
    Vowel Harmony Rule:
    - Last vowel 'e' or 'o' -> applied/causative uses 'e' (-er-, -es-), reversive uses 'o' (-or-)
    - Last vowel 'a', 'i', 'u' -> applied/causative uses 'i' (-ir-, -is-), reversive uses 'u' (-ur-)
    """
    word_lower = word.lower().strip()
    
    # We only process verbs that start with 'ku' (infinitive form) and end with 'a'
    if not (word_lower.startswith("ku") and word_lower.endswith("a")):
        return []
        
    # Strip 'ku' and final 'a' to get the root
    root = word[2:-1]
    
    if not root:
        return []
        
    last_vowel = get_last_vowel(root)
    
    # 1. Passive Extension (-wa / -iwa)
    if len(root) == 1:
        # Monosyllabic roots use -iwa (e.g., kuda -> kudiwa)
        passive = "ku" + root + "iwa"
    else:
        passive = "ku" + root + "wa"
        
    # 2. Causative Extension (-is- / -es-)
    causative_suffix = "es" if last_vowel in 'eo' else "is"
    causative = "ku" + root + causative_suffix + "a"
    
    # 3. Reciprocal Extension (-ana)
    reciprocal = "ku" + root + "ana"
    
    # 4. Applied Extension (-ir- / -er-)
    applied_suffix = "er" if last_vowel in 'eo' else "ir"
    applied = "ku" + root + applied_suffix + "a"
    
    # 5. Reversive Extension (-ur- / -or-)
    reversive_suffix = "or" if last_vowel == 'o' else "ur"
    reversive = "ku" + root + reversive_suffix + "a"
    
    return [
        {"ext_type": "passive", "word": passive, "definition_suffix": "to be v-ed"},
        {"ext_type": "causative", "word": causative, "definition_suffix": "to cause to v; to make v"},
        {"ext_type": "reciprocal", "word": reciprocal, "definition_suffix": "to v each other"},
        {"ext_type": "applied", "word": applied, "definition_suffix": "to v for / at / on behalf of"},
        {"ext_type": "reversive", "word": reversive, "definition_suffix": "to un-v; to reverse the action of v"}
    ]

# Basic sanity check
if __name__ == "__main__":
    print("Testing Noun Pluralization:")
    print("  munhu (Class 1) ->", pluralize_noun("munhu", "Class 1"))
    print("  mwana (Class 1) ->", pluralize_noun("mwana", "Class 1"))
    print("  muti (Class 3) ->", pluralize_noun("muti", "Class 3"))
    print("  gomo (Class 5) ->", pluralize_noun("gomo", "Class 5"))
    print("  badza (Class 5) ->", pluralize_noun("badza", "Class 5"))
    print("  chigaro (Class 7) ->", pluralize_noun("chigaro", "Class 7"))
    print("  ruoko (Class 11) ->", pluralize_noun("ruoko", "Class 11"))
    print("  rwizi (Class 11) ->", pluralize_noun("rwizi", "Class 11"))
    
    print("\nTesting Verbal Extensions:")
    print("  kutaura:")
    for ext in generate_verbal_extensions("kutaura"):
        print(f"    {ext['ext_type']}: {ext['word']} ({ext['definition_suffix']})")
    print("  kuenda:")
    for ext in generate_verbal_extensions("kuenda"):
        print(f"    {ext['ext_type']}: {ext['word']} ({ext['definition_suffix']})")
    print("  kuda:")
    for ext in generate_verbal_extensions("kuda"):
        print(f"    {ext['ext_type']}: {ext['word']} ({ext['definition_suffix']})")
