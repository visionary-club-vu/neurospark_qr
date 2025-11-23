import os
import pandas as pd
import urllib.parse

# --- CONFIGURATION ---
REPO_BASE_URL = "https://raw.githubusercontent.com/visionary-club-vu/neurospark_qr/main"
PARTICIPANT_FOLDER = "partcert"  # Folder name for participation certs
WINNER_FOLDER = "wincert"  # Folder name for winner certs
REGISTRATIONS_FILE = "registrations_final.csv"  # Updated to match your new file name
OUTPUT_FILE = "certificates_to_send.csv"


def get_certificates_from_folder(folder_name):
    """Scans a folder and returns a list of dictionaries with Name and URL."""
    certs = []

    if not os.path.exists(folder_name):
        print(f"⚠️ Warning: Folder '{folder_name}' not found. Skipping.")
        return certs

    print(f"Scanning '{folder_name}'...")
    files = os.listdir(folder_name)

    for filename in files:
        if filename.lower().endswith(".pdf"):
            # 1. Get the Name (Remove .pdf)
            name = os.path.splitext(filename)[0]

            # 2. Build the URL (Encode spaces to %20)
            safe_filename = urllib.parse.quote(filename)
            url = f"{REPO_BASE_URL}/{folder_name}/{safe_filename}"

            certs.append({"Name": name, "Certificate_URL": url})

    return certs


def main():
    # 1. Load Emails from Master List
    email_lookup = {}

    # Check if file exists
    if not os.path.exists(REGISTRATIONS_FILE):
        print(f"⚠️ Error: '{REGISTRATIONS_FILE}' not found.")
        print("   Please make sure your CSV file is in this folder and named correctly.")
        return

    print(f"Loading emails from {REGISTRATIONS_FILE}...")
    try:
        df_reg = pd.read_csv(REGISTRATIONS_FILE)

        # Clean column headers (remove spaces)
        df_reg.columns = df_reg.columns.str.strip()
        print(f"Columns found: {list(df_reg.columns)}")

        # --- SMART COLUMN DETECTION ---
        # Find the Name column
        name_col = None
        possible_names = ['Name', 'Full Name', 'Student Name', 'Participant Name']
        for col in possible_names:
            if col in df_reg.columns:
                name_col = col
                break

        # Find the Email column
        email_col = None
        possible_emails = ['Email', 'Email Address', 'EmailAddress', 'Email ID']
        for col in possible_emails:
            if col in df_reg.columns:
                email_col = col
                break

        if name_col and email_col:
            print(f"✅ Using '{name_col}' for Names and '{email_col}' for Emails.")
            # Create dictionary: Name -> Email
            email_lookup = pd.Series(df_reg[email_col].values, index=df_reg[name_col].astype(str).str.strip()).to_dict()
        else:
            print("⚠️ ERROR: Could not identify Name or Email columns.")
            print(f"   Looking for Name in: {possible_names}")
            print(f"   Looking for Email in: {possible_emails}")
            return

    except Exception as e:
        print(f"⚠️ Error reading CSV: {e}")
        return

    # 2. Scan Folders
    all_certs = []
    all_certs.extend(get_certificates_from_folder(PARTICIPANT_FOLDER))
    all_certs.extend(get_certificates_from_folder(WINNER_FOLDER))

    if not all_certs:
        print("❌ No certificates found. Check your folder names.")
        return

    # 3. Match Emails and Build Final List
    print(f"Processing {len(all_certs)} certificates...")
    final_data = []

    matched_count = 0
    for cert in all_certs:
        name = cert['Name']
        # Try to find email, leave empty if not found
        email = email_lookup.get(name.strip(), "")

        if email:
            matched_count += 1

        final_data.append({
            "Name": name,
            "Email": email,
            "Certificate_URL": cert['Certificate_URL']
        })

    # 4. Save to CSV
    df_final = pd.DataFrame(final_data)
    df_final.to_csv(OUTPUT_FILE, index=False)

    print(f"\n✅ Success! Generated '{OUTPUT_FILE}' with {len(df_final)} rows.")
    print(f"   Matched {matched_count} emails automatically.")

    missing_emails = len(df_final) - matched_count
    if missing_emails > 0:
        print(f"⚠️ Warning: Could not find emails for {missing_emails} people.")
        print("   This happens if the name in the PDF file doesn't match the CSV Name exactly.")


if __name__ == "__main__":
    main()