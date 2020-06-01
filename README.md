# Evaluating Federated Learning Algorithms

This repository contains artefacts for [A Performance Evaluation of Federated Learning Algorithms (DIDL'18)](https://dl.acm.org/doi/10.1145/3286490.3286559)

# Dependencies

* Erlang (>= OPT 20)
* conda
* gnome-terminal

We've run on Ubuntu 16.04 LTS as well as Ubuntu 20.04 LTS.

### Python set up
Python dependencies are defined in `conda_environment.yaml`.
Install the environment with:

```
$ conda env create -f conda_environment.yaml
```

### Setup Erlang's secret cookie:
If you plan to use multiple machines, you'll need to make sure that their Erlang cookies match.
For instance, you could do:
```
echo secretcookie > ~/.erlang.cookie
chmod 400 ~/.erlang.cookie
```
on all machines that you want to use.

# Usage

Please refer to `src/README.md`.

# Directories

Here are some explanations on the contents of the repository's directories.

## benchmark_results

Contains experiment results, i.e. logs from training with the various algorithms.
In other words, this is the raw data used to generate most figures in the paper.

## notebooks

Most notebooks create various plots based on the contents of `benchmark_results/`, save for a couple that partitions data.

To view and run the notebooks, you first need to start a Jupyter server.
With the `fl-eval` conda environment activated run:
```
$ jupyter notebook
```
A browser will open where you can navigate to `notebooks/` and inspect and/or run the notebooks.

You should be able to run notebooks right away as long as you started Jupyter in the root of the repository.

## src

This directory has all source code for running experiments.
This includes implementations of the federated learning algorithms and the distributed framework.
The directory also contains scripted experiments.
There's a lot going on here, and it's far form perfectly structured.
You'll find more details in `src/README.md`, e.g. how to run experiments of your own.

# Copyright

(c) 2018 - 2020 Fraunhofer-Chalmers Research Centre for Industrial Mathematics