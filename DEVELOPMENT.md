# Development and packaging

Use Python 3.12 or newer. The two dependencies are used only for validation and packaging.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-test.txt
.venv\Scripts\python tools/check.py
```

The default check validates Lua syntax, mod metadata, versions, links, option definitions, images, and licenses. To run the native-method simulations, set `GAME_SOURCE` to your installed Relaunched ModTools source directory and run:

```powershell
$env:GAME_SOURCE = "<game directory>\ModTools\Src"
.venv\Scripts\python tools/check.py --game-source "$env:GAME_SOURCE"
```

The proprietary game source is read locally and is not copied into this repository. Simulations do not prove gameplay compatibility.

Build separate mod packages with their metadata versions:

```powershell
.venv\Scripts\python tools/package.py
```

Packages are written to `dist`. Each ZIP has one folder named after its mod ID. They are manual installation packages. The Mod Editor creates its own upload archive for Paradox Mods.

To update a version, edit `version_major`, `version_minor`, and `version` in that mod's `mod/metadata.lua`. Update the same version in the root README, the mod README, and `mod/Read me.txt`. Keep mod IDs, author, listing IDs, and publishing versions intact. Run the shared check before packaging.
