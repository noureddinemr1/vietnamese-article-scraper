def count_words(text):
    if not text:
        return 0
           
    words = [word for word in text.split() if word.strip()]
    return len(words)
    