# About LunaEngine ✨

Welcome, fellow adventurer! Ever wondered about the heart and soul behind LunaEngine? You've come to the right place. This isn't just a technical document; it's a peek behind the curtain, a story of passion, Python, and pixels. So, grab a coffee (or your beverage of choice), and let's chat.

## What is LunaEngine?

First things first: I call LunaEngine an "Engine," but let's be honest, it's more like a super-powered **framework**. Think of it as your trusty sidekick, expertly bridging the gap between the raw power of Pygame and the dazzling capabilities of OpenGL. My mission? To make your life as a 2D game developer ridiculously easier. Instead of wrestling with repetitive functions and low-level integrations, LunaEngine hands you a ready-to-use toolkit, letting you focus on the fun stuff: crafting incredible game experiences. It's 2D, it's Python, and it's built to make you smile.

## The Spark of Inspiration

Every great journey starts with a spark, and LunaEngine's was ignited by a deep dive into the world of game development. While building various systems, I meticulously explored other engines, noting down every brilliant idea and clever solution. Here's a shout-out to the inspirations that shaped LunaEngine:

| Engine/Platform | What I Learned & Loved |
| --- | --- |
| **Godot** | The way Godot organizes scenes? Pure genius! It taught me the immense value of separating game logic into distinct, manageable scenes, giving us unparalleled control over transitions, camera movements, and overall game flow. It's like having a perfectly organized workshop for your game. |
| **Roblox Studio** | My time in Roblox Studio was a wild ride of successes and… interesting experiments. It profoundly influenced LunaEngine's built-in functionalities. From the intuitive UI system to smooth Tween animations and essential utilities, you'll find echoes of that dynamic, user-friendly approach woven throughout LunaEngine. |
| **Pure Pygame** | There's an undeniable charm to pure Pygame, especially the elegance of Python itself. Its object-oriented nature makes coding feel intuitive and genuinely enjoyable. My goal was to marry this Pythonic beauty with OpenGL's raw performance, creating a framework that's both a joy to write for and a powerhouse to run. |
| **Web Development (HTML/CSS)** | The sheer freedom and flexibility of HTML and CSS/SCSS are mind-boggling. It's that feeling of |
| "if you can imagine it, you can build it." This philosophy of unbridled creation, where code becomes a canvas, heavily influenced the design of LunaEngine, especially its UI system. |  |

## The Name: LunaEngine

Ah, the age-old question: "Where did the name come from?" When this framework started taking shape, it needed a name – for the folder, the main class, everything! I already had a Discord bot named Luna, and a lightbulb went off. "Why not?" I thought. And just like that, **LunaEngine** was born. Simple, right? Sometimes the best names are the ones that just feel right.

## A Stroll Through History

Full disclosure: this isn't my first rodeo. I had another framework project once upon a time, but it, well, retired early. I wasn't exactly planning to dive into another one, especially not one that would mess with my head and then get tossed aside. But then I stumbled upon Cave Engine, and a thought sparked: "They made an engine that runs Python? Maybe I can do that too..." And here we are, against all odds!

Just to set expectations straight: LunaEngine is currently focused on **Windows** and **Linux**. While I appreciate the enthusiasm, there are no plans to conquer **macOS** or **Google** devices. And 3D? Nope. My vision for Luna is a lean, mean, 2D machine – keeping it simple, focused, and incredibly effective.

## The Organized Chaos: LunaEngine's Structure

> "When developing big projects, you end up with big, messy code." — Someone, Some Year (probably me, after a long night of coding)

Yeah, I get it. LunaEngine, like any growing project, has had its share oforganizational growing pains. In the early days (think Luna `0.0` or `0.0.1`), it was a beautiful mess – files scattered like confetti after a party. Then, one fateful day, a tiny, exasperated fairy (or maybe it was just my inner voice) whispered, "Fix this mess, or you’ll be lost in your own code, dumbass." So, I did. I organized the files. The code, well, that was a work in progress.

But through some coding magic (and a lot of coffee), I’ve managed to inject more docstrings into this project than I have in my entire Python-coding life. Seriously, it’s a personal best!

So, what’s the deal with Luna’s structure? We operate on six main pillars, neatly tucked away in their own folders: `backend`, `core`, `graphics`, `tools`, `ui`, `misc`, and `utils`. Each one is a specialist, handling its own domain. Don’t fret too much about `tools` – that’s mostly my personal playground for developing Luna itself. You probably won’t need to venture in there, unless you’re feeling particularly adventurous.

