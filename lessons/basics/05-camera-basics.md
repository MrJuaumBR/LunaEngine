# Camera Basics

The Camera system controls what part of the world is visible on the screen.

## Creating a Camera

```python
    from lunaengine.graphics.camera import Camera

    camera = Camera()
```
## Moving the Camera

```python
    camera.x += 10
    camera.y += 5
```
## Following an Object

```python
    camera.x = player.x
    camera.y = player.y
```

This is useful for side-scrollers, RPGs, and large maps.