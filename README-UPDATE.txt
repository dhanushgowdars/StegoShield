StegoShield simple presentation UI update

Replaces only app.py. Keep all existing stegoshield/ modules, requirements, sample files, and saved history.

1. Stop Streamlit (Ctrl+C)
2. Back up your existing app.py.
3. Copy the app.py in this update into the StegoShield project folder (overwrite only app.py).
4. Run python -m streamlit run app.py

Changes: Removed technical file size/CRC32/encryption copy from normal result screens, shortened messages and tips, retained four core algorithms and the local file vault. Checksums still run internally.
