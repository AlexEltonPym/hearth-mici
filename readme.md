# Dependencies

 ./gradlew spellsource-server:shadowJar
git submodule update --init --recursive 

 1. Source your virtual environment.
 2. Install the Spellsource package using python setup.py install from the 
Spellsource/python directory.
 3. Install the remaining dependencies:
# on macOS
pip install scoop matplotlib deap fpdf pyfiglet
brew install graphviz
pip install --global-option=build_ext --global-option="-I/opt/homebrew/Cellar/graphviz/3.0.0/include/" \
          --global-option="-L/opt/homebrew/Cellar/graphviz/3.0.0/lib" pygraphviz
