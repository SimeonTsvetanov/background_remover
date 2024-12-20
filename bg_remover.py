# pyinstaller --onefile -w --icon=icon.ico bg_remover.py
# flet pack bg_remover.py --name "Background Remover" --icon icon.ico

import flet as ft
from rembg import remove
from PIL import Image
import io
import os
import threading
import time
import traceback
from datetime import datetime
import sys


def main(page: ft.Page):
    page.title = 'Background Remover'
    page.icon = "icon.ico"  # Set the app icon to the new image icon
    page.vertical_alignment = 'center'
    page.horizontal_alignment = 'center'
    page.window.maximized = True  # Set the app to fill the available window

    def select_image(e):
        file_picker.pick_files()

    def file_picker_result(e):
        if not file_picker.result or not file_picker.result.files:
            return
        global image_path
        image_path = file_picker.result.files[0].path
        if not is_valid_image(image_path):
            show_invalid_prompt()
        else:
            start_conversion()

    def is_valid_image(file_path):
        try:
            Image.open(file_path).verify()
            return True
        except:
            return False

    def show_invalid_prompt():
        invalid_dialog.visible = True
        page.update()

    def hide_invalid_prompt(e):
        invalid_dialog.visible = False
        page.update()

    def start_conversion():
        loading_text.value = "Processing image, please wait"
        page.update()
        # Start the loading animation in a new thread
        threading.Thread(target=loading_animation).start()
        base_name = os.path.basename(image_path)
        name, ext = os.path.splitext(base_name)
        output_path = os.path.join(os.path.dirname(image_path), f"{name}_removed_background{ext}")
        convert(image_path, output_path)

    def convert(file_path, output_path):
        try:
            with open(file_path, "rb") as input_file:
                input_image = input_file.read()

            if input_image is None:
                raise ValueError("Failed to read input image")

            output_image = remove(input_image, progress=False)  # Disable progress bar

            if output_image is None:
                raise ValueError("Failed to process image")

            image = Image.open(io.BytesIO(output_image))
            image.save(output_path, "PNG")

            loading_text.value = "Image converted and saved successfully!"
            page.update()
            # Schedule a task to reset the message after 4 seconds
            threading.Timer(4.0, reset_message).start()
        except Exception as ex:
            log_error(ex)
            loading_text.value = f"Error: {ex}"
            page.update()

    def reset_message():
        loading_text.value = "Select new image to convert"
        page.update()

    def loading_animation():
        dots = 1
        while "Processing image, please wait" in loading_text.value:
            try:
                loading_text.value = "Processing image, please wait" + "." * dots
                page.update()
                dots = dots % 3 + 1
                time.sleep(0.5)  # Change dots every half second
            except RuntimeError:
                # Stop the loop if the event loop is closed
                break

    def log_error(exception):
        # Get the current time and format it
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Get the full error message
        error_message = "".join(traceback.format_exception(None, exception, exception.__traceback__))
        # Determine the output path for the error log
        error_log_path = os.path.join(os.path.dirname(image_path), "background_remover_errors_backlog.txt")
        # Write the error to the log file
        with open(error_log_path, "a") as error_log:
            error_log.write(f"{current_time}\n{error_message}\n\n")

    def on_window_close(e):
        # Ensure the app closes completely
        page.close()
        sys.exit(0)

    # Redirect standard output and error streams
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

    # Register the window close event
    page.on_close = on_window_close

    # Create UI elements
    prompt_text = ft.Text("Pick an image to convert to PNG without background:",
                          style=ft.TextStyle(font_family="Segoe UI", size=24))
    loading_text = ft.Text("", style=ft.TextStyle(font_family="Segoe UI", size=18))
    button = ft.ElevatedButton(text="Select Image", on_click=select_image, width=250, height=60)

    invalid_dialog = ft.AlertDialog(
        content=ft.Text("Invalid image file. Please select a valid image.", style=ft.TextStyle(font_family="Segoe UI")),
        actions=[ft.TextButton("OK", on_click=hide_invalid_prompt)],
        visible=False
    )

    file_picker = ft.FilePicker(on_result=file_picker_result)

    # Add file pickers to page overlay
    page.overlay.append(file_picker)

    # Center the elements on the page and ensure the column elements are centered
    page.add(
        ft.Row(
            [ft.Column([prompt_text, button, loading_text], alignment="center", horizontal_alignment="center")],
            alignment="center"
        )
    )

    # Add invalid dialog
    page.overlay.append(invalid_dialog)


# Initialize and run the app
if __name__ == '__main__':
    ft.app(target=main)