## Engine Structure: A Deeper Dive

LunaEngine prides itself on a modular architecture, designed for clarity, maintainability, and sanity. Here’s a breakdown of what each core folder brings to the party:

| Directory | Role & Responsibilities |
| --- | --- |
| **`backend/`** | This is where the engine gets down to the nitty-gritty, handling low-level bindings and direct hardware communication. Think OpenGL, OpenAL, networking protocols, and getting cozy with your controller inputs. It’s the unsung hero making everything tick. |
| **`core/`** | The very heart of LunaEngine. This is where the main loop beats, windows are managed, scenes gracefully transition, and the rendering pipeline orchestrates the visual symphony. It’s the conductor of our digital orchestra. |
| **`graphics/`** | All things visual live here. From managing your camera’s perspective to conjuring dazzling particle effects, dynamic lights, and shadowy mysteries. This folder also houses sprite sheets and all the GLSL shaders that make your game look stunning. |
| **`ui/`** | The complete user interface system, a true gem of LunaEngine. It’s packed with elements like buttons, text boxes, dropdowns, and scrolling frames. Plus, it handles theming, animations (hello, tweening!), notifications, tooltips, and ensures everything looks perfectly laid out. |
| **`utils/`** | Your go-to for general utility functions. Need some math helpers? Threading magic? Performance monitoring? Timers? Or perhaps some image conversion? This folder has your back, providing all those handy tools that make development smoother. |
| **`misc/`** | A collection of miscellaneous tools and assets. This includes debugging utilities and a charming set of built-in icons. It’s the junk drawer you actually want to rummage through. |
| **`tools/`** | Primarily for internal development scripts, such as code statistics and asset helpers. While fascinating, it’s generally not intended for end-users. Consider it the engine’s secret workshop. |

And for those who love numbers, here’s a quick snapshot:

- **Total codebase**: Roughly 149 files, spanning over 16,000 lines of Python code.

- **Themes**: A delightful collection of 58+ pre-built themes, ready to give your UI a fresh look.

- **UI Elements**: 27 distinct UI elements, from humble buttons to complex widgets, all ready for your creative touch.

## Documentation: Your Guide to the Luna-verse

