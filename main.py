import tkinter as tk
from tkinter import messagebox, font
import cv2
from pyzbar import pyzbar
import pandas as pd
from PIL import Image, ImageTk
import threading
import os
import time

# --- CONFIGURATION ---
# IMPORTANT: Change this value each day of the event!
# For Oct 13th, set to 1. For Oct 14th, set to 2, and so on.
CURRENT_EVENT_DAY = 4

# --- FILE PATHS ---
REGISTRATIONS_FILE = 'registrations_final.csv'
ATTENDANCE_FILE = 'attendance_final.csv'


class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"NeuroSpark Attendance Tracker - DAY {CURRENT_EVENT_DAY}")

        self.root.configure(bg='#2c3e50')
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(family="Arial", size=12)

        self.info_font = ("Arial", 16, "bold")
        self.status_font = ("Arial", 14)

        self.vid = cv2.VideoCapture(0)

        main_frame = tk.Frame(root, bg='#2c3e50', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- WIDGETS ---
        self.day_label = tk.Label(main_frame, text=f"Tracking Attendance for: Day {CURRENT_EVENT_DAY}",
                                  font=self.info_font, bg='#34495e', fg='#ecf0f1', pady=10)
        self.day_label.pack(pady=(0, 20), fill=tk.X)

        self.canvas = tk.Canvas(main_frame, width=self.vid.get(cv2.CAP_PROP_FRAME_WIDTH),
                                height=self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT), bg='#34495e', highlightthickness=0)
        self.canvas.pack()

        self.status_label = tk.Label(main_frame, text="Please scan a QR code...", font=self.status_font, bg='#2c3e50',
                                     fg='white', height=2, wraplength=500)
        self.status_label.pack(pady=(20, 0), fill=tk.X)

        self.export_button = tk.Button(main_frame, text="Export Today's Attendance", command=self.export_attendance,
                                       font=("Arial", 12, "bold"), bg='#16a085', fg='white', relief=tk.FLAT, padx=10,
                                       pady=5, cursor="hand2")
        self.export_button.pack(pady=(10, 0), fill=tk.X)

        # --- DATA SETUP ---
        self.df = self.setup_database()

        self.last_scanned_srn = None
        self.scan_cooldown_time = 3

        # --- THREADING ---
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.video_loop)
        self.thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_database(self):

        if not os.path.exists(ATTENDANCE_FILE):
            try:
                reg_df = pd.read_csv(REGISTRATIONS_FILE)

                if 'SRN' not in reg_df.columns:
                    messagebox.showerror("Error",
                                         f"'SRN' column not found in {REGISTRATIONS_FILE}. Please ensure the unique identifier column is named 'SRN'.")
                    self.root.destroy()
                    return None

                for i in range(1, 6):
                    reg_df[f'Day{i}_Attendance'] = False

                reg_df.to_csv(ATTENDANCE_FILE, index=False)
                messagebox.showinfo("Setup Complete", f"'{ATTENDANCE_FILE}' has been created successfully.")

            except FileNotFoundError:
                messagebox.showerror("Error",
                                     f"The initial registration file '{REGISTRATIONS_FILE}' was not found. Please place it in the same directory.")
                self.root.destroy()
                return None
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred during setup: {e}")
                self.root.destroy()
                return None

        return pd.read_csv(ATTENDANCE_FILE)

    def video_loop(self):

        try:
            while not self.stop_event.is_set():
                ret, frame = self.vid.read()
                if ret:
                    barcodes = pyzbar.decode(frame)
                    for barcode in barcodes:
                        (x, y, w, h) = barcode.rect
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                        barcode_data = barcode.data.decode('utf-8')
                        self.process_qr_code(barcode_data)

                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    photo = ImageTk.PhotoImage(image=Image.fromarray(rgb_frame))

                    self.canvas.create_image(0, 0, image=photo, anchor=tk.NW)
                    self.canvas.image = photo  # Keep a reference to avoid garbage collection
        except Exception as e:
            print(f"Error in video loop: {e}")

    def process_qr_code(self, srn_data):

        if self.last_scanned_srn and self.last_scanned_srn['srn'] == srn_data and (
                time.time() - self.last_scanned_srn['time']) < self.scan_cooldown_time:
            return

        try:
            srn = int(srn_data)

            self.last_scanned_srn = {'srn': srn_data, 'time': time.time()}

            attendance_column = f'Day{CURRENT_EVENT_DAY}_Attendance'

            student_record = self.df[self.df['SRN'] == srn]

            if student_record.empty:
                self.update_status(f"SRN: {srn} NOT FOUND in database.", 'red')
                return

            student_index = student_record.index[0]
            student_name = student_record['Name'].values[0]

            if self.df.loc[student_index, attendance_column]:
                self.update_status(f"ALREADY PRESENT: {student_name} ({srn})", 'orange')
            else:

                self.df.loc[student_index, attendance_column] = True

                self.df.to_csv(ATTENDANCE_FILE, index=False)

                self.update_status(f"SUCCESS: {student_name} ({srn}) marked present for Day {CURRENT_EVENT_DAY}.",
                                   'lightgreen')
                self.root.bell()

        except ValueError:
            self.update_status(f"INVALID QR: Data '{srn_data}' is not a valid SRN.", 'red')
        except Exception as e:
            self.update_status(f"An error occurred: {e}", 'red')

    def update_status(self, message, color):
        self.status_label.config(text=message, fg=color)

    def export_attendance(self):

        if not messagebox.askyesno("Confirm Export",
                                   f"Do you want to export the attendance list for Day {CURRENT_EVENT_DAY}?"):
            return

        try:
            attendance_column = f'Day{CURRENT_EVENT_DAY}_Attendance'

            present_students_df = self.df[self.df[attendance_column] == True]

            if present_students_df.empty:
                messagebox.showinfo("Export Info",
                                    f"No students have been marked present for Day {CURRENT_EVENT_DAY} yet.")
                return

            desired_columns = ['Name', 'SRN', 'Department', 'Year', 'Division']

            columns_to_export = [col for col in desired_columns if col in present_students_df.columns]

            if not columns_to_export:
                messagebox.showerror("Export Error",
                                     "None of the specified columns (Name, SRN, Department, etc.) were found to export.")
                return

            export_df = present_students_df[columns_to_export]

            export_filename = f'Day{CURRENT_EVENT_DAY}_Attendance_Export_{time.strftime("%Y-%m-%d")}.csv'

            export_df.to_csv(export_filename, index=False)

            messagebox.showinfo("Export Successful",
                                f"Attendance for Day {CURRENT_EVENT_DAY} has been exported to:\n{export_filename}")

        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred while exporting the data: {e}")

    def on_closing(self):

        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            print("Closing application...")
            self.stop_event.set()
            if self.thread.is_alive():
                self.thread.join()
            self.vid.release()  
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceApp(root)
    root.mainloop()

