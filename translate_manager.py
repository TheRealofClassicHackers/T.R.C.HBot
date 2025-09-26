def translate_to_pig_latin(text):
    words = text.split()
    result = []
    for word in words:
        if not word:
            continue
        if word[0].lower() in 'aeiou':
            result.append(word + 'ay')
        else:
            result.append(word[1:] + word[0] + 'ay')
    return ' '.join(result)