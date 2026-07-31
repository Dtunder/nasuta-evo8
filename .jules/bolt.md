## 2024-05-18 - [Pygame SysFont Caching]
**Learning:** Pygame's `SysFont` is incredibly slow because it scans system font directories on every single invocation. Calling `pygame.font.SysFont` inside `draw` methods (e.g., `draw_text` or inside sprite loops like `Diagram.draw`) causes massive UI latency and is a specific performance anti-pattern in Pygame architectures.
**Action:** Always memoize `pygame.font.SysFont` calls using a global dictionary cache (e.g., `_FONT_CACHE[(name, size)]`) when fonts are needed on every frame.
