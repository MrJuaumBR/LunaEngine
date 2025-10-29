# threading

## Overview

*File: `lunaengine\utils\threading.py`*
*Lines: 57*

## Classes

### Task

```
class Task:
    """Represents a task that can be executed."""

    def __init__(self, func: Callable):
        """Initialize the task with a function to execute.

        Args:
            func (Callable): The function to execute.
        """

    def execute(self):
        """Execute the task.

        Returns:
            Any: The result of executing the task.
        """
```

*Line: 5*

#### Methods

##### Method `__init__`

Private method.

*Line: 6*

##### Method `execute`

Execute the task

*Line: 13*

---

### ThreadPool

ThreadPool
=========

A class for managing a pool of worker threads.

### Initialization

__init__(self, num_threads: int)
-------------------------------

Initialize the thread pool with the specified number of worker threads.

Parameters:

* `num_threads`: The number of worker threads to create in the pool.

### Methods

start(self)
---------

Start the thread pool.

stop(self)
-------

Stop the thread pool.

submit(self, task: Task)
-------------------

Submit a task to the thread pool.

Parameters:

* `task`: The task to submit to the pool.

_worker(self)
-------------

Worker thread function. This method is called by each worker thread in the pool.

### Description

The ThreadPool class provides a simple way to manage a pool of worker threads. It allows you to start, stop, and submit tasks to the pool. Each task is executed by a separate worker thread in the pool. The ThreadPool class also provides a _worker method that can be used to define the behavior of each worker thread.

*Line: 20*

#### Methods

##### Method `__init__`

Private method.

*Line: 21*

##### Method `stop`

Stop the thread pool

*Line: 36*

##### Method `start`

Start the thread pool

*Line: 27*

##### Method `_worker`

Worker thread function

*Line: 49*

##### Method `submit`

Submit a task to the thread pool

*Line: 45*

---

## Functions

### Function `__init__`

Private method.

*Line: 6*

### Function `stop`

Stop the thread pool

*Line: 36*

### Function `start`

Start the thread pool

*Line: 27*

### Function `__init__`

Private method.

*Line: 21*

### Function `submit`

Submit a task to the thread pool

*Line: 45*

### Function `execute`

Execute the task

*Line: 13*

### Function `_worker`

Worker thread function

*Line: 49*

