from setuptools import setup, find_packages

setup(
    name="lunaengine",
    version="0.2.6.2",
    description="A modern 2D game framework with advanced UI and graphics",
    author="MrJuaumBR",
    url="https://github.com/MrJuaumBR/LunaEngine",
    packages=find_packages(),
    install_requires=[
        "pygame>=2.6.1",
        "numpy>=2.4.6",
        "PyOpenGL>=3.1.10",
        "PyOpenGL-accelerate>=3.1.10",
        "PyOpenAL",
        "psutil"
    ],
    python_requires=">=3.11",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9", # Linux Mint
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    package_data={
        'lunaengine': ['assets/*', '*.json', '*.txt', '*.md']
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            
        ],
    },
)