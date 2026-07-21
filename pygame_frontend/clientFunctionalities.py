import pywhatkit as kit

def play_song(song, artist):
    query = f"{song} {artist}"
    if song == 'any' and artist == 'unknown':
        query = 'song'
    elif song == 'any':
        query = f'{artist} songs'
    elif artist == 'unknown':
        query = song
    kit.playonyt(query)
