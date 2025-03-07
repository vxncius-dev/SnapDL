#!/usr/bin/env python3
import flet as ft
import asyncio, subprocess, pathlib, time, os, sys
from notifypy import Notify
from re import match, compile
from typing import Optional


notification = Notify()
app_title = "SnapDL"
app_icon = pathlib.Path(__file__).parent / "assets" / "icon.png"
window_icon = pathlib.Path(__file__).parent / "assets" / "icon.ico"
icon_sucess = pathlib.Path(__file__).parent / "assets" / "sucess.png"
icon_error = pathlib.Path(__file__).parent / "assets" / "error.png"


def send_notification(message):
    notification._notification_application_name = (
        f"{app_title} - Video and Music Downloader"
    )
    notification._notification_icon = app_icon
    notification.title, notification.message = app_title, message
    notification.send()


def main(page: ft.Page):
    page.title, page.window.icon = app_title, window_icon
    page.padding = 0
    page.bgcolor = ft.Colors.TRANSPARENT
    page.window.width, page.window.max_width = 450, 450
    page.window.height, page.window.max_height = 70, 70
    page.window.maximizable, page.window.frameless = False, True
    page.window.shadow = True
    page.window.center()

    def validate_link(link):
        if not link or len(link) > 500:
            link_input.content.hint_text = "Invalid link"
            page.update()
            return False

        url_pattern = compile(
            r"^(https?:\/\/)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(\/[^\s]*)?$"
        )
        if not url_pattern.match(link):
            link_input.content.value = ""
            link_input.content.hint_text = "Enter a valid link"
            page.update()
            return False

        return True

    def handle_close(e):
        page.close(banner)
        page.update()

    def download(link, mode):
        download_dir = (
            os.path.join(os.environ["USERPROFILE"], "Downloads")
            if sys.platform.startswith("win")
            else os.path.join(os.path.expanduser("~"), "Downloads")
        )
        output_template = os.path.join(download_dir, "%(title)s.%(ext)s")

        if mode == "audio":
            command = [
                "yt-dlp",
                "-f",
                "bestaudio",
                "--extract-audio",
                "--audio-format",
                "mp3",
                "-o",
                output_template,
                link,
            ]
        else:
            command = [
                "yt-dlp",
                "-f",
                "best",
                "-o",
                output_template,
                link,
            ]

        indicator.controls.clear()
        try:
            subprocess.run(
                command,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            indicator.controls.append(final_status(1))
            indicator.update()
            send_notification("Download concluído e salvo na pasta Downloads")

        except subprocess.CalledProcessError as e:
            send_notification(f"Erro no download: {e}")
            indicator.controls.append(final_status(0))
            indicator.update()

        finally:
            time.sleep(5)
            indicator.controls.clear()
            indicator.update()

    banner = ft.AlertDialog(
        content=ft.Container(
            ft.Row(
                [
                    ft.Text(
                        "Download as Video or Audio?",
                        color=ft.Colors.WHITE,
                        size=16,
                    ),
                    ft.Row(
                        [
                            ft.TextButton(
                                "Video",
                                on_click=lambda e: (
                                    handle_close(e),
                                    on_option_select(e),
                                ),
                            ),
                            ft.TextButton(
                                "Audio",
                                on_click=lambda e: (
                                    handle_close(e),
                                    on_option_select(e),
                                ),
                            ),
                        ]
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            width=450,
            height=70,
            border=ft.border.all(2, "#444444"),
            bgcolor="#111111",
            margin=ft.margin.only(bottom=-22),
            padding=ft.padding.only(top=10, left=20, right=20, bottom=10),
        ),
        shape=ft.RoundedRectangleBorder(radius=0),
        content_padding=ft.padding.all(0),
        inset_padding=ft.padding.all(0),
    )

    def on_option_select(e):
        mode = e.control.text.lower()
        link = link_input.content.value.strip()
        send_notification("Download started")

        if validate_link(link):
            indicator.controls.clear()
            indicator.controls.append(progress)
            indicator.controls[0].visible = True
            indicator.controls[0].update()
            indicator.update()
            download(link, mode)

    def show_options(e):
        if validate_link(link_input.content.value):
            page.open(banner)
            page.update()

    link_input = ft.Container(
        ft.TextField(
            "",
            hint_text="Paste your link here",
            border=ft.InputBorder.NONE,
            max_length=500,
            selection_color="#222222",
            on_submit=show_options,
            width=330,
        ),
        margin=ft.margin.only(bottom=5),
    )

    progress = ft.ProgressRing(
        width=16, height=16, stroke_width=2, color=ft.Colors.WHITE, visible=False
    )

    def final_status(status):
        return ft.Image(
            src=icon_sucess if status else icon_error,
            width=25,
            height=25,
            fit=ft.ImageFit.COVER,
        )

    indicator = ft.Row([progress])

    page.add(
        ft.WindowDragArea(
            ft.Container(
                ft.Row(
                    [
                        link_input,
                        ft.Container(
                            ft.Row(
                                [
                                    indicator,
                                    ft.IconButton(
                                        ft.Icons.CHEVRON_RIGHT,
                                        icon_color=ft.Colors.WHITE,
                                        on_click=lambda _: page.window.close(),
                                    ),
                                ]
                            ),
                            margin=ft.padding.only(left=-40),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    spacing=0,
                ),
                padding=ft.padding.only(left=20, right=10),
                bgcolor="#111111",
                height=70,
                border=ft.border.all(2, "#444444"),
            ),
            expand=True,
            maximizable=False,
        ),
    )

    def control_window_size(e):
        page.window.width, page.window.height = 450, 70
        page.window.update()

    page.on_window_event = control_window_size


ft.app(target=main)
