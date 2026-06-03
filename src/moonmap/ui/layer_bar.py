"""Row of layer tabs displayed above the keyboard widget.

- One tab per layer, labeled with layer name and index
- Active layer tab is highlighted
- Clicking a tab fires a manual_layer_override signal
- Manual override is cleared by the MainWindow on the next MO/TG event
"""

from __future__ import annotations

# TODO: implement in build phase
