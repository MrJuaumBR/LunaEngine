# Lesson 19 – Clipboard

Text controls use LunaEngine's clipboard helpers in `lunaengine.utils.clipboard`.

## Copy and paste
```python
from lunaengine.utils.clipboard import copy_text, paste_text

copy_text("Saved from LunaEngine")
value = paste_text()
print(value)
```

`copy_text(text)` returns `True` when the platform clipboard accepts the text and `False` when the backend is unavailable. `paste_text()` returns the current text, or an empty string when no clipboard is available.

`TextBox` and `TextArea` already integrate Ctrl+C, Ctrl+X, and Ctrl+V when they have focus. A button can use the helpers directly:
```python
from lunaengine.ui import Button
from lunaengine.utils.clipboard import copy_text

button = Button(20, 20, 160, 40, "Copy save code")
button.set_on_click(lambda: copy_text("player-export-001"))
```

For a simple export/import save flow:
```python
from lunaengine.utils.clipboard import copy_text, paste_text

# Export
copy_text(savedata.export_json())

# Import
raw = paste_text()
if raw:
    savedata.import_json(raw)
```

Clipboard support depends on the platform. Linux commonly needs an X11 clipboard service and a working `pygame.scrap` backend; Windows normally provides the system clipboard. Headless CI, remote sessions, and Wayland/container setups may return failure or an empty string. Treat those results as normal and provide a file-based fallback for important data.
