import tkinter as tk
from tkinter import filedialog, simpledialog, Toplevel
from urllib.parse import parse_qs, urlparse
import os
import sqlite3
from pytube import YouTube, Playlist
from pytube.exceptions import PytubeError
import customtkinter  # Assuming this is a custom module

# Create or connect to the SQLite database
conn = sqlite3.connect('youtube_playlists.db')
c = conn.cursor()

# Create a table for playlists if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS playlists
             (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, links TEXT)''')


def start_download():
    yt_link = link.get()
    download_dir = filedialog.askdirectory()
    if not download_dir:  # If user canceled download selection
        return

    parsed_url = urlparse(yt_link)
    query_string = parse_qs(parsed_url.query)

    format_selection = download_format.get()
    resolution_selection = resolution_var.get()
    create_new_folder = new_folder_var.get()
    folder_name = folder_name_entry.get() if create_new_folder and folder_name_entry.get() else "Downloaded Playlist"

    if 'list' in query_string:
        download_playlist(yt_link, download_dir, format_selection, resolution_selection, create_new_folder, folder_name)
    else:
        try:
            yt_object = YouTube(yt_link, on_progress_callback=on_progress)
            if format_selection == "Video":
                stream = yt_object.streams.get_highest_resolution()
            elif format_selection == "Audio":
                stream = yt_object.streams.filter(only_audio=True).first()

            final_download_dir = os.path.join(download_dir, folder_name) if create_new_folder else download_dir
            if not os.path.exists(final_download_dir):
                os.makedirs(final_download_dir)

            stream.download(final_download_dir)
            finish_label.configure(text="Downloaded!", text_color="green")
            title.configure(text=yt_object.title, text_color="white")

            # Insert the downloaded video into the database
            c.execute("INSERT INTO playlists (title, links) VALUES (?, ?)", (yt_object.title, yt_link))
            conn.commit()
        except PytubeError as e:
            print(e)
            finish_label.configure(text="Download Error!", text_color="red")


def download_playlist_options(playlist_url, download_dir):
    options_window = tk.Toplevel(app)
    options_window.title("Download Options")

    format_var = tk.StringVar(value="MP4")
    tk.Radiobutton(options_window,
                   text="MP3 (Audio)",
                   variable=format_var,
                   value="MP3").pack(anchor=tk.W)
    tk.Radiobutton(options_window,
                   text="MP4 (Video)",
                   variable=format_var,
                   value="MP4").pack(anchor=tk.W)

    resolution_var = tk.StringVar(value="1080p")
    resolutions = ["1080p", "720p", "480p", "360p"]
    tk.OptionMenu(options_window, resolution_var, *resolutions).pack()

    new_folder_var = tk.BooleanVar()
    tk.Checkbutton(options_window,
                   text="Create new folder for playlist",
                   variable=new_folder_var).pack(anchor=tk.W)

    def on_submit():
        folder_name = simpledialog.askstring("Folder Name", "Enter the name of the new folder:")
        if not folder_name:
            folder_name = "New Playlist"
        options_window.destroy()
        download_playlist(playlist_url, download_dir, format_var.get(),
                          resolution_var.get(), new_folder_var.get(), folder_name)

    tk.Button(options_window, text="Download", command=on_submit).pack()


def download_playlist(playlist_url, download_dir, format, resolution, create_new_folder, folder_name):
    playlist = Playlist(playlist_url)

    if create_new_folder:
        download_dir = os.path.join(download_dir, folder_name)
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

    def on_progress(stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_of_completion = (bytes_downloaded / total_size) * 100

    print(f'Downloading videos in playlist: {playlist.title}')
    for video in playlist.videos:
        print(f'Downloading video: {video.title}')
        if format == "MP3":
            audio_stream = video.streams.filter(only_audio=True).first()
            audio_stream.download(output_path=download_dir, filename_prefix=f"{video.title}.mp3")
        else:
            video_stream = video.streams.filter(res=resolution, file_extension='mp4').first()
            if video_stream:
                video_stream.download(download_dir, on_progress_callback=on_progress)
            else:
                print(f"Resolution {resolution} not available for video: {video.title}")
        print('Download completed')

    if 'list' in query_string:
        if download_dir:
            download_playlist_options(yt_link, download_dir)
        else:
            finish_label.configure(text="Download Cancelled", text_color="red")
    else:
        try:
            yt_object = YouTube(yt_link, on_progress_callback=on_progress)
            if download_format.get() == "Video":
                stream = yt_object.streams.get_highest_resolution()
            elif download_format.get() == "Audio":
                stream = yt_object.streams.filter(only_audio=True).first()

            if download_dir:
                stream.download(download_dir)
                finish_label.configure(text="Downloaded!")
                title.configure(text=yt_object.title, text_color="white")

                c.execute("INSERT INTO playlists (title, links) VALUES (?, ?)", (yt_object.title, yt_link))
                conn.commit()
            else:
                finish_label.configure(text="Download Cancelled", text_color="red")
        except PytubeError as e:
            print(e)
            finish_label.configure(text="Download Error!", text_color="red")


def on_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_download = total_size - bytes_remaining
    percentage_of_completion = bytes_download / total_size * 100
    per = str(int(percentage_of_completion))
    p_percentage.configure(text=per + "%")
    p_percentage.update()
    progressBar.set(float(percentage_of_completion / 100))


def display_playlist():
    playlist_window = Toplevel(app)
    playlist_window.title("Playlist")

    c.execute("SELECT * FROM playlists")
    playlist = c.fetchall()

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


def restart_app():
    app.destroy()
    main()


def main():
    customtkinter.set_appearance_mode("System")
    customtkinter.set_default_color_theme("green")

    global app
    app = customtkinter.CTk()
    app.geometry("720x520")
    app.title("YouTube Downloader")

    my_font = customtkinter.CTkFont(family="sans-serif", size=28)

    global title
    title = customtkinter.CTkLabel(app,
                                   text="Insert a YouTube link",
                                   font=my_font)
    title.pack(padx=10, pady=20)

    url_var = tk.StringVar()
    global link
    link = customtkinter.CTkEntry(app,
                                  width=350,
                                  height=40,
                                  font=customtkinter.CTkFont(family="sans-serif", size=16),
                                  textvariable=url_var)
    link.pack()

    global previous_url
    previous_url = ""

    app.after(100, check_for_change)  # Move this line to the end of the main function


def check_for_change():
    global previous_url
    current_url = link.get()
    if current_url != previous_url:
        previous_url = current_url
        print("URL Changed:", current_url)
    app.after(100, check_for_change)


main()  # Call the main function to start the application


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
        print("URL Changed:", current_url)
    app.after(100, check_for_change)


app.after(100, check_for_change)

global download_format
download_format = tk.StringVar()
download_format.set("Video")

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

download_format = tk.StringVar(value="MP4")
format_frame = tk.Frame(app)
format_frame.pack(pady=10)
tk.Radiobutton(format_frame, text="MP3 (Audio)", variable=download_format, value="MP3").pack(side=tk.LEFT)
tk.Radiobutton(format_frame, text="MP4 (Video)", variable=download_format, value="MP4").pack(side=tk.LEFT)

resolution_var = tk.StringVar(app)
resolution_var.set("1080p")
resolutions = ["1080p", "720p", "480p", "360p"]
tk.OptionMenu(app, resolution_var, *resolutions).pack(pady=10)

new_folder_var = tk.BooleanVar()
tk.Checkbutton(app, text="Create new folder for download", variable=new_folder_var).pack(anchor=tk.W)
folder_name_entry = tk.Entry(app)
folder_name_entry.pack(pady=5)

global finish_label
finish_label = customtkinter.CTkLabel(app, text="")
finish_label.pack()

global p_percentage
p_percentage = customtkinter.CTkLabel(app, text="0%")
p_percentage.pack()

global progressBar
progressBar = customtkinter.CTkProgressBar(app, width=400)
progressBar.set(0)
progressBar.pack(padx=10, pady=10)

download = customtkinter.CTkButton(app,
                                   text="Download",
                                   command=start_download)
download.pack(padx=10, pady=10)

display_playlist_button = customtkinter.CTkButton(app,
                                                  text="Display Playlist",
                                                  command=display_playlist)
display_playlist_button.pack(padx=10, pady=10)

refresh_button = customtkinter.CTkButton(app,
                                         text="Refresh",
                                         command=restart_app)
refresh_button.pack(padx=10, pady=10)

app.mainloop()

# Close the database connection
conn.close()

