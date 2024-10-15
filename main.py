#!/usr/bin/env python3
from os import path, makedirs, getenv, rename, listdir, remove, rmdir, getcwd
from ctypes import windll
from yt_dlp import YoutubeDL
from re import match, compile
from requests import get, ConnectionError
import flet as ft
from pathlib import Path
from typing import Optional, Dict, Tuple
from subprocess import run, PIPE
from zipfile import ZipFile


class SnapDL:
    def __init__(self) -> None:
        self.app_name: str = "SnapDL"
        self.icon: Path = Path(__file__).parent / "assets" / "icon.png"
        self.icon_window: Path = Path(__file__).parent / "assets" / "icon.ico"
        self.width: int = 400
        self.height: int = 60
        self.link_download: str = ""
        self.downloading_type: bool = True
        self.downloading: bool = False
        self.ffmpeg_dir: Path = Path(getcwd()) / "ffmpeg"

        if self.is_ffmpeg_installed():
            print("FFmpeg está instalado.")
        else:
            print("FFmpeg não está instalado ou não foi encontrado. Baixando...")
            self.download_ffmpeg()
            
        self.ffmpeg_path: Path = Path(__file__).parent / "ffmpeg" / "bin" / "ffmpeg.exe"
        self.ffprobe_path: Path = Path(__file__).parent / "ffmpeg" / "bin" / "ffprobe.exe"
        self.default_video_icon: Path = Path(__file__).parent / "assets" / "video.png"
        self.default_music_icon: Path = Path(__file__).parent / "assets" / "music.png"
        self.conclude_icon: Path = Path(__file__).parent / "assets" / "check.png"
        self.fail_icon: Path = Path(__file__).parent / "assets" / "error.png"
        ft.app(target=self.main, assets_dir="./assets")
        

    def is_ffmpeg_installed(self) -> bool:
        return self.ffmpeg_dir.exists() and (self.ffmpeg_dir / "bin" / "ffmpeg.exe").exists()

    def download_ffmpeg(self) -> None:
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        response = get(url)
        zip_file_path = "ffmpeg-release-essentials.zip"
        with open(zip_file_path, "wb") as f:
            f.write(response.content)

        self.extract_zip(zip_file_path)

        if not self.ffmpeg_dir.exists():
            makedirs(self.ffmpeg_dir)

        extracted_dir = next(Path(getcwd()).glob("ffmpeg-*-essentials_build"), None)
        if extracted_dir:
            for item in extracted_dir.glob("*"):
                destination = self.ffmpeg_dir / item.name
                if item.is_dir():
                    item.rename(destination)
                else:
                    item.rename(destination)

            for item in extracted_dir.glob("*"):
                if item.is_dir():
                    rmdir(item)
                else:
                    remove(item)
            rmdir(extracted_dir)

        remove(zip_file_path)

    def extract_zip(self, file_path: str) -> None:
        with ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(getcwd())

    def get_screen_dimensions(self) -> Tuple[int, int]:
        user32 = windll.user32
        screen_width: int = user32.GetSystemMetrics(0)
        screen_height: int = user32.GetSystemMetrics(1)
        return screen_width, screen_height

    def icon_(self, src: Path) -> ft.Image:
        return ft.Image(src=src, width=20, height=20)

    def main(self, page: ft.Page) -> None:
        self.page = page
        page.title = self.app_name
        page.window.icon = self.icon_window
        page.window.width, page.window.height = self.width, self.height
        page.window.max_width, page.window.max_height = self.width, self.height
        screen_width, screen_height = self.get_screen_dimensions()
        page.window.left = screen_width - self.width - 16
        page.window.top = screen_height - self.height - 65
        page.window.resizable = False
        page.window.maximizable = False
        page.window.title_bar_hidden = True
        page.window.title_bar_buttons_hidden = True
        page.bgcolor = "#111111"
        page.window.on_close = self.cleanup
        page.fonts = {"JetBrainsMono": "./fonts/JetBrainsMono-Regular.ttf"}
        page.theme = ft.Theme(font_family="JetBrainsMono")

        self.video_icon: ft.Image = self.icon_(self.default_video_icon)
        self.music_icon: ft.Image = self.icon_(self.default_music_icon)
        self.video_indicator: ft.Container = ft.Container()
        self.music_indicator: ft.Container = ft.Container()

        self.search_input: ft.TextField = ft.TextField(
            hint_text="Cole seu link aqui",
            width=282,
            height=60,
            text_size=14,
            border=ft.InputBorder.NONE,
            color=ft.colors.WHITE,
            on_change=lambda e: (
                setattr(self, 'link_download', e.control.value),
                self.reset_hint_text()
            ),
            on_submit=lambda e: self.validate_link(self.link_download, False),
        )

        self.close_button: ft.Container = ft.Container(
            content=ft.Icon(
                name=ft.icons.CHEVRON_RIGHT,
                color=ft.colors.GREY,
                size=20,
                opacity=.4,
            ),
            margin=ft.margin.only(left=-8),
            on_click=lambda e: self.cleanup(e),
        )

        page.add(
            ft.WindowDragArea(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(
                                content=self.search_input,
                                padding=ft.padding.only(left=5),
                                margin=ft.margin.only(top=-8),
                                height=60,
                            ),
                            self.video_indicator,
                            self.music_indicator,
                            self.close_button,
                        ]
                    ),
                ),
                expand=True
            ),
        )

        self.update_buttons()

    def reset_hint_text(self) -> None:
        self.search_input.hint_text = "Cole seu link aqui"
        self.page.update()

    def validate_link(self, link: str, audio: bool) -> None:
        if not link or self.downloading:
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

    def cleanup(self, e) -> None:
        self.clear_temp_content()
        e.page.window.close()

    def get_music_folder(self) -> Path:
        return Path.home() / "Music"

    def get_video_folder(self) -> Path:
        return Path.home() / "Videos"

    def download(self, link: str, audio: Optional[bool] = False) -> None:
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

        for plataforma, pattern in link_patterns.items():
            if match(pattern, link):
                if plataforma == "reels do Instagram":
                    ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio' if audio else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                else:
                    self.toast_info(f"Links do {plataforma.capitalize()} ainda não têm suporte no momento.", "Estamos trabalhando nisso!")
                    self.reset()
                    return
            else:
                ydl_opts['format'] = 'best' if audio else 'best'

        self.downloading = True
        self.downloading_type = not audio
        self.update_buttons()

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

            if downloaded_file.endswith('.webp'):
                output_mp4 = final_path.rsplit('.', 1)[0] + '.mp4'
            elif downloaded_file.endswith('.webm') and audio:
                output_mp3 = final_path.rsplit('.', 1)[0] + '.mp3'

            self.icon_status(True, audio)
            self.toast_info("Download finalizado", "O arquivo foi baixado com sucesso.", final_path, audio)

        except ConnectionError:
            self.toast_info("Erro de conexão", "Verifique sua internet.")
            self.icon_status(False, audio)
        except FileNotFoundError as e:
            self.toast_info("Erro", str(e))
            self.icon_status(False, audio)
        except Exception:
            self.toast_info("Erro inesperado", "Ocorreu um erro inesperado.\nTente novamente em alguns instantes.")
            self.icon_status(False, audio)
        finally:
            self.clear_temp_content()

        from time import sleep
        sleep(4)
        self.reset()

    def reset(self) -> None:
        self.link_download = ""
        self.search_input.value = ""
        self.downloading = False
        self.update_buttons()

    def icon_status(self, conclude: bool, audio: bool) -> None:
        if audio:
            self.music_icon.src = self.conclude_icon if conclude else self.fail_icon
            self.music_indicator.content = self.music_icon
        else:
            self.video_icon.src = self.conclude_icon if conclude else self.fail_icon
            self.video_indicator.content = self.video_icon
        self.page.update()

    def update_buttons(self) -> None:
        size: int = 20
        loading: ft.ProgressRing = ft.ProgressRing(width=size, height=size)

        if self.downloading:
            indicator = self.video_indicator if self.downloading_type else self.music_indicator
            indicator.content = loading
        else:
            self.video_indicator.content = self.icon_(self.default_video_icon)
            self.video_indicator.on_click = lambda _: self.download(self.link_download, False)
            self.music_indicator.content = self.icon_(self.default_music_icon)
            self.music_indicator.on_click = lambda _: self.download(self.link_download, True)

        self.page.update()

    def toast_info(self, title: str, msg: str, path: Optional[str] = None, audio: Optional[bool] = None) -> None:
        from winotify import Notification
        toast = Notification(
            app_id=self.app_name,
            title=title,
            msg=msg,
            duration="short",
            icon=self.icon,
        )

        if path:
            if audio is not None:
                local_files: str = str(self.get_music_folder()) if audio else str(self.get_video_folder())
                toast.add_actions(label="Abrir diretório", launch=f"file:///{local_files}")

            toast.add_actions(label="Abrir arquivo", launch=f"file:///{path}")

        toast.show()


if __name__ == "__main__":
    SnapDL()
