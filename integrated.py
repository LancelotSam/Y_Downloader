import tkinter as tk
import customtkinter
from pytube import YouTube, Playlist
from pytube.exceptions import PytubeError
from tkinter import filedialog, simpledialog
from urllib.parse import parse_qs, urlparse
import sqlite3
import os

# Create a new SQLite database or connect to an existing one
conn = sqlite3.connect('youtube_playlists.db')
c = conn.cursor()

# Create a table for playlists if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS playlists
             (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, links TEXT)''')


def start_download():
    ytLink = link.get()
    download_dir = filedialog.askdirectory()
    if not download_dir: # if user cancelled download selection
        return

    parsed_url = urlparse(ytLink)
    query_string = parse_qs(parsed_url.query)

    format_selection = download_format.get()
    resolution_selection = resolution_var.get()
    create_new_folder = new_folder_var.get()
    folder_name = folder_name_entry.get() if create_new_folder and folder_name_entry.get() else "Downloaded Playlist"

    if 'list' in query_string:
        download_playlist(ytLink, download_dir, format_selection, resolution_selection, create_new_folder, folder_name)
    else:
        # Single video download logic goes here, similar to the existing one
        try:
            ytObject = YouTube(ytLink, on_progress_callback=on_progress)
            if format_selection == "Video":
                stream = ytObject.streams.get_highest_resolution()
            elif format_selection == "Audio":
                stream = ytObject.streams.filter(only_audio=True).first()

            final_download_dir = os.path.join(download_dir, folder_name) if create_new_folder else download_dir
            if not os.path.exists(final_download_dir):
                os.makedirs(final_download_dir)

            stream.download(final_download_dir)
            finishLabel.configure(text="Downloaded!", text_color="green")
            title.configure(text=ytObject.title, text_color="white")

            # Insert the downloaded video into the database
            c.execute("INSERT INTO playlists (title, links) VALUES (?, ?)", (ytObject.title, ytLink))
            conn.commit()
        except PytubeError as e:
            print(e)
            finishLabel.configure(text="Download Error!", text_color="red")


def download_playlist_options(playlist_url, download_dir):
  # Create a new Toplevel window to host the new options
  options_window = tk.Toplevel(app)
  options_window.title("Download Options")

  # Format selection (MP3 or MP4)
  format_var = tk.StringVar(value="MP4")
  tk.Radiobutton(options_window,
                 text="MP3 (Audio)",
                 variable=format_var,
                 value="MP3").pack(anchor=tk.W)
  tk.Radiobutton(options_window,
                 text="MP4 (Video)",
                 variable=format_var,
                 value="MP4").pack(anchor=tk.W)

  # Resolution selection (placeholder values)
  resolution_var = tk.StringVar(value="1080p")
  resolutions = ["1080p", "720p", "480p", "360p"]  # Example resolutions
  tk.OptionMenu(options_window, resolution_var, *resolutions).pack()

  # New folder checkbox
  new_folder_var = tk.BooleanVar()
  tk.Checkbutton(options_window,
                 text="Create new folder for playlist",
                 variable=new_folder_var).pack(anchor=tk.W)

  def on_submit():
    #prompt for folder name
    folder_name = simpledialog.askstring("Folder Name", "Enter the name of the new folder:")
    if not folder_name: #if user didnt provide the folder name, use default
        folder_name = "New Playlist"
    options_window.destroy()
    download_playlist(playlist_url, download_dir, format_var.get(),
                      resolution_var.get(), new_folder_var.get(), folder_name)

  tk.Button(options_window, text="Download", command=on_submit).pack()


def download_playlist(playlist_url, download_dir, format, resolution, create_new_folder, folder_name):
    playlist = Playlist(playlist_url)

    # If creating a new folder, modify the download_dir accordingly
    if create_new_folder:
        download_dir = os.path.join(download_dir, folder_name)
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

    # function to update progress bar

    def on_progress(stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_of_completion = (bytes_downloaded / total_size) * 100

    print(f'Downloading videos in playlist: {playlist.title}')
    for video in playlist.videos:
        print(f'Downloading video: {video.title}')
        if format == "MP3":
            # Download only audio
            audio_stream = video.streams.filter(only_audio=True).first()
            audio_stream.download(output_path=download_dir, filename_prefix=f"{video.title}.mp3")
        else:
            # Download video with selected resolution
            # Note: Actual implementation should handle cases where the selected resolution is not available
            video_stream = video.streams.filter(res=resolution, file_extension='mp4').first()
            if video_stream:
                video_stream.download(download_dir, on_progress_callback=on_progress)
            else:
                print(f"Resolution {resolution} not available for video: {video.title}")
        print('Download completed')


    format_selection = download_format.get()
    resolution_selection = resolution_var.get()
    create_new_folder = new_folder_var.get()
    folder_name = folder_name_entry.get() if new_folder_var.get() else None

    if 'list' in query_string:
        # It's a playlist, show options window
        if download_dir:
            download_playlist_options(ytLink, download_dir)
        else:
            finishLable.configure(text="Download Cancelled", text_color="red")
    else:
        # It's a single video
        try:
            ytObject = YouTube(ytLink, on_progress_callback=on_progress)
            if download_format.get() == "Video":
                stream = ytObject.streams.get_highest_resolution()
            elif download_format.get() == "Audio":
                stream = ytObject.streams.filter(only_audio=True).first()

            if download_dir:
                stream.download(download_dir)
                finishLable.configure(text="Downloaded!")
                title.configure(text=ytObject.title, text_color="white")

                # Insert the downloaded video into the database
                c.execute("INSERT INTO playlists (title, links) VALUES (?, ?)", (ytObject.title, ytLink))
                conn.commit()
            else:
                finishLable.configure(text="Download Cancelled", text_color="red")
        except PytubeError as e:
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


def restart_app(app):
  app.destroy()  # Close the current app window
  main()  # Restart the app


def main():
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
    url_var = tk.StringVar()
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
download_format = tk.StringVar()
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

  # Format selection (MP3 or MP4)
download_format = tk.StringVar(value="MP4")  # Default value
format_frame = tk.Frame(app)
format_frame.pack(pady=10)
tk.Radiobutton(format_frame, text="MP3 (Audio)", variable=download_format, value="MP3").pack(side=tk.LEFT)
tk.Radiobutton(format_frame, text="MP4 (Video)", variable=download_format, value="MP4").pack(side=tk.LEFT)

    # Resolution selection
resolution_var = tk.StringVar(app)
resolution_var.set("1080p")  # default value
resolutions = ["1080p", "720p", "480p", "360p"]
tk.OptionMenu(app, resolution_var, *resolutions).pack(pady=10)

    # New folder option
new_folder_var = tk.BooleanVar()
tk.Checkbutton(app, text="Create new folder for download", variable=new_folder_var).pack(anchor=tk.W)
folder_name_entry = tk.Entry(app)
folder_name_entry.pack(pady=5)

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
