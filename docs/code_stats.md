# code_stats

## Overview

*File: `lunaengine\tools\code_stats.py`*
*Lines: 253*

## Classes

### CodeStatistics

CodeStatistics Class
=====================

This class provides methods for analyzing the code statistics of a project. It can count the number of lines in a file, get all relevant files in the project, and analyze the entire project to provide statistics.

### Methods

* `count_lines_in_file(file_path: Path) -> Tuple[int, int, int]`: Count the number of lines in a given file, including code, comments, and blank lines.
* `get_all_files() -> List[Path]`: Get all relevant files in the project.
* `analyze_project() -> Dict`: Analyze the entire project and return statistics.
* `get_code_density(stats: Dict) -> float`: Calculate the code density of a given set of statistics.
* `print_statistics(stats: Dict) -> None`: Print formatted statistics to the console.

*Line: 12*

#### Methods

##### Method `count_lines_in_file`

Count lines in a file
Returns: (total_lines, code_lines, comment_lines, blank_lines)

*Line: 19*

##### Method `__init__`

Private method.

*Line: 13*

##### Method `analyze_project`

Analyze the entire project and return statistics

*Line: 84*

##### Method `get_all_files`

Get all relevant files in the project

*Line: 67*

##### Method `print_statistics`

Print formatted statistics

*Line: 135*

##### Method `get_code_density`

```
def get_code_density(self, stats):
    """
    Calculates the code density of a given set of statistics.

    Parameters:
        stats (dict): A dictionary containing various statistics about the code.

    Returns:
        float: The code density of the given set of statistics.
    """
```

*Line: 131*

---

## Functions

### Function `get_all_files`

Get all relevant files in the project

*Line: 67*

### Function `count_lines_in_file`

Count lines in a file
Returns: (total_lines, code_lines, comment_lines, blank_lines)

*Line: 19*

### Function `save_detailed_report`

Save a detailed markdown report

*Line: 212*

### Function `__init__`

Private method.

*Line: 13*

### Function `analyze_project`

Analyze the entire project and return statistics

*Line: 84*

### Function `print_statistics`

Print formatted statistics

*Line: 135*

### Function `main`

```
def main(project_root):
    """
    Checks if the project root directory exists.

    Parameters:
        project_root (str): The path to the project root directory.

    Returns:
        bool: True if the project root directory exists, False otherwise.
    """
```

*Line: 189*

### Function `get_code_density`

```
def get_code_density(stats):
    """
    Calculates the code density of a given set of statistics.
    
    Parameters:
        stats (dict): A dictionary containing various statistics about the code.
    
    Returns:
        float: The code density of the given set of statistics.
    """
```

*Line: 131*

