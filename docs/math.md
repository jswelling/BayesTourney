---
usemathjax: true
---

For any given bout, we use a simple 'odds ratio' model to express the likelihood that some entrant $$k$$ will win against another entrant $$i$$ :

$$
P_{ki}=\frac{w_k}{w_k + w_i}
$$

where $$w_k$$ and $$w_i$$ are the 'weights' of $$k$$ and $$i$$ respectively.  For N players there are  N such weights, and those weights fully specify the model.  The likelihood that entrant $$k$$ will have a given number of wins and losses in all the bouts of the tourney is thus

$$
P_k \propto \prod _{i \neq k } \left ( \frac{w_k}{w_k + w_i} \right )^{\alpha_{ki}}\left ( \frac{w_i}{w_k + w_i} \right )^{\beta_{ki}}
$$

where $$N$$ is the set of all participants, $$i, k \in N$$, $$\alpha_{ij}$$ is the number of times $$i$$ wins over j, and $$\beta_{ij}$$ is the number of times $$i$$ loses to $$j$$ .  The likelihood that a given set of wins and losses will arise for all entrants is

$$
P \propto \prod_{k} \prod _{i \neq k } \left ( \frac{w_k}{w_k + w_i} \right )^{\alpha_{ki}}\left ( \frac{w_i}{w_k + w_i} \right )^{\beta_{ki}}
$$
.

For a mutation that takes $$w_k \mapsto {w_k}'$$ ,

{% raw %}
$$
\frac{{P_k}'}{P_k} = \prod _{i\neq k}\left ( \frac{{w_k}'}{w_k} \right )^{\alpha_{ki}} \left (\frac{w_k + w_i}{{w_k}' + w_i} \right )^{\alpha_{ki} + \beta_{ki}}
$$
{% endraw %}
