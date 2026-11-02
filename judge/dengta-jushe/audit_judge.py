def evaluate(state, text):
    challenge = state.get('hintMode') is False
    login = challenge and state.get('backstageUnlocked') is True
    reconstructed = login and state.get('reconstructed') is True
    return dict(login=login, reconstruction=reconstructed, optional_cue=login and state.get('cueGameDone') is True, success=reconstructed and state.get('seenEnding') is True and '—— 幕落 · 灯亮着 ——' in text)
