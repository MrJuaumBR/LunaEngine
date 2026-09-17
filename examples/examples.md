# LunaEngine - Examples

## UI
| Name             | Description                          | File                                                        |
| ---------------- | ------------------------------------ | ----------------------------------------------------------- |
| Ui comprehensive |                                      | [ui_comprehensive_demo.py](./ui/ui_comprehensive_demo.py)   |
| New Frame        |                                      | [new_frame.py](./ui/new_frame.py)                           |
| Convert Themes   | Convert theme data to JSON          | [convert_themes.py](./ui/convert_themes.py)                 |
| External Theme   | Load a theme JSON from any path     | [external_theme_demo.py](./ui/external_theme_demo.py)       |
| Window Events    |                                      | [windows_events_demo.py](./ui/windows_events_demo.py)       |

## Audio
| Name             | Description                          | File                                                        |
| ---------------- | ------------------------------------ | ----------------------------------------------------------- |
| Audio            | Channels, groups, curves, pan, EFX  | [audio_demo.py](./audio/audio_demo.py)                      |

## Storage
| Name             | Description                          | File                                                        |
| ---------------- | ------------------------------------ | ----------------------------------------------------------- |
| Atlas            |                                      | [atlas_demo.py](./storage/atlas_demo.py)                    |
| Storage          |                                      | [storage_demo.py](./storage/storage_demo.py)                |

## Graphics
| Name             | Description                          | File                                                        |
| ---------------- | ------------------------------------ | ----------------------------------------------------------- |
| Filters          |                                      | [filters_demo.py](./graphics/filters_demo.py)               |
| Parallax         |                                      | [parallax_demo.py](./graphics/parallax_demo.py)             |
| Particle         |                                      | [particle_demo.py](./graphics/particle_demo.py)             |
| Shadow           |                                      | [shadow_demo.py](./graphics/shadow_demo.py)                 |
| Shapes Styling   |                                      | [shapes_styling_demo.py](./graphics/shapes_styling_demo.py) |
| Spritesheets     | SpriteSheet, Animation, and Image   | [spritesheets.py](./graphics/spritesheets.py)               |
| Paperdoll        |                                      | [paperdoll_demo.py](./graphics/paperdoll_demo.py)           |

## Scenes
| Name             | Description                          | File                                                        |
| ---------------- | ------------------------------------ | ----------------------------------------------------------- |
| Scene Transitions| Fade, slide, zoom, and other effects | [scenes_transitions_demo.py](./scenes_transitions_demo.py)  |

All examples target LunaEngine **0.2.6.2**. Run them from the repository root so
relative assets resolve correctly, for example:

```bash
python examples/graphics/spritesheets.py
python examples/audio/audio_demo.py
python examples/ui/external_theme_demo.py examples/ui/external_theme.json
```
