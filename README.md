<img src="https://github.com/Talendar/nevopy/blob/master/docs/imgs/nevopy.png?raw=true" width="180" alt="NEvoPy logo">

<h2> Neuroevolution for Python </h2>

![Python versions](https://img.shields.io/pypi/pyversions/nevopy)
[![License](https://img.shields.io/github/license/Talendar/nevopy)](https://github.com/Talendar/nevopy/blob/master/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/nevopy)](https://pypi.org/project/nevopy/)
[![Documentation](https://img.shields.io/badge/api-reference-blue.svg)](https://nevopy.readthedocs.io/en/latest/index.html)

*NEvoPy* is an open source neuroevolution framework for Python. It allows 
researchers and enthusiasts to quickly tackle machine learning problems 
through the use of neuroevolutionary algorithms. In addition to being highly 
optimized for distributed computing, *NEvoPy* is also compatible with
TensorFlow.

Neuroevolution is a form of artificial intelligence that uses evolutionary
algorithms to generate artificial neural networks (ANNs). It is a vast and 
expanding field of research that holds many promises for the future. Currently,
*NEvoPy* implements the NEAT (NeuroEvolution of Augmenting Topologies) algorithm
and a custom fixed-topology deep-neuroevolutionary algorithm, but much more is
coming.

Here is a sample neural network generated by the NEAT algorithm to learn the XOR
logic function:

<img src="https://github.com/Talendar/nevopy/blob/master/docs/imgs/sample_network.png?raw=true" width="700" alt="Sample neural network">

<h2> Installing </h2>

To install the current release, use the following command:

```
$ pip install nevopy
```

<h2> Getting started </h2>

To get started with *NEvoPy*, please check out the examples available
[here](https://github.com/Talendar/nevopy/tree/master/examples).

The project's documentation is available
[here](https://nevopy.readthedocs.io/en/latest/index.html).

<h2> Citing </h2>

If you use *NEvoPy* in your research and would like to cite the *NEvoPy*
framework, here is a Bibtex entry you can use. It currently contains only the
name of the original author, but more names might be added as more people
contribute to the project. Also, feel free to contact me (Talendar/Gabriel) to
show me your work - I'd love to see it.

```
@misc{nevopy,
  title={ {NEvoPy}: A Neuroevolution Framework for Python},
  author={Gabriel Guedes Nogueira},
  howpublished={\url{https://github.com/Talendar/nevopy}},   
}
```
