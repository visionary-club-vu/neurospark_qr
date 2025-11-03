import pandas as pd
import qrcode
import os

# --- Configuration ---
# Make sure your registration file is named 'registrations.csv'
CSV_FILE = 'registrations_final.csv'
# The folder where the new, correctly named QR codes will be saved
OUTPUT_FOLDER = 'qr_codes'

# --- Script ---

# Create the output folder if it doesn't exist
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)
    print(f"Created output folder: '{OUTPUT_FOLDER}'")

try:
    # --- THE FIX IS HERE ---
    # We explicitly tell pandas to read the 'SRN' column as a string (str).
    # This prevents it from being interpreted as a number and adding '.0'
    df = pd.read_csv(CSV_FILE, dtype={'SRN': str})

    # Check if 'SRN' column exists
    if 'SRN' not in df.columns:
        print(f"Error: The file '{CSV_FILE}' does not have an 'SRN' column. Please check the file.")
    else:
        print(f"Reading data from '{CSV_FILE}'...")
        print(f"Generating {len(df)} QR codes with correct filenames...")

        # Generate a QR code for each student
        for index, row in df.iterrows():
            # Get the SRN as a clean string
            srn = row['SRN']

            # Define the output filename (e.g., '31240349.png')
            filename = os.path.join(OUTPUT_FOLDER, f"{srn}.png")

            # Create QR code object and save the image file
            qr_img = qrcode.make(srn)
            qr_img.save(filename)

        print("\n✅ Success! All QR codes have been generated correctly.")
        print(f"You can find them in the '{OUTPUT_FOLDER}' folder.")

except FileNotFoundError:
    print(f"Error: The file '{CSV_FILE}' was not found.")
    print("Please make sure the script is in the same directory as your registration file.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
