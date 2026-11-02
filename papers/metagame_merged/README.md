# Pokémon and Hearthstone metagame prediction

[Read the paper (PDF)](main.pdf).

This merged manuscript studies metagame prediction in Pokémon and Hearthstone. It includes the clarification of how simulated outcomes are used in ABC-Meta, the Pokémon surrogate, and Hearthstone's probe-guided evolution.

The earlier Hearthstone-only manuscript remains in [../metagame_prediction](../metagame_prediction).

## Build

The source is `main.tex`, with references in `refs.bib`. Figures are drawn in LaTeX. Use a TeX distribution with IEEEtran, TikZ, and PGFPlots installed:

```sh
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```
