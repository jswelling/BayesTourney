---
usemathjax: true
---

For any given bout, we use a simple 'odds ratio' model to express the likelihood that some entrant $$k$$ will win against another entrant $$i$$ :

$$
P_{ki}=\frac{w_k}{w_k + w_i}
$$

where $$w_k$$ and $$w_i$$ are the 'weights' of $$k$$ and $$i$$ respectively.  For N players there are  N such weights, and those weights fully specify the model.  

The weights are not known a priori, but at any given point in the tournament the outcomes of a set of such bouts are known.  The objective is to estimate the weights based on those known outcomes.  A given outcome could arise from a range of possible weights, since the outcome of any given bout is random.  Thus, the formal statement of the objective is to estimate the probability distribution function ( *pdf* ) on the N-dimensional set of weights parameterized by the specific set of observed outcomes.

We will do this using the [Metropolis-Hastings Algorithm](https://en.wikipedia.org/wiki/Metropolis%E2%80%93Hastings_algorithm).  In this specific case the jump function will be a Normal distribution, which is symmetric, so the algorithm is technically Metropolis rather than Metropolis-Hastings.

The likelihood that entrant $$k$$ will have a given number of wins and losses in all the bouts of the tourney is thus

$$
P_k \propto \prod _{i \neq k } \left ( \frac{w_k}{w_k + w_i} \right )^{\alpha_{ki}}\left ( \frac{w_i}{w_k + w_i} \right )^{\beta_{ki}}
$$

where $$N$$ is the set of all participants, $$i, k \in N$$, $$\alpha_{ij}$$ is the number of times $$i$$ wins over j, and $$\beta_{ij}$$ is the number of times $$i$$ loses to $$j$$ .  The likelihood that a given set of wins and losses will arise for all entrants is

$$
P \propto \prod_{k} \prod _{i \neq k } \left ( \frac{w_k}{w_k + w_i} \right )^{\alpha_{ki}}\left ( \frac{w_i}{w_k + w_i} \right )^{\beta_{ki}} .
$$

For a mutation that takes $$w_k \mapsto {w_k}'$$ ,

{% raw %}
$$
\frac{P'}{P} = \prod _{i\neq k}\left ( \frac{{w_k}'}{w_k} \right )^{\alpha_{ki}} \left (\frac{w_k + w_i}{{w_k}' + w_i} \right )^{\alpha_{ki} + \beta_{ki}}
$$
{% endraw %}
