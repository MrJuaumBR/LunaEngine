from setuptools import setup, find_packages

setup(
    name="lunaengine",
    version="0.2.2",
    description="A modern 2D game engine with advanced UI and graphics",
    author="MrJuaum",
    url="https://github.com/MrJuaumBR/lunaengine",
    packages=find_packages(),
    install_requires=[
        "pygame>=2.5.0",
        "numpy>=1.21.0",
        "PyOpenGL>=3.1.0",
        "PyOpenGL-accelerate>=3.1.0",
        "PyOpenAL",
        "psutil",
    ],
    python_requires=">=3.9",
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
    package_data={
        'lunaengine': ['themes.json', '*.json', '*.txt', '*.md']
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            
        ],
    },
)