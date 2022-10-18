from nltk.tokenize import word_tokenize
from nltk.tokenize.treebank import TreebankWordDetokenizer
from .dictionary import lem_word
import re

tokenize = word_tokenize
detokenize = TreebankWordDetokenizer().detokenize

re_bolded = r"__([ \w]+)__"
apply_bold = lambda word: f"__{word}__"

def remove_bold(text):
    return re.sub(re_bolded, lambda match: match.group(1), text)

def bold_word_in_text(
    word, 
    text, 
    language,
    use_lemmatize=True, 
    greedy_lemmatize=False):
    if not use_lemmatize:
        return re.sub(word, lambda match: apply_bold(match.group()), text)
    else:
        lemmed_word = lem_word(word, language, greedy_lemmatize)
        tokenised_text = tokenize(text)
        return detokenize(list(map(
            lambda w: apply_bold(w) if lem_word(w, language, greedy_lemmatize) == lemmed_word else w, 
            tokenised_text
        )))
