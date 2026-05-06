import re


def classify_intent(text):
    text = text.lower()
    # Search intents
    if re.search(r'\b(find|search|look for|show me)\b', text):
        # Extract query
        for keyword in ['find', 'search', 'look for', 'show me']:
            if keyword in text:
                query = text.split(keyword, 1)[-1].strip()
                break
        else:
            query = text
        return {'intent': 'SEARCH', 'query': query}

    # Playback intents
    if 'play' in text:
        return {'intent': 'PLAY'}
    if 'pause' in text:
        return {'intent': 'PAUSE'}
    if 'resume' in text:
        return {'intent': 'RESUME'}
    if 'stop' in text:
        return {'intent': 'STOP'}

    return {'intent': 'UNKNOWN'}


if __name__ == '__main__':
    tests = [
        "Find books by Arthur Conan Doyle",
        "Search for mystery novels",
        "Play the audiobook",
        "Pause playback",
        "stop",
        "Turn the lights on",
    ]
    for t in tests:
        print(t, "->", classify_intent(t))
