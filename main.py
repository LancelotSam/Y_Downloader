import tkinter
import customtkinter
import pytube
import urllib.parse
import sqlite3
from pytube import YouTube, Playlist
from pytube.exceptions import PytubeError
from tkinter import filedialog, Toplevel
from urllib.parse import parse_qs, urlparse

# Create a new SQLite database or connect to an existing one
conn = sqlite3.connect('youtube_playlists.db')
c = conn.cursor()

# Create a table for playlists if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS playlists
             (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, links TEXT)''')


def start_download():
  try:
    ytLink = link.get()
    ytObject = YouTube(ytLink, on_progress_callback=on_progress)

    if download_format.get() == "Video":
      stream = ytObject.streams.get_highest_resolution()
    elif download_format.get() == "Audio":
      stream = ytObject.streams.filter(only_audio=True).first()

    # Select download directory
    download_dir = filedialog.askdirectory()
    if download_dir:
      stream.download(download_dir)
      finishLable.configure(text="Downloaded!")
    else:
      finishLable.configure(text="Download Cancelled", text_color="red")

    title.configure(text=ytObject.title, text_color="white")

    # Insert the downloaded video into the playlist
    c.execute("INSERT INTO playlists (title, links) VALUES (?, ?)",
              (ytObject.title, ytLink))
    conn.commit()
  except Exception as e:
    print(e)
    finishLable.configure(text="Download Error!", text_color="red")


def on_progress(stream, chunk, bytes_remaining):
  total_size = stream.filesize
  bytes_download = total_size - bytes_remaining
  percentage_of_completion = bytes_download / total_size * 100
  per = str(int(percentage_of_completion))
  pPercentage.configure(text=per + "%")
  pPercentage.update()

  # Update progress bar
  progressBar.set(float(percentage_of_completion / 100))


def display_playlist():
  playlist_window = Toplevel(app)
  playlist_window.title("Playlist")

  conn = sqlite3.connect('youtube_playlists.db')
  c = conn.cursor()
  c.execute("SELECT * FROM playlists")
  playlist = c.fetchall()
  conn.close()

  if not playlist:
    label = customtkinter.CTkLabel(playlist_window,
                                   text="Playlist is empty",
                                   text_color="red")
    label.pack(padx=10, pady=10)
  else:
    for index, item in enumerate(playlist, start=1):
      title_label = customtkinter.CTkLabel(playlist_window,
                                           text=f"{index}. {item[1]}",
                                           text_color="gray25")
      title_label.pack(padx=10, pady=5)
      link_label = customtkinter.CTkLabel(playlist_window, text=item[2])
      link_label.pack(padx=10, pady=5)

def download_playlist(playlist_url):
    try:
        playlist = Playlist(playlist_url)
        # Ensure the playlist object fetches the video URLs upon initialization
        playlist._video_regex = None  # necessary due to a pytube issue that prevents video URLs from being fetched.
        for video_url in playlist.video_urls:
            yt = YouTube(video_url)
            stream = yt.streams.get_highest_resolution()
            stream.download(output_path='your_output_directory')
            print(f'Downloaded: {yt.title}')
    except PytubeError as e:  # Catching a general Pytube error if specific ones like KeyError occur
        print(f"An error occurred: {e}")

def extract_video_info(url):
    """Extract video ID, playlist ID, and index from the URL."""
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    video_id = query_params.get('v', [None])[0]
    playlist_id = query_params.get('list', [None])[0]
    index = int(query_params.get('index', [1])[0])  # Default to 1 if not found
    return video_id, playlist_id, index

def download_video_by_id(video_id, output_directory):
    """Download a video given its ID."""
    try:
        yt = YouTube(f'https://www.youtube.com/watch?v={video_id}')
        stream = yt.streams.get_highest_resolution()
        stream.download(output_path=output_directory)
        print(f'Downloaded: {yt.title}')
    except Exception as e:
        print(f"Failed to download video {video_id}: {str(e)}")

def download_videos_in_sequence(start_url, end_index, output_directory):
    """Attempt to download a sequence of videos from a dynamic playlist."""
    video_id, playlist_id, current_index = extract_video_info(start_url)

    while current_index <= end_index:
        download_video_by_id(video_id, output_directory)
        current_index += 1
        # Assuming the video IDs aren't predictable, we cannot just increment video_id.
        # Instead, we rely on the fact that this function is a conceptual approach and 
        # would need actual video ID fetching logic here for a real application.

        # Fetch the next video ID (this part is conceptual and not directly implementable without API or scraping logic)
        # video_id = fetch_next_video_id(playlist_id, current_index)
        # This is a placeholder to indicate where logic to fetch the next video ID would go.
        # Implementing this directly violates YouTube's Terms of Service and is not recommended.

# Example usage
start_url = 'https://www.youtube.com/watch?v=2FMtxACKlYM&list=RDboiwEmHFrRk&index=1'
end_index = 3  # Hypothetical end index if you wanted to stop after a certain number of videos
output_directory = 'your_output_directory'

download_videos_in_sequence(start_url, end_index, output_directory)

def restart_app():
  app.destroy()  # Close the current app window
  main()  # Restart the app


def main():
  # System Settings
  customtkinter.set_appearance_mode("System")
  customtkinter.set_default_color_theme("green")

  # App frame
  global app
  app = customtkinter.CTk()
  app.geometry("720x520")
  app.title("YouTube Downloader")

  # Font
  my_font = customtkinter.CTkFont(family="sans-serif", size=28)

  # Adding UI Elements
  global title
  title = customtkinter.CTkLabel(app,
                                 text="Insert a YouTube link",
                                 font=my_font)
  title.pack(padx=10, pady=20)

  # Link input
  url_var = tkinter.StringVar()
  global link
  link = customtkinter.CTkEntry(app,
                                width=350,
                                height=40,
                                font=customtkinter.CTkFont(family="sans-serif",
                                                           size=16),
                                textvariable=url_var)
  link.pack()

  global previous_url
  previous_url = ""

  def paste_from_clipboard():
      try:
          url_var.set(app.clipboard_get())
      except:
          print("Clipboard access failed or empty")
          paste_button = customtkinter.CTkButton(app,
                  text="Paste URL",
                  command=paste_from_clipboard)
          paste_button.pack(padx=10, pady=5)

  def check_for_change():
    global previous_url
    current_url = link.get()
    if current_url != previous_url:
      previous_url = current_url
      # Place any logic you want to execute on URL change here
      print("URL Changed:", current_url)
    app.after(100, check_for_change)  # Check every 100ms

  app.after(100, check_for_change)  # Initial call to start the check loop

  # Download format selection
  global download_format
  download_format = tkinter.StringVar()
  download_format.set("Video")  # Default selection

  video_radio = customtkinter.CTkRadioButton(app,
                                             text="Video",
                                             variable=download_format,
                                             value="Video")
  video_radio.pack()

  audio_radio = customtkinter.CTkRadioButton(app,
                                             text="Audio",
                                             variable=download_format,
                                             value="Audio")
  audio_radio.pack()

  # Finished Downloading
  global finishLable
  finishLable = customtkinter.CTkLabel(app, text="")
  finishLable.pack()

  # Progress percentage
  global pPercentage
  pPercentage = customtkinter.CTkLabel(app, text="0%")
  pPercentage.pack()

  global progressBar
  progressBar = customtkinter.CTkProgressBar(app, width=400)
  progressBar.set(0)
  progressBar.pack(padx=10, pady=10)

  # Download Button
  download = customtkinter.CTkButton(app,
                                     text="Download",
                                     command=start_download)
  download.pack(padx=10, pady=10)

  # Display Playlist Button
  display_playlist_button = customtkinter.CTkButton(app,
                                                    text="Display Playlist",
                                                    command=display_playlist)
  display_playlist_button.pack(padx=10, pady=10)

  # Refresh Button
  refresh_button = customtkinter.CTkButton(app,
                                           text="Refresh",
                                           command=restart_app)
  refresh_button.pack(padx=10, pady=10)

  app.mainloop()


if __name__ == "__main__":
  main()

# Close the database connection when the app is closed
conn.close()

