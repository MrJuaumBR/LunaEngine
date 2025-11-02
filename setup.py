from setuptools import setup, find_packages

setup(
    name="lunaengine",
    version="0.1.1",
    description="A modern 2D game engine with advanced UI and graphics",
    packages=find_packages(),
    install_requires=[
        "pygame>=2.5.0",
        "numpy>=1.21.0",
        "PyOpenGL>=3.1.0",
        "PyOpenGL-accelerate>=3.1.0",
    ],
    python_requires=">=3.8",
    author="MrJuaum",
    url="https://github.com/MrJuaumBR/lunaengine",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)