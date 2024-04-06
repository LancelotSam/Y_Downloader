import tkinter as tk
from tkinter import filedialog, simpledialog, Toplevel, messagebox, ttk, Canvas, Frame, Scrollbar
from urllib.parse import parse_qs, urlparse
import os
import re
import sqlite3
from pytube import YouTube, Playlist
from pytube.exceptions import PytubeError, RegexMatchError
import customtkinter 

# Create or connect to the SQLite database
conn = sqlite3.connect('youtube_playlists.db')
c = conn.cursor()

# Create a table for playlists if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS playlists
             (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, links TEXT)''')

def is_playlist_url(url):
    return 'list=' in url

def start_download():
    yt_link = link.get()
    message_label.configure(text=f"URL Changed: {yt_link}")
    download_dir = filedialog.askdirectory()
    if not download_dir:  # If user canceled download selection
        return

    create_new_folder = new_folder_var.get()
    final_download_dir = os.path.join(download_dir, folder_name_entry.get()) if create_new_folder and folder_name_entry.get() else download_dir

    if create_new_folder:
        folder_name = simpledialog.askstring("Folder Name", "Enter the name of the new folder:")
        if folder_name:
            final_download_dir = os.path.join(download_dir, folder_name)
            if not os.path.exists(final_download_dir):
                os.makedirs(final_download_dir)
        else:
            final_download_dir = download_dir
    else:
        final_download_dir = download_dir

    if is_playlist_url(yt_link):
        try: 
            download_playlist(yt_link, download_dir, download_format.get(), resolution_var.get(), new_folder_var.get(), folder_name_entry.get())
        except Exception as e:
            print(f"Error downloading playlist: {e}")
            finish_label.configure(text="Download error!", text_color="red")
    else:
        try:
            yt_object = YouTube(yt_link, on_progress_callback=on_progress)
            # use label to display available streams
            streams_list = yt_object.streams.filter(progressive=True)
            available_streams = "\n".join([f"Resolution: {stream.resolution}, Type: {stream.mime_type.split('/')[-1]}, Progressive: {'Yes' if stream.is_progressive else 'No'}" for stream in streams_list])
            message = f"Available streams:\n{available_streams}"
            message_label.configure(text=message)
            format_selection = download_format.get()
            resolution_selection = resolution_var.get()

            stream = None # Initializes stream
            if format_selection == "MP4":
            #attempt to download the seletion, progressive=True, file_extension='mp4').first()ed res, else use higehst vailable
                stream = yt_object.streams.filter(res=resolution_selection, progressive=True, file_extension='mp4').first()
                if not stream:
                    #print(f"resolution {resolution_selection} not available. Downloading highest available resolution.")
                    alternative_stream = yt_object.streams.get_highest_resolution()
                    message += f"\nSelected resolution not available. Choose a different resolution or download the highest available resolution: {alternative_stream.resolution}."
                    message_label.configure(text=message)
            elif format_selection == "MP3":
                stream = yt_object.streams.filter(only_audio=True).first()

            if stream:
                stream.download(final_download_dir)
                finish_label.configure(text="Downloaded!", text_color="green")
                title.configure(text=yt_object.title, text_color="white")
                c.execute("INSERT INTO playlists (title, links) VALUES (?, ?)", (yt_object.title, yt_link))
                conn.commit()
            else:
                finish_label.configure(text="Stream not found", text_color="red")
        except PytubeError as e:
            print(e)
            finish_label.configure(text="Download Error!", text_color="red")
        except RegexMatchError as e:
            print(f"Error: {e}")
            finish_label.configure(text="URL Error! Not a valid YouTube video URL.", text_color="red")

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
    resolutions = ["2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"]
    tk.OptionMenu(options_window, resolution_var, *resolutions).pack()

    new_folder_var = tk.BooleanVar()
    new_folder_checkbox = tk.Checkbutton(app, text="Create new folder", variable=new_folder_var)
    new_folder_checkbox.pack()
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


def download_playlist(playlist_url, download_dir, format_selection, resolution_selection, create_new_folder, folder_name):
    playlist = Playlist(playlist_url)
    message = f"URL Changed: {playlist_url}\n"
    message += f"Downloading videos in playlist: {playlist.title}\n"

    for video_url in playlist.video_urls:
        progressBar.set(0) # reset bar for each download
        yt_object = YouTube(video_url, on_progress_callback=on_progress)
        video_title = yt_object.title
        
        # Try to get a 1080p stream; fall back to the highest resolution if not available.
        if format_selection == "MP4":
            stream = yt_object.streams.filter(res="1080p", file_extension='mp4').first()
            if not stream:  # If 1080p is not available
                stream = yt_object.streams.filter(file_extension='mp4').get_highest_resolution()
                message += f"Resolution 1080p not available for video: {video_title}\n"
                message += f"Downloading in {stream.resolution} instead.\n"
            else:
                message += f"Downloading video: {video_title} in 1080p.\n"
        elif format_selection == "MP3":
            stream = yt_object.streams.filter(only_audio=True).first()
            message += f"Downloading audio: {video_title}\n"

        final_download_dir = os.path.join(download_dir, playlist.title)
        if not os.path.exists(final_download_dir):
            os.makedirs(final_download_dir)
        
        stream.download(output_path=final_download_dir)
        message += "Download completed for video: " + video_title + "\n"
        
        # Update the GUI with the download progress and resolution information
        message_label.configure(text=message)
        message_label.update_idletasks()


def on_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_download = total_size - bytes_remaining
    percentage_of_completion = (bytes_download / total_size) * 100
    progressBar.set(percentage_of_completion / 100)
    per = str(int(percentage_of_completion))
    p_percentage.configure(text=per + "%")
    app.update_idletasks() #updates gui after each download


def display_playlist():
    playlist_window = Toplevel(app)
    playlist_window.title("Playlist")
    playlist_window.geometry("600x400")  # Set an initial size for the window

    # Create a canvas and a scrollbar
    canvas = Canvas(playlist_window)
    scrollbar = Scrollbar(playlist_window, orient="vertical", command=canvas.yview)
    scrollable_frame = Frame(canvas)

    # Configure the canvas
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Create a window in the canvas for the scrollable_frame
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    # Pack the canvas and scrollbar into the window
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    c.execute("SELECT * FROM playlists")
    playlist = c.fetchall()

    if not playlist:
        label = customtkinter.CTkLabel(playlist_window,
                                       text="Playlist is empty",
                                       text_color="red")
        label.pack(padx=10, pady=10)
    else:
        for index, item in enumerate(playlist, start=1):
            title_label = customtkinter.CTkLabel(scrollable_frame, text=f"{index}. {item[1]}", text_color="gray25")
            title_label.pack(padx=10, pady=5)
            link_label = customtkinter.CTkLabel(scrollable_frame, text=item[2])
            link_label.pack(padx=10, pady=5)


def restart_app():
    #app.destroy() reste variable sinstead of destorying
    url_var.set("")
    download_format.set("Video")
    resolution_var.set("1080p")
    new_folder_var.set(False)
    folder_name_entry.delete(0, tk.END)
    finish_label.configure(text="", text_color="")
    p_percentage.configure(text="0%")
    progressBar.set(0)
    main()


def main():
    customtkinter.set_appearance_mode("System")
    customtkinter.set_default_color_theme("green")

    global app
    app = customtkinter.CTk()
    app.geometry("720x520")
    app.title("YPL Downloader")

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

download_format = tk.StringVar(value="MP4")
format_frame = tk.Frame(app)
format_frame.pack(pady=10)
tk.Radiobutton(format_frame, text="MP3 (Audio)", variable=download_format, value="MP3").pack(side=tk.LEFT)
tk.Radiobutton(format_frame, text="MP4 (Video)", variable=download_format, value="MP4").pack(side=tk.LEFT)

resolution_var = tk.StringVar(app)
resolution_var.set("1080p")
resolutions = ["2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"]
tk.OptionMenu(app, resolution_var, *resolutions).pack(pady=10)

new_folder_var = tk.BooleanVar()
tk.Checkbutton(app, text="Create new folder for download", variable=new_folder_var).pack(anchor=tk.W)
folder_name_entry = tk.Entry(app)
folder_name_entry.pack(pady=5)

global finish_label
finish_label = customtkinter.CTkLabel(app, text="")
finish_label.pack()

global message_label
message_label = customtkinter.CTkLabel(app, text="")
message_label.pack(pady=10)

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

