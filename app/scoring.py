"""Basic candidate scorer. Upgrade to semantic/event-based highlight detection in next iteration."""
HYPE_WORDS = {
    "wow", "omg", "no way", "insane", "crazy", "what", "bro", "laugh",
    "amazing", "unbelievable", "finally", "clutch", "fail", "win", "lost",
    "пиздец", "ахах", "смешно", "невероятно", "ого", "жесть", "вот это",
    "победа", "проиграл", "серьезно", "блин"
}

def score_segments(segments, min_seconds=45, max_seconds=75):
    candidates = []
    n = len(segments)
    i = 0
    while i < n:
        start = float(segments[i]["start"])
        j = i
        text_parts = []
        score = 0
        end = start
        while j < n and float(segments[j]["end"]) - start <= max_seconds:
            end = float(segments[j]["end"])
            text = (segments[j].get("text") or "").lower()
            text_parts.append(text)
            score += sum(1 for phrase in HYPE_WORDS if phrase in text)
            j += 1
            if end - start >= min_seconds:
                candidates.append((score, start, end, " ".join(text_parts)))
                break
        i += max(1, j - i)
    candidates.sort(key=lambda c: c[0], reverse=True)
    selected = []
    for candidate in candidates:
        if all(candidate[2] <= s[1] or candidate[1] >= s[2] for s in selected):
            selected.append(candidate)
    return sorted(selected, key=lambda c: c[1])
