# UI Elements Basics

LunaEngine includes a built-in UI system with reusable components such as buttons, labels, and containers.

## Creating a Button

```python
    from lunaengine.ui.elements import Button

    button = Button(
        x=100,
        y=100,
        width=200,
        height=50,
        text="Click Me"
    )
```
## Adding Events

```python
    button.on_click = lambda: print("Button clicked!")
```
## Adding to Scene

```python
    self.add_ui_element(button)
```
## Common UI Elements

- Button
- TextLabel
- TextBox
- ImageLabel
- Dropdown

These elements help create menus, HUDs, and interfaces without manually handling rendering.