---
layout: distill
title: Principles of statistic
description: An introduction to statistic
banner:
  image: "/assets/images/banners/statistics.jpg"
categories: Statistic
tags: [statistic, math]
giscus_comments: true

authors:
  - name: Matteo Spanio
    affiliations:
      name: University of Padua

toc:
  - name: Introduction
  - name: Population samples, parameters and statistics
  - name: Sampling and non-sampling errors
  - name: Sample statistics
---

## Introduction

Statistic is that field of math which studies collections of empirical data. How are data distributed? Can we infer something from our data?

With statistic we can answer to these and other questions.

In this article we will discuss about the fundamentals that we need to know before starting an analysis of the data.

---

## Population samples, parameters and statistics

Data collection is a crucial fact in Statistics. The _samples_ collected and analyzed are used to make scale assertions about the _population_.

It is therefore necessary to divide the types of data we are dealing with in different ways: if a _parameter_ (which is usually a number) concerns a fact of the entire object that is taken into consideration (e.g. the number of women living on earth at a given moment), this is a number that observes the reality of the facts and does not change depending on the observation, it is usually the parameter sought through the statistics, as it is often very difficult or impossible to know these numbers. Statistic takes into account smaller samples of the problem by sampling a part of the population, the quantities are studied on this smaller scale and then they are brought back to a larger scale.

Let's define a glossary with the multiple terms used in statistics that help us to define whether they are absolute numbers related to a certain situation or whether they are related to a studied sample.

### Glossary

- **Population**: the reality of the facts of which we usually want to know some aspects, if we talk about population we mean to refer to all the units that are part of a certain group;

- **Parameter $$\theta$$**: a characteristic that describes the population (for example the actual mean or median);

- **Census**: observation of **all** population units to quantify a parameter;

- **Sample**: subset of the population used to estimate $$ \theta $$;

- **Statistics**: any function (or observation) of census or sample data;

- **Estimator**: $$ \hat{\theta} $$ statistic that is used to reconstruct $$ \theta $$;

- **Estimate**: value of the estimator on a particular sample.

## Sampling and non-sampling errors

The discrepancy between the estimate and the parameter is due to two sources of error:

1. **Sampling errors** unavoidable, they are errors due to the fact that we are observing only a part of the population and they decrease as the sample size increases if the estimator $$ \hat{\theta} $$ is well constructed;

2. **Avoidable non-sampling errors**, they are errors due to a wrong construction of the sample or an incorrect estimator, it is not certain that these errors decrease as the sample size increases.

---

## Sample statistics

Once we have established which entities we are going to focus on, let's define which statistics are of main interest.

Consider a random sample of size $$ n $$:

$$ (X_1, ..., X_n) $$

the goal is to use the data obtained to reconstruct some parameters of the population. Simple descriptive statistics that measure the location, variability, and other parameters of a given population do not necessarily have to be in the sample already, but estimators and parameter estimates can be derived easily from this sample.

The main statistics we use to derive location information are:

- **sample mean**, to measure the sample mean value;

- **sample median**, to find the central value;

- **quantiles, percentiles, quartiles**, through which the portions of the sample are identified

While the statistics that measure the variability of the data (i.e. how wide the curve is on the graph) are:

- **sample variance** and **standard deviation**

- **interquartile range**

Each statistic is a random variable because it is calculated from a sample, which is why they are said to describe the _sample distribution_.

Statistics are used to estimate population parameters, e. g. the 'sample' mean is used to estimate the population mean.

As for the following sections, always remember that we are considering observations on independent and identically distributed random variables (i.i.d.) with expected value $$ E(X) = \mu $$ and variance $$ Var(X) = \sigma^2 $$.

### Sample Mean

The sample mean is a stylist of the population mean $$ \mu = E(X) $$ and is written:

$$ \bar {X} = \frac {1}{n} \sum\_{i = 1}^{n} X_i $$

therefore $$ \bar{x} $$ is an estimate of the population value $$ \mu $$, in fact $$ \bar {X} $$ is the random variable of the sample mean (i.e. the estimator), while with $$ \bar {x} $$ we refer to the estimate, that is the number observed with the estimator with a given sample.

> Summarizing, $$ \bar{X} $$ is an estimate of $$ \mu $$, while $$ \bar{x} $$ is an estimate of $$ \mu $$.

> The sample mean has many interesting properties: it is _undistorted_, _consistent_ and _asymptotically Normal_.
