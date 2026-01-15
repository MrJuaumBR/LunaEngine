# LunaEngine

## What is LunaEngine?

First of all, I call LunaEngine an "Engine," but in reality, it is a framework that facilitates communication between Pygame and OpenGL for the user.

It is a 2D engine developed entirely in Python using PyGame and OpenGL. This engine aims to make every user's life easier by providing many repetitive functions that you would otherwise need to implement yourself.

## Inspiration

While developing the systems, I tested several other engines and noted what I liked about each one.

| Engine Name      | Features |
|------------------|----------|
| Godot            | What I liked most about Godot was how scenes are organized. This approach allows us to separate them and have much greater control over entering, exiting, moving the camera, etc. |
| Roblox Studio    | My experience with Roblox Studio was more extensive; I developed several games—some were successful, others were more like experiments. It’s fair to say that most of its built-in functions—like the UI system, Tween animations, and basic utilities—are integrated here. |
| Pure Pygame      | In pure Pygame, I really appreciate the Python language. Object-oriented programming is intuitive and fun to work with, so I wanted to combine it with OpenGL for better performance. |
| Web Development  | The freedom that HTML and CSS/SCSS offer is incredible. It feels like if you can write code, you can build anything—just go for it. |

## Where did this name come from?

When I started creating this **framework**, I needed a name—for the folder, the main class, and so on.  
I already have a Discord bot named Luna, so I thought: "Why not?"  
And that’s how the name **LunaEngine** was born!

## History

First, I should mention that this isn’t the first **framework** I’ve worked on. Honestly, I already had another one that I discontinued.

I wasn’t planning to create another one just to mess with my head and then throw it away, but when I saw Cave Engine, I thought: "So they made an engine that runs Python? Maybe I can do that too..." And here we are.

Just to be clear, I have no plans to make this run on **macOS** or **Google** devices—only **Linux** and **Windows**. Also, I don’t intend to add 3D support; it doesn’t fit with the idea of a simple **framework** that I have for Luna.

## Organization

"When developing big projects, you end up with big, messy code." — Someone, Some Year

Yeah, the engine has hundreds of problems that i try to fix with every update—emphasis on *try* . In the early versions of Luna (__0.0/0.0.1__), we didn’t have good organization—just files thrown around chaotically. Then one day, a tiny fairy came into my room and said, "Fix this mess, or you’ll be lost in your own code, dumbass." So the next day, I organized everything… but only the files. The code was still a mess.

But through some magic, I’ve added more docstrings to this project than in my entire life using Python. Seriously.

So, what do you need to know? In Luna, we have six main pillars—the folders: *backend* , *core* , *graphics* , *tools* , *ui* , and *utils* . Each one basically handles its own functions. Don’t worry about *tools* —it’s mostly for my daily development of Luna. I don’t think you’ll need it.

## Documentation

I developed a script that automatically generates documentation, which is hosted on GitHub. You can access it here:  
[LunaEngine Docs](https://mrjuaumbr.github.io/LunaEngine/)

However, sometimes the documentation might be incomplete. If you have questions, please join the [Discord](https://discord.gg/fb84sHDX7R) server—I’ll be happy to help.

## Getting Started

I’d love to create a full YouTube video series teaching how to use Luna, but I don’t feel confident doing it in English—I speak Portuguese, and my English pronunciation is pretty bad.

But… I do have code examples! You can check them out in the *[examples/](https://github.com/MrJuaumBR/LunaEngine/tree/main/examples)* folder on the engine’s GitHub, or visit the *[LunaEngine-Games](https://github.com/MrJuaumBR/LunaEngine-Games)* repository, where I have some more "complex" projects for you to explore.

## AI

You can’t really use AI with Luna—and I don’t think it’s my fault. AIs usually have a knowledge cutoff (e.g., up to 2023), so when a new project comes out, it takes time for them to learn how it works. Plus, the project needs to be **popular**, which Luna isn’t… yet. >:(

## Production

Want to use Luna to make your own game and earn money from it? Go ahead—I don’t mind. But I’m not sure if it’s the best choice. Maybe it is—I honestly don’t care enough to find out.

## FAQs

Well, no one really uses this framework/engine yet, so we don’t have FAQs, alright?

**Cute message for you guys :)**

<div style="max-width: 800px; margin: 40px auto; padding: 0 20px;">
  <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 15px; margin-bottom: 30px;">    
    <div style="flex: 1; min-width: 150px; max-width: 180px;">
      <div style="background: #fff; border: 2px solid #3498db; border-radius: 10px; padding: 20px; text-align: center;">
        <div style="font-size: 36px; font-weight: 800; color: #3498db;">Ca</div>
        <div style="font-size: 18px; color: #2c3e50; margin: 10px 0;">20</div>
        <div style="font-size: 14px; color: #7f8c8d;">Cálcio</div>
      </div>
    </div>
    <div style="flex: 1; min-width: 150px; max-width: 180px;">
      <div style="background: #fff; border: 2px solid #e74c3c; border-radius: 10px; padding: 20px; text-align: center;">
        <div style="font-size: 36px; font-weight: 800; color: #e74c3c;">Ga</div>
        <div style="font-size: 18px; color: #2c3e50; margin: 10px 0;">31</div>
        <div style="font-size: 14px; color: #7f8c8d;">Gálio</div>
      </div>
    </div>
    <div style="flex: 1; min-width: 150px; max-width: 180px;">
      <div style="background: #fff; border: 2px solid #2ecc71; border-radius: 10px; padding: 20px; text-align: center;">
        <div style="font-size: 36px; font-weight: 800; color: #2ecc71;">N</div>
        <div style="font-size: 18px; color: #2c3e50; margin: 10px 0;">7</div>
        <div style="font-size: 14px; color: #7f8c8d;">Nitrogênio</div>
      </div>
    </div>
    <div style="flex: 1; min-width: 150px; max-width: 180px;">
      <div style="background: #fff; border: 2px solid #f39c12; border-radius: 10px; padding: 20px; text-align: center;">
        <div style="font-size: 36px; font-weight: 800; color: #f39c12;">O</div>
        <div style="font-size: 18px; color: #2c3e50; margin: 10px 0;">8</div>
        <div style="font-size: 14px; color: #7f8c8d;">Oxigênio</div>
      </div>
    </div>  
  </div>
</div>