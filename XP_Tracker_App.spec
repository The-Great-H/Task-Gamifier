# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import get_hooks_dirs
import os
import sys

# Define the base Streamlit package path (this is the most important part)
# This path is usually found within your environment's site-packages.
# We will rely on PyInstaller finding this internally via hooks, but we add 
# hidden imports and manual data adds for safety.

# PyInstaller uses os.path.join internally, but we manually add the necessary 
# hidden imports and data collections often missed with complex apps.

# --- Aggressive Collection of Hidden Imports and Data ---
# These are the files and modules most often missed in complex bundles
# We explicitly call out all of our data files and key package dependencies.

# Determine if we are running the final PyInstaller execution (used to set the final file list)
if sys.platform.startswith('win'):
    # Windows specific fixes (like the pkg_resources issue)
    hidden_imports_list = [
        "pkg_resources.py2_warn",
        "plotly",
        "pandas",
        "streamlit.vendor",
        "streamlit.vendor.pymediacms",
        "streamlit.vendor.protobuf"
    ]
else:
    hidden_imports_list = [
        "pkg_resources.py2_warn",
        "plotly",
        "pandas",
        "streamlit.vendor",
        "streamlit.vendor.pymediacms",
        "streamlit.vendor.protobuf"
    ]

# PyInstaller's built-in Analysis section
a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 1. Your app data files
        ('tasks.json', '.'),
        ('rewards.json', '.'),
        ('xp_log.csv', '.'),

        # 2. Add Plotly/Pandas/Streamlit hidden assets
        # PyInstaller's hooks should handle the internal assets for the collected packages.
    ],
    hiddenimports=hidden_imports_list,
    hookspath=get_hooks_dirs(),
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=a.cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='XPTrackerApp',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True,  # Ensure console remains open to see errors
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='XPTrackerApp')
