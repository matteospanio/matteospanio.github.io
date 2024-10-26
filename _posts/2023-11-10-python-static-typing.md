---
layout: post
title: "Python's Static Typing Safari: In Search of Code Clarity"
author: Matteo Spanio
categories: Python, Programming
tags: [python, programming, code]
giscus_comments: true
description: A brief introduction to Python's static typing and its benefits.
date: 2023-11-10

toc:
  - name: Introduction
  - name: Bug alert!
  - name: Type annotations
  - name: Generics
  - name: Sum up
---

## Introduction

In the vast landscape of programming languages, Python stands out as a dynamically typed language, celebrated for its readability and simplicity. Its syntax, clear and concise, makes it an ideal choice for scripting and automating processes with just a few lines of code. However, as projects grow in complexity and involve multiple contributors, the need for a more robust syntax becomes evident.

In this exploration, we dive into the realm of Python's static typing, unraveling its nuances and unveiling the tools at our disposal. Beyond the simplicity of dynamically typed languages, Python provides features like type annotations, function overloading, and generics, offering developers a sophisticated toolkit for crafting elegant and maintainable code.

Let's embark on a journey through the evolution of a simple addition function, uncovering the power of type annotations, the resurgence of overloading, and the elegance introduced by generics in Python. Join us as we navigate the intricacies of Python's static typing, discovering how it transforms code clarity and enhances the development experience.

## Bug alert!

Consider the following lines of code:

{% highlight python %}
def mysum(a, b):
return a + b
{% endhighlight %}

This function sums two elements. In this case, it might seem reasonable to leave it as it is, as you get function overloading for free on types:

{% highlight python %}
mysum(1, 2) # a: int, b: int -> int
mysum(0.5, 1.2) # a: float, b: float -> float
mysum(1, 0.6) # a: int, b: float -> float
mysum(7, 4+2.3j) # a: int, b: complex -> complex
{% endhighlight %}

All the calls to the `mysum` function are correct, and each time Python is able to infer the correct return type. Similarly, these function calls are valid and correct:

{% highlight python %}
mysum([1, 2, 3], [4, 5, 6])
mysum("foo", "bar")
{% endhighlight %}

However, what happens when you start calling the function with mixed arguments?

{% highlight python %}
mysum(1, "foo")
mysum({"a": 2}, [1, 4, 7])
mysum(5, None)
{% endhighlight %}

These lines are legitimate Python, yet most text editors won't complain. However, once the script executes, the Python interpreter crashes against these type mismatches:

```console
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "<stdin>", line 2, in mysum
TypeError: unsupported operand type(s) for +: 'int' and 'NoneType'
```

## Type annotations

`TypeError`! How is this possible?! Who dared to tell the interpreter to check types? Even though the use of types in Python is mostly transparent, it doesn't mean they don't exist. Therefore, annotating types in Python can be a good idea to save hours of debugging. Consider the following:

```python
def mysum_number(
    a: int | float | complex,
    b: int | float | complex,
) -> int | float | complex:
    return a + b

def mysum_list(a: list, b: list) -> list:
    return a + b

def mysum_str(a: str, b: str) -> str:
    return a + b
```

Let's break down the code above. The first function, `mysum_number`, accepts two arguments of type `int`, `float`, or `complex` and returns a value of the same type. The second function, `mysum_list`, accepts two arguments of type `list` and returns a value of the same type. The third function, `mysum_str`, accepts two arguments of type `str` and returns a value of the same type.

Now, every time you want to add two elements, knowing their type is enough to decide which function to call. However, this precision sacrifices overloading. To call all functions in the same way, indicating the desire for an overload, the standard library `typing` contains the `overload` decorator. The refactored code looks like this:

```python
from typing import overload

@overload
def mysum(
    a: int | float | complex,
    b: int | float | complex
) -> int | float | complex:
    ...

@overload
def mysum(a: list, b: list) -> list:
    ...

@overload
def mysum(a: str, b: str) -> str:
    ...

def mysum(a, b):
    return a + b
```

Overloading is back. Now, the function calls seen earlier all work, and those that used to generate a `TypeError` at runtime are now highlighted in red by our IDE.

> #### Note
>
> The three dots `...` have a special meaning in Python; it is the symbol known as an _ellipsis_. This symbol is usually used as a placeholder, but its meaning can vary slightly depending on the context. I recommend checking the documentation if you are curious and want to understand more about it.

## Generics

We could consider ourselves satisfied like this, but the `typing` module offers many other features. Among these, the use of Generics stands out, which in this case can be exploited to create a more elegant solution:

```python
from typing import TypeVar

T = TypeVar("T", int, float, complex, str, list)

def mysum(a: T, b: T) -> T:
    return a + b
```

`TypeVar` allows you to define a type that varies depending on the context, but once it is determined, it cannot change:

```python
mysum(1, 2)     # T = int
mysum(5, 0.7)   # T = float
mysum("a", "b") # T = str
```

Since Python 3.12 the `T` typevar declaration can be omitted[^1], and the type can be directly specified in the function definition:

```python
def mysum[T: (int, float, complex, str, list)](a: T, b: T) -> T:
    return a + b
```

> #### Note
>
> Along with `T` some constraints have been added, which are the types that `T` can assume. In this case, `T` can be `int`, `float`, `complex`, `str`, or `list`. That's because the `+` operator is defined for these types and not for others.

## Sum up

In this exploration of Python's static typing, we delved into crucial concepts that enhance code clarity and maintainability. Let's recap the key takeaways:

1. **Clear Syntax for All Sizes:** Python's dynamic typing shines in small scripts, offering a clear and concise syntax. However, as projects grow, the need for a more expressive syntax becomes apparent.

2. **Navigating Overloading:** The journey from a dynamically typed function to an overloaded one, thanks to the `typing` module's `overload` decorator, showcases Python's adaptability to diverse project requirements.

3. **Type Annotations as Guides:** Embracing type annotations is akin to providing a map for your code. Explicitly specifying types not only aids in debugging but also serves as documentation, making your code more understandable and maintainable.

4. **Generics: The Elegance Factor:** The introduction of generics via `TypeVar` elevates Python's static typing to new heights. With constraints on acceptable types, developers can craft more elegant and type-safe solutions.

5. **Evolution of Python's Typing Tools:** From annotations to overloading and generics, Python's typing tools evolve to cater to various development scenarios, offering a versatile toolkit for developers.

As you navigate your coding endeavors, remember that Python's static typing is not about rigid constraints but about providing developers with powerful tools to enhance their code's expressiveness and robustness. Embrace these tools judiciously, and may your coding journey be both clear and elegant.

---

[^1]: [PEP 695 -- Type Parameter Syntax](https://www.python.org/dev/peps/pep-0695/)
