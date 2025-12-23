---
layout: post
title: "Making scientific python blazingly fast with PyTorch"
author: Matteo Spanio
categories: Python, Programming, Scientific Computing
tags: [python, programming, code, scientific-computing, gpu]
giscus_comments: false
description: A deep dive into using PyTorch for high-performance scientific computing
date: 2025-08-28
thumbnail: assets/img/thumbnail-fast.jpg

toc:
  - name: The slow python problem
  - name: Already used solutions (and their limitations)
  - name: PyTorch to the rescue
  - name: Conclusions
---

If you’ve ever written scientific code in Python, you know the pain: Python is elegant, easy to read, and full of libraries—but when it comes to performance, it often feels like you’re driving a Ferrari with the handbrake on. In my recent paper _TorchFX: A Modern Approach to Audio DSP with PyTorch and GPU Acceleration_ (DAFx25), we introduce a solution to this long-standing problem.

The idea is simple yet powerful: instead of relying on the traditional **NumPy + SciPy stack**, we can **swap them out for PyTorch**, instantly gaining GPU acceleration, an object-oriented API, and direct compatibility with AI workflows.

## The slow python problem

Python itself is notoriously slow for heavy computations. The interpreter adds overhead, and loops kill performance. That’s why scientific programming in Python always starts with NumPy and SciPy, which wrap C and Fortran under the hood. But even then, scaling to multi-channel or real-time contexts (like audio DSP) is a challenge.

![python slow meme](https://i.imgflip.com/416iip.jpg)

## Already used solutions (and their limitations)

Over the years, developers have tried different hacks to speed up Python:

- **Vectorization with NumPy** – great, but requires reshaping your code.
- **Cython** – lets you drop into C, but you need to rewrite parts of your program.
- **Numba** – JIT compilation is cool, but not everything is parallelizable, and libraries like SciPy aren’t fully supported.

All of these approaches share one problem: you must **refactor your code** in sometimes unnatural ways, and you’re still limited by CPU-based execution.

![numba meme](https://i.programmerhumor.io/2024/05/programmerhumor-io-python-memes-backend-memes-c74192bb729eec4.jpg)

## PyTorch to the rescue

This is where **PyTorch** comes in. Originally built for AI, PyTorch provides:

- **Tensors that work like NumPy arrays**, but with GPU acceleration.
- **An object-oriented API**, more structured than SciPy’s MATLAB-inspired procedural style.
- **Direct integration with AI models**—any DSP function you write can be dropped into a neural network.

In our paper, we introduce **TorchFX**, a new library built on top of PyTorch, designed specifically for audio DSP. With TorchFX, you can:

- Apply **FIR and IIR filters** using GPU acceleration.
- Work naturally with **multichannel audio**.
- Build filter chains with an intuitive **pipe operator (`|`)**, making code both clean and fast.

And the performance? In our benchmarks, TorchFX crushed SciPy when dealing with multi-channel or long-duration signals. While SciPy slows down linearly with more channels, TorchFX (especially on GPU) keeps execution times almost flat—even for huge datasets.

## Conclusions

Python’s slowness has always been the elephant in the room for scientific computing. While solutions like Numba and Cython help, they demand compromises. Our proposal is simple: **if you’re starting from NumPy and SciPy, switch to PyTorch.**

With TorchFX, we show how this shift can **revolutionize scientific Python for audio DSP**:

- Cleaner, object-oriented code
- Built-in AI compatibility
- GPU acceleration out of the box

The result? **Your code will run blazingly fast.**

👉 TorchFX is open-source and available here: [https://github.com/matteospanio/torchfx](https://github.com/matteospanio/torchfx)
