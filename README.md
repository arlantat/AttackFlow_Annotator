# attackflow_12

This is a joint project for my degree's capstone course. Meant to be a web application that aids [the main repository](https://github.com/center-for-threat-informed-defense/attack-flow) in annotating attack vectors.

### My Main Contributions:

- Mapping user-typed information (in the form of excel sheets) to the correct JSON format that adheres to AttackFlow specifications with `app/models/annotation.py`.
- Visualise the resulting JSON files using existing tools with `app/models/visualise.py`.

## Set Up Docker

__Windows users will need to:__
   - Enable WSL on Windows:
   - Install a Linux Distribution
   - Follow steps from that Linux Distribution

__1. Clone and Navigate to the Project Repository__
   
__2. Build and Run Docker Containers__

   Use docker-compose to build and run the project:
   - Install docker desktop
   - Install docker & docker compose extensions
   - `docker-compose build`
   - `docker-compose up`

   This will start the required services, including the web application and the MongoDB database.

__3. Accessing the Application__

   Once the containers are up and running:
   
   Access to MongoDb Shell:
   
   - `docker-compose exec -it mongo mongosh`
   
   Access to web-project Shell:
   
   - `docker-compose exec web /bin/bash`
   - `python run.py` which should run on localhost

## Set up Project

Pull the latest version of main and Navigate to app.

- `curl -sSL https://install.python-poetry.org | python3 -`
- `poetry install`
- Double-check if attackflow is installed `af version`
- Access the virtual environment with `poetry shell`
- Install the missing python packages, which include the mitreattack library containing data for tactics and techniques: `pip install mitreattack-python`. [More details](https://mitreattack-python.readthedocs.io/en/latest/mitre_attack_data/mitre_attack_data.html)
- Visualisation example:
```
python models/visualise.py
af validate docs/sample_excel.json
af graphviz docs/sample_excel.json docs/equifax
dot -Tpng -O docs/equifax
# see the result at docs/equifax.png
```
