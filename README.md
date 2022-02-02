# Bril-Dev

This repository contains experimental tools of the [Bril](https://github.com/sampsyo/bril) compiler for Cornell [CS 6120](https://www.cs.cornell.edu/courses/cs6120/2022sp).

Following shows the installation commands that can be used.

```bash
git clone https://github.com/sampsyo/bril.git
cd bril-ts
yarn
yarn build
yarn link
export PATH=$(yarn global bin):$PATH

cd ..
python3 -m venv ~/.venv/bril-dev
source ~/.venv/bril-dev/bin/activate
pip install flit
flit install --symlink

pip install turnt
make test
```