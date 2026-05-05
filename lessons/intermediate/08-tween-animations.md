# Tween Animations

Tweening allows smooth animation of UI elements and objects.

## Example

```python
    from lunaengine.ui.tween import Tween

    Tween(
        target=button,
        property="x",
        start=100,
        end=400,
        duration=1.0
    )
```

This smoothly moves the button from x=100 to x=400.

## Common Uses

- moving menus
- fading elements
- smooth UI transitions
- animated panels