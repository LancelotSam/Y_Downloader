from pytube import Playlist

playlist_url = 'https://www.youtube.com/playlist?list=PLojaLLEEkd0BI9DjLsQvpNBYTq643gpql'
playlist = Playlist(playlist_url)

# Skip printing the playlist title to bypass the error
for video in playlist:
    print(f'Downloading video: {video.title}')
    video.streams.first().download()
    print('Downloaded')

