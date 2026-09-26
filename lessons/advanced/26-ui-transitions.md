# UI Transitions

Transitions improve how interfaces appear and disappear.

Use Tween to animate:

- position
- opacity
- size

## Example

```py
    Tween(
        target=menu,
        property="opacity",
        start=0,
        end=1,
        duration=0.5
    )
```

This creates a fade-in effect.