---
layout: page
permalink: /bibliography/
title: Bibliografia
description: Bibliografia consultabile della tesi.
years:
  [
    2021,
    2019,
    2018,
    2017,
    2014,
    2012,
    2010,
    2009,
    2008,
    2006,
    2005,
    2004,
    2002,
    2001,
    1999,
    1997,
    1996,
    1995,
    1994,
    1992,
    1991,
    1988,
    1987,
    1986,
    1985,
    1983,
    1982,
    1981,
    1978,
    1977,
    1972,
    1971,
    1968,
    1965,
    1963,
    1962,
    1958,
    1950,
    1947,
    1943,
    1937,
    1931,
    1903,
  ]
nav: true
---

<div class="publications">

{% for y in page.years %}

  <h2 class="year">{{y}}</h2>
  {% bibliography -f papers -q @*[year={{y}}]* %}
{% endfor %}

</div>
