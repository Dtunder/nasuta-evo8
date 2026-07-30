## 2024-05-19 - Pygame SysFont IO Bottleneck
**Learning:** Initializing `pygame.font.SysFont` is incredibly expensive (takes over 1ms per call) because it requires hitting the file system to scan for system fonts every single time. Doing this inside render loops (like `draw_text` or `Diagram.draw` which run every frame) causes massive UI lag and CPU burn.
**Action:** Always memoize `pygame.font.SysFont(name, size)` calls using a global dictionary cache based on the font name and size tuple. Never instantiate Pygame fonts directly inside an update or draw loop.
