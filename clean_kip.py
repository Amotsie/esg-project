import re
from grammar import check_and_correct_grammar

def extract_dynamic_associations(sentence, target_word, window=5):
    cleaned_sentence = re.sub(r'\b(?:N/A/?\s*)+\b', '', sentence)

    # Split the cleaned sentence into words
    words = cleaned_sentence.split()
    
    # Find positions of the target word in the sentence
    target_indices = [i for i, word in enumerate(words) if word.lower().startswith(target_word.lower())]
    
    # Initialize a list to store found associations
    results = []

    for index in target_indices:
        # Get words within the defined window around the target word
        start = max(0, index - window)
        end = min(len(words), index + window + 1)
        context_words = words[start:end]
        #check grammar and return sentence with good grammar
        #final_context_word=check_and_correct_grammar(context_words)
        # Join the context into a phrase
        context_phrase = " ".join(context_words)
        # Append the context phrase to results
        results.append(context_phrase)
    
    # Return the result
    return results if results else target_word


