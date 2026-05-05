# Camera Movement

Instead of instantly changing camera position, smooth movement improves the user experience.

## Smooth Follow

```python
    camera.x += (player.x - camera.x) * 0.1
    camera.y += (player.y - camera.y) * 0.1
```

This creates a smooth follow effect.

Useful for:

- platformers
- action games
- top-down games