import language_tool_python

def check_and_correct_grammar(text):
    # Remove leading whitespace
    text = text.lstrip()

    # Initialize the LanguageTool object
    tool = language_tool_python.LanguageTool('en-US')  # Change language code if needed

    # Check for common indicators of incomplete sentences
    incomplete_indicators = (
        "and", "or", "but", "with", "to", "for", "if", "when", "because", "although", "since",
        "while", "until", "as", "after", "before", "in", "about", "near", "between", "among", 
        "including", "despite", "regarding", "besides", "upon", "unless", "whether",
        "although", "where", "like", "even if","they"
    )

    # Automatically remove trailing indicators if found
    for indicator in incomplete_indicators:
        if text.strip().endswith(indicator):
            # Remove the indicator from the end of the text
            text = text[: -len(indicator)].rstrip()  # Remove the indicator and any trailing whitespace
            break  # Exit the loop after the first removal

    # Check the text for grammar issues
    matches = tool.check(text)

    # If there are no issues
    if not matches:
        return text, "No grammar issues found."

    # Correct the issues found
    corrected_text = text
    for match in reversed(matches):  # Reverse to avoid index shifting
        start_index = match.offset
        end_index = start_index + match.errorLength
        replacement = match.replacements[0] if match.replacements else match.error  # Take the first replacement or the original error

        # Replace the error with the suggested correction
        corrected_text = corrected_text[:start_index] + replacement + corrected_text[end_index:]

    return corrected_text, matches