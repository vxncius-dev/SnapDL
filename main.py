#!/usr/bin/env python3
from os import path, makedirs, getenv, rename, listdir, remove, rmdir
from ctypes import windll
from yt_dlp import YoutubeDL
from re import match, compile
from winotify import Notification
from requests import exceptions
from pathlib import Path
from typing import Optional, Dict, Tuple
from time import sleep
import tkinter as tk
from tkinter import *
from ctypes import windll

GWL_EXSTYLE = -20
WS_EX_APPWINDOW = 0x00040000
WS_EX_TOOLWINDOW = 0x00000080


class PlaceholderEntry(tk.Entry):
    def __init__(self, master=None, placeholder="", *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)
        self.placeholder = placeholder
        self.bind("<FocusIn>", self.on_focus_in)
        self.bind("<FocusOut>", self.on_focus_out)
        self.insert(0, self.placeholder)
        
    def on_focus_in(self, event) -> None:
        if self.get() == self.placeholder:
            self.delete(0, tk.END)

    def on_focus_out(self, event) -> None:
        if not self.get():
            self.insert(0, self.placeholder)


class SnapDL:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.offset_x = 0
        self.offset_y = 0
        self.downloading_type: bool = True
        self.downloading: bool = False
        self.is_minimized = False      
        self.main()
        
    def main(self):
        self.ffmpeg_path: Path = Path(__file__).parent / "src"  / "ffmpeg" / "bin" / "ffmpeg.exe"
        self.ffmprobe_path: Path = Path(__file__).parent / "src"  / "ffmpeg" / "bin" / "ffmprobe.exe"
        self.icon: Path = Path(__file__).parent / "src" / "assets" / "icon.png"
        self.window_icon: Path = Path(__file__).parent / "src" / "assets" / "icon.ico"
        self.w_size, self.h_size = 400, 60 
        self.screen_width, self.screen_height = self.get_screen_dimensions()
        pos_x, pos_y = self.screen_width - self.w_size - 15, self.screen_height - self.h_size - 65
        self.root = tk.Tk()
        self.root.title("SnapDL")
        self.root.iconbitmap(self.window_icon)
        self.root.geometry(f"{self.w_size}x{self.h_size}+{pos_x}+{pos_y}")
        self.root.overrideredirect(True)
        self.root.config(bg='grey')
        self.root.attributes("-transparentcolor", "grey")
        self.video_img = PhotoImage(file=r"./src/assets/video.png")
        self.music_img = PhotoImage(file=r"./src/assets/music.png")
        self.close_img = PhotoImage(file=r"./src/assets/close.png")
        self.canvas = Canvas(self.root, bg="grey", highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.round_rectangle(0, 0, self.w_size - 2, self.h_size - 2, radius=19, fill="#111111", outline="#444444", width=1)
        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.move_window)
        self.build()
        self.root.after(10, lambda: self.set_appwindow())
        self.root.protocol("WM_DELETE_WINDOW", self.toggle_minimize_restore)
        self.root.mainloop()

    def minimize(self):
        self.root.withdraw()
        self.is_minimized = True

    def restore_window(self):
        self.root.deiconify()
        self.is_minimized = False
        
    def toggle_minimize_restore(self):
        self.restore_window() if self.is_minimized else self.minimize()   

    def set_appwindow(self):
        hwnd = windll.user32.GetParent(self.root.winfo_id())
        style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = style & ~WS_EX_TOOLWINDOW
        style = style | WS_EX_APPWINDOW
        windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        self.root.wm_withdraw()
        self.root.after(10, self.root.wm_deiconify)
        
    def round_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs) -> int:
        points = [
            x1 + radius, y1, x1 + radius, y1, x2 - radius, y1, x2 - radius, y1, x2, y1,
            x2, y1 + radius, x2, y1 + radius, x2, y2 - radius, x2, y2 - radius, x2, y2,
            x2 - radius, y2, x2 - radius, y2, x1 + radius, y2, x1 + radius, y2, x1, y2,
            x1, y2 - radius, x1, y2 - radius, x1, y1 + radius, x1, y1 + radius, x1, y1
        ]
        return self.canvas.create_polygon(points, **kwargs, smooth=True)
        
    def build(self) -> None:
        self.link_input = PlaceholderEntry(self.root, width=30, placeholder="Cole seu link aqui",
            borderwidth=0, highlightthickness=0, font=("JetBrainsMono", 12), insertbackground="#ccc",
            background="#111", fg="#fff")
        self.link_input.grid(row=0, column=0, padx=(15, 5), pady=10)
        
        self.video_button = tk.Button(self.root, image=self.video_img, bg="#111", borderwidth=0, highlightthickness=0, 
                           command=lambda: self.validate_link(self.link_input.get(), False), activebackground="#111")
        self.video_button.grid(row=0, column=1, padx=7, pady=20)

        self.music_button = tk.Button(self.root, image=self.music_img, bg="#111", borderwidth=0, highlightthickness=0,
                           command=lambda: self.validate_link(self.link_input.get(), True), activebackground="#111")
        self.music_button.grid(row=0, column=2, padx=7, pady=20)
        
        close_button = tk.Button(self.root, image=self.close_img, bg="#111", borderwidth=0, highlightthickness=0, 
                           command=lambda: self.root.destroy(), activebackground="#111")
        close_button.grid(row=0, column=3, padx=7, pady=20)
        
    def start_move(self, event) -> None:
        self.offset_x = event.x
        self.offset_y = event.y

    def move_window(self, event) -> None:
        x = event.x_root - self.offset_x
        y = event.y_root - self.offset_y
        self.root.geometry(f"+{x}+{y}")
      
    def get_screen_dimensions(self) -> Tuple[int, int]:
        user32 = windll.user32
        screen_width: int = user32.GetSystemMetrics(0)
        screen_height: int = user32.GetSystemMetrics(1)
        return screen_width, screen_height

    def validate_link(self, link: str, audio: bool) -> None:
        if link == "Cole seu link aqui" or not link.strip() or self.downloading:
            return

        link = link.strip()
        max_url_length = 500
        if len(link) > max_url_length:
            self.toast_info("Erro", f"O link excede o limite de {max_url_length} caracteres.")
            return

        url_pattern = compile(r'^(https?:\/\/)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(\/[^\s]*)?$')
        if not url_pattern.match(link):
            self.search_input.value = ""
            self.search_input.hint_text = "Insira um link válido"
            self.page.update()
            return

        self.download(link, audio)

    def get_music_folder(self) -> Path:
        return Path.home() / "Music"

    def get_video_folder(self) -> Path:
        return Path.home() / "Videos"

    def download(self, link: str, audio: Optional[bool] = False) -> None:
        if not link:
            return
        
        self.video_button.config(state=tk.DISABLED)
        self.music_button.config(state=tk.DISABLED)
    
        if any(service in link for service in ["deezer", "soundcloud", "youtube_music", "apple_music"]):
            audio = True

        temp_folder = path.join(getenv("TEMP"), "downloader_temp")
        makedirs(temp_folder, exist_ok=True)
        output_path_temp = path.join(temp_folder, f'%(title)s.%(ext)s')
        link_patterns: Dict[str, str] = {
            "reels do Instagram": r'https://www\.instagram\.com/reel/[A-Za-z0-9]+/?',
            "twitter": r'https://x\.com/[A-Za-z0-9_]+/status/[0-9]+',
            "spotify": r"(https?://(open|play)\.spotify\.com/(track|album|playlist|artist)/[^\s]+|"
                       r"https?://spotify\.com/(track|album|playlist|artist)/[^\s]+|"
                       r"https?://(www\.)?spotify\.com/[^\s]+|"
                       r"https?://(open|play)\.spotify\.com/(intl-[a-z]{2}/)?(track|album|playlist|artist)/[^\s]+)",
            "deezer": r"(https?://(www\.)?deezer\.com/([a-z]{2}/)?(track|album|playlist|artist)/[^\s]+|"
                       r"https?://deezer\.page\.link/[^\s]+)"
        }

        ydl_opts = {
            'outtmpl': output_path_temp,
            'merge_output_format': 'mp4' if not audio else None,
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'aac'}] if audio else [],
            'ffmpeg_location': str(self.ffmpeg_path),
        }
        
        if self.screen_height > 1080:
            best_format = 'bestvideo[height<=?2160]+bestaudio[ext=m4a]/best[height<=?2160]'
        else:
            best_format = 'bestvideo[height<=?1080]+bestaudio[ext=m4a]/best[height<=?1080]'

        for plataforma, pattern in link_patterns.items():
            if match(pattern, link):
                if plataforma == "reels do Instagram":
                    ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio' if audio else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                else:
                    self.toast_info(f"Links do {plataforma.capitalize()} ainda não têm suporte no momento.", "Estamos trabalhando nisso!")
                    self.reset()
                    return
            else:
                ydl_opts['format'] = 'bestaudio[ext=m4a]/best' if audio else best_format

        self.downloading = True
        self.downloading_type = not audio

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])

            downloaded_files = listdir(temp_folder)
            if not downloaded_files:
                raise FileNotFoundError("Nenhum arquivo baixado foi encontrado.")

            downloaded_file = next((f for f in downloaded_files if f.endswith(('.mp4', '.mp3', '.m4a', 'webm'))), None)
            if not downloaded_file:
                raise FileNotFoundError("Arquivo de mídia não encontrado na pasta temporária.")

            output_ = str(self.get_music_folder()) if audio else str(self.get_video_folder())
            final_path = path.join(output_, downloaded_file)
            base_name, ext = path.splitext(downloaded_file)
            count = 1

            while path.exists(final_path):
                final_path = path.join(output_, f"{base_name}-{count}{ext}")
                count += 1

            rename(path.join(temp_folder, downloaded_file), final_path)
            self.icon_status(True, audio)
            self.toast_info("Download finalizado", "O arquivo foi baixado com sucesso.", final_path, audio)

        except exceptions.ConnectionError:
            self.toast_info("Erro de conexão", "Verifique sua internet.")
            self.icon_status(False, audio)
        except FileNotFoundError as e:
            self.toast_info("Erro", str(e))
            self.icon_status(False, audio)
        except Exception:
            self.toast_info("Erro inesperado", "Ocorreu um erro inesperado.\nTente novamente em alguns instantes.")
            self.icon_status(False, audio)
        finally:
            self.video_button.config(state=tk.NORMAL)
            self.music_button.config(state=tk.NORMAL)
            self.clear_temp_content()
    
    def icon_status(self, conclude: bool, audio: bool) -> None:
        success_icon = PhotoImage(file=r"./src/assets/check.png")
        error_icon = PhotoImage(file=r"./src/assets/error.png")

        if audio:
            if conclude:
                self.music_button.config(image=success_icon)
                self.music_button.image = success_icon
            else:
                self.music_button.config(image=error_icon)
                self.music_button.image = error_icon
        else:
            if conclude:
                self.video_button.config(image=success_icon)
                self.video_button.image = success_icon
            else:
                self.video_button.config(image=error_icon)
                self.video_button.image = error_icon

        self.root.update()

    def toast_info(self, title: str, msg: str, path: Optional[str] = None, audio: Optional[bool] = None) -> None:
        toast = Notification( app_id="SnapDL", title=title, msg=msg, duration="short", icon=self.icon)
        if path:
            if audio is not None:
                local_files: str = str(self.get_music_folder()) if audio else str(self.get_video_folder())
                toast.add_actions(label="Abrir diretório", launch=f"file:///{local_files}")
            toast.add_actions(label="Abrir arquivo", launch=f"file:///{path}")
        toast.show()

    def clear_temp_content(self) -> None:
        temp_folder = path.join(getenv("TEMP"), "downloader_temp")
        if path.exists(temp_folder):
            for file in listdir(temp_folder):
                try:
                    remove(path.join(temp_folder, file))
                except Exception as ex:
                    print(f"Erro ao remover arquivo temporário: {ex}")
            try:
                rmdir(temp_folder)
            except Exception as ex:
                print(f"Erro ao remover diretório temporário: {ex}")


if __name__ == "__main__":
    SnapDL()
