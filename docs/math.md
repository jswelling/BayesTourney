---
usemathjax: true
---

A description of the math goes here.

{% comment %}
 {% raw %}
  $$a^2 + b^2 = c^2$$ --> note that all equations between these tags will not need escaping! 
 {% endraw %}
 {% endcomment %}

$$
P_{ki}=\frac{w_k}{w_k + w_i}
$$

$$
P_k \propto \prod _{i \neq k } \left ( \frac{w_k}{w_k + w_i} \right )^{\alpha_{ki}}\left ( \frac{w_i}{w_k + w_i} \right )^{\beta_{ki}}
$$

where $$N$$ is the set of all participants, $$i, k \in N$$, $$\alpha_{ij}$$ is the number of times $$i$$ wins over j, and $$\beta_{ij}$$ is the number of times $$i$$ loses to $$j$$ .

For a mutation that takes $$w_k \mapsto {w_k}'$$ ,

$$
\frac{{P_k}'}{P_k} = \prod _{i\neq k}\left ( \frac{{w_k}'}{w_k} \right )^{\alpha_{ki}} \left (\frac{w_k + w_i}{{w_k}' + w_i} \right )^{\alpha_{ki} + \beta_{ki}}
$$