I’m a firm believer that good documentation is like a warm hug for developers. While I’ve poured a lot into making LunaEngine intuitive, sometimes you need a map. I’ve even whipped up a script that auto-generates documentation, proudly hosted on GitHub. You can dive into it right here: [LunaEngine Docs](https://mrjuaumbr.github.io/LunaEngine/).

Now, I’ll be honest, sometimes the auto-generated docs might have a few gaps. If you ever find yourself scratching your head, don’t suffer in silence! Hop onto our [Discord server](https://discord.com/invite/fb84sHDX7R). I’m usually lurking around, happy to help untangle any knots and chat about all things Luna.

## Getting Started: Your First Steps

I’d absolutely love to create a full YouTube video series on how to wield LunaEngine’s power. But, between you and me, my English pronunciation isn’t exactly Oscar-worthy (Portuguese is my jam!). So, for now, I’ll stick to what I do best: code examples!

You can find a treasure trove of examples in the `examples/` folder on the engine’s GitHub: [LunaEngine examples](https://github.com/MrJuaumBR/LunaEngine/tree/main/examples). For those craving something a bit more substantial, check out the [LunaEngine-Games repository](https://github.com/MrJuaumBR/LunaEngine-Games), where I’ve got some more "complex" projects that showcase LunaEngine in action. Dive in, tinker around, and let your creativity run wild!

## AI: Your Smart Co-Pilot

In this brave new world, AI can be an incredible asset, even for game development with LunaEngine. The trick? Giving it the right tools. Most AI models have a knowledge cutoff (meaning they don’t know about projects born after a certain date), so they won’t magically know about LunaEngine.

But fear not! You can turn your AI into a super-smart co-pilot by following these simple steps:

1. **Use an AI with web search/browsing capabilities**: Think models like DeepSeek or Grok (in its expert mode). These can actually browse the internet and learn about LunaEngine in real-time.

1. **Feed it the good stuff**: Explicitly provide these two links to your AI:
  - The official [LunaEngine GitHub repository](https://github.com/MrJuaumBR/LunaEngine)
  - The [LunaEngine official documentation](https://mrjuaumbr.github.io/LunaEngine/)

I’ve personally put this to the test with DeepSeek and Grok, and they’ve been surprisingly good! They can grasp the engine’s code structure, explain its features, and even help you whip up small code examples. So, yes, AI can absolutely lend a hand – just make sure it’s well-informed!

## Production: Go Forth and Create!

Dreaming of making your own game with LunaEngine and maybe even earning a few bucks? Go for it! I’m not here to stop you. In fact, I encourage it! Whether LunaEngine is the *best* choice for your magnum opus? Honestly, I’m not sure, and I don’t really care enough to find out. What I *do* care about is you creating something awesome. So, if LunaEngine helps you do that, then it’s the best choice for you. Period.

## LunaEngine Utilities: The Little Things That Matter

While LunaEngine might not be everyone’s cup of tea, I truly believe it offers some incredibly useful features that make Python game development a joy. Here are a few highlights:

- **Themes Galore**: With over **58+** pre-made themes, you can effortlessly style your game’s UI to match any aesthetic. It’s like having a wardrobe full of outfits for your game!

- **UI Elements**: Our UI system is one of LunaEngine’s crown jewels, heavily inspired by the intuitive design of HTML inputs and the robust component system of Roblox Studio. Building interfaces has never been this enjoyable.

- **Godot-Inspired Scenes**: The scene control in LunaEngine takes a page from Godot’s excellent scene management. This means organizing your game logic and transitions is incredibly intuitive and powerful, likely hitting the sweet spot for about 80% of users.

- **Optimized Particles**: I’m incredibly proud of our particle system. I’d even go so far as to say it’s one of the most optimized particle systems you’ll find in a Pygame-based framework (maybe!). Get ready for stunning visual effects without the performance hit.

- **Simplified Cameras**: Cameras can be a real headache in game development, especially when you’re just trying to make a quick demo. I’ve worked hard to simplify camera controls in LunaEngine, so you can focus on what’s important: your game, not wrestling with viewpoints.

## FAQs: The Questions You (Might) Have

Alright, let’s be real. Since LunaEngine is still a burgeoning project, we don’t have a massive backlog of frequently asked questions. But I can anticipate a few, so let’s tackle them head-on:

**Q: Why only OpenGL? Why not Pygame’s default renderer?**

A: Good question! The decision to focus solely on OpenGL was a deliberate one, driven by a desire for performance and advanced graphical capabilities. OpenGL allows LunaEngine to tap into hardware acceleration, delivering smoother animations, more complex visual effects, and dynamic lighting that would be challenging, if not impossible, with Pygame’s software renderer. It’s about pushing the visual boundaries of 2D Python games.

**Q: Will LunaEngine ever support 3D?**

A: As much as I love a good 3D adventure, LunaEngine is firmly rooted in the 2D realm. My vision is to create the best possible 2D game framework in Python, and introducing 3D would drastically alter its scope and complexity. So, for now, let’s enjoy the beauty of two dimensions!

**Q: Why isn’t macOS officially supported?**

A: Developing for multiple platforms is a significant undertaking. To ensure a stable and optimized experience, I’ve chosen to focus LunaEngine’s official support on Windows and Linux. While it might be possible to get it running on macOS, it’s not actively tested or maintained for that platform. My apologies to the Apple crowd!

**Q: Can I make commercial games with LunaEngine?**

A: Absolutely, go for it! LunaEngine is released under a permissive license, meaning you’re free to use it for personal projects, commercial ventures, or anything in between. Build your dream game, sell it, and make a fortune – just remember who helped you get there! 😉

**Q: How can I contribute to the LunaEngine project?**

A: Your contributions are incredibly welcome! Whether you’re a seasoned developer or just starting out, there are many ways to help. You can report bugs, suggest new features, improve the documentation (yes, even this `about.md`!), or contribute code. Check out the `CONTRIBUTING.md` file (if it exists) in the main repository for detailed guidelines. Every little bit helps make LunaEngine better for everyone!

## Final Message: From My Heart to Yours

And so, we reach the end of our little chat. Building LunaEngine has been an absolute labor of love, a journey filled with late nights, countless lines of code, and an unwavering belief in the magic of game development. This isn’t just a framework; it’s a piece of my passion, designed to empower you to bring your wildest 2D game ideas to life. I hope you feel the enthusiasm, the honesty, and maybe even a little bit of the humor that went into creating it. Go forth, create, innovate, and most importantly, have an absolute blast making games. The world is waiting for your next masterpiece! ✨

---

*P.S. If you’ve read this far, you’re officially awesome. Now go make something cool!*