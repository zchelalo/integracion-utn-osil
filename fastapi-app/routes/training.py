from fastapi import APIRouter, status, Depends
from starlette.status import HTTP_200_OK
from middlewares.jwt_bearer import AdminRoleBearer
from config.database import Session, engine, Base

from services.usuarios import UsuarioService
from services.intents import IntentService
from services.responses import ResponseService
from services.steps import StepService
from services.steps_rule import StepRuleService

# import yaml
import ruamel.yaml

import docker

training_router = APIRouter()

Base.metadata.create_all(bind=engine)

############################################################################
# Crear domain.yml
############################################################################
@training_router.post(
    path='/training/domain', 
    tags=['training'], 
    status_code=status.HTTP_200_OK,
    # response_model=IntentSchema,
    dependencies=[Depends(AdminRoleBearer())]
  )
async def create_domain():
  db = Session()
  intents = IntentService(db).get_intents()

  respuestas = {}
  intenciones = []

  for intent in intents:
    intencion = intent.nombre_intent
    intenciones.append(intencion)

    responses = ResponseService(db).get_responses_by_intent_id(intent.id)
    respuestas_json = []

    for response in responses:
      respuestas_json.append(response.respuesta)

    respuesta = {
      "custom": {
        "json": respuestas_json
      }
    }

    # Usamos la intención como clave y la respuesta como valor
    respuestas[intent.nombre_respuesta] = [respuesta]

  # Agregar las intenciones al diccionario domain_data
  domain_data = {
    "version": "3.1",
    "intents": intenciones,
    "responses": respuestas,
    "session_config": {
        "session_expiration_time": 60,
        "carry_over_slots_to_new_session": True
    }
  }

  # Ruta completa al archivo domain.yml en el volumen compartido
  domain_path = "/app/shared_data/domain.yml"

  # Escribir el contenido en un archivo YAML
  yaml = ruamel.yaml.YAML()
  yaml.width = 10000
  # yaml.explicit_start = True

  with open(domain_path, "w") as yaml_file:
    yaml.dump(domain_data, yaml_file)

  return domain_data

############################################################################
# Crear nlu.yml
############################################################################
@training_router.post(
    path='/training/nlu', 
    tags=['training'], 
    status_code=status.HTTP_200_OK,
    # response_model=IntentSchema,
    dependencies=[Depends(AdminRoleBearer())]
  )
async def create_nlu():
  db = Session()
  intents = IntentService(db).get_intents()

  # Crear un diccionario con los datos dinámicos
  nlu_data = {
      "version": "3.1",
      "nlu": []
    }

  for intent in intents:
    nlu_data["nlu"].append(
      {
        "intent": intent.nombre_intent,
        "examples": intent.ejemplos
      }
    )

  # Nombre del archivo NLU
  nlu_filename = "/app/shared_data/data/nlu.yml"

  # Escribir el contenido en un archivo YAML
  yaml = ruamel.yaml.YAML()
  yaml.indent(offset=2)
  yaml.width = 10000

  with open(nlu_filename, "w") as nlu_file:
    yaml.dump(nlu_data, nlu_file)

  # Corregir la indentación de "intent" aquí
  with open(nlu_filename, "r") as nlu_file:
    nlu_content = nlu_file.read()
    nlu_content = nlu_content.replace("  - intent", "- intent")
    nlu_content = nlu_content.replace("  examples:", "  examples: |")

  with open(nlu_filename, "w") as nlu_file:
    nlu_file.write(nlu_content)

  return intents

############################################################################
# Crear stories.yml
############################################################################
@training_router.post(
    path='/training/stories', 
    tags=['training'], 
    status_code=status.HTTP_200_OK,
    # response_model=IntentSchema,
    dependencies=[Depends(AdminRoleBearer())]
  )
async def create_stories():
  db = Session()
  steps = StepService(db).get_steps_story_and_intent()

  # Crear un diccionario con el formato deseado
  stories_data  = {
    "version": "3.1",
    "stories": []
  }

  formatted_data = {}
  for step in steps:
    descripcion = step.descripcion
    intent = step.nombre_intent
    respuesta = step.nombre_respuesta

    if descripcion not in formatted_data:
      formatted_data[descripcion] = {
        "intent": [intent],
        "respuesta": [respuesta]
      }
    else:
      formatted_data[descripcion]["intent"].append(intent)
      formatted_data[descripcion]["respuesta"].append(respuesta)

  # Convertir los datos al formato de Rasa
  for descripcion, data in formatted_data.items():
    story_entry = {
      "story": descripcion,
      "steps": []
    }
    for intent, respuesta in zip(data["intent"], data["respuesta"]):
      story_entry["steps"].append({"intent": intent})
      story_entry["steps"].append({"action": respuesta})
    stories_data["stories"].append(story_entry)

  # Nombre del archivo Stories
  stories_filename = "/app/shared_data/data/stories.yml"
    
  # Escribir el contenido en un archivo YAML
  yaml = ruamel.yaml.YAML()
  yaml.indent(offset=2)
  yaml.width = 10000

  with open(stories_filename, "w") as stories_file:
    yaml.dump(stories_data, stories_file)

  # Corregir la indentación de "intent" aquí
  with open(stories_filename, "r") as stories_file:
    stories_content = stories_file.read()
    stories_content = stories_content.replace("  - story", "- story")
    stories_content = stories_content.replace("    - intent", "  - intent")
    stories_content = stories_content.replace("    - action", "  - action")

  with open(stories_filename, "w") as stories_file:
    stories_file.write(stories_content)

  return stories_data

############################################################################
# Crear rules.yml
############################################################################
@training_router.post(
    path='/training/rules', 
    tags=['training'], 
    status_code=status.HTTP_200_OK,
    # response_model=IntentSchema,
    dependencies=[Depends(AdminRoleBearer())]
  )
async def create_rules():
  db = Session()
  steps = StepRuleService(db).get_step_rule_rule_and_intent()

  # Crear un diccionario con el formato deseado
  rules_data  = {
    "version": "3.1",
    "rules": []
  }

  formatted_data = {}
  for step in steps:
    descripcion = step.descripcion
    intent = step.nombre_intent
    respuesta = step.nombre_respuesta

    if descripcion not in formatted_data:
      formatted_data[descripcion] = {
        "intent": [intent],
        "respuesta": [respuesta]
      }
    else:
      formatted_data[descripcion]["intent"].append(intent)
      formatted_data[descripcion]["respuesta"].append(respuesta)

  # Convertir los datos al formato de Rasa
  for descripcion, data in formatted_data.items():
    rule_entry = {
      "rule": descripcion,
      "steps": []
    }
    for intent, respuesta in zip(data["intent"], data["respuesta"]):
      rule_entry["steps"].append({"intent": intent})
      rule_entry["steps"].append({"action": respuesta})
    rules_data["rules"].append(rule_entry)

  # Nombre del archivo Stories
  rules_filename = "/app/shared_data/data/rules.yml"
    
  # Escribir el contenido en un archivo YAML
  yaml = ruamel.yaml.YAML()
  yaml.indent(offset=2)
  yaml.width = 10000

  with open(rules_filename, "w") as rules_file:
    yaml.dump(rules_data, rules_file)

  # Corregir la indentación de "intent" aquí
  with open(rules_filename, "r") as rules_file:
    rules_content = rules_file.read()
    rules_content = rules_content.replace("  - rule", "- rule")
    rules_content = rules_content.replace("    - intent", "  - intent")
    rules_content = rules_content.replace("    - action", "  - action")

  with open(rules_filename, "w") as rules_file:
    rules_file.write(rules_content)

  return rules_data

############################################################################
# Crear el modelo
############################################################################
# Crea el cliente de Docker
client = docker.from_env()

@training_router.post(
    path='/training/model', 
    tags=['training'], 
    status_code=status.HTTP_200_OK,
    # response_model=IntentSchema,
    dependencies=[Depends(AdminRoleBearer())]
  )
async def create_model():
  try:
    # Obtén el contenedor de Rasa por su nombre o ID
    rasa_container = client.containers.get("rasa_app")

    # Ejecuta el comando "rasa train" en el contenedor
    exec_command = rasa_container.exec_run(["rasa", "train", "-d", "/app/shared_data/domain.yml", "--data", "/app/shared_data/data"])

    # Obtiene la salida y el código de salida
    output = exec_command.output.decode()
    exit_code = exec_command.exit_code

    return {"output": output, "exit_code": exit_code}
  except Exception as e:
    return {"error": str(e)}

############################################################################
# Parar rasa
############################################################################
@training_router.post(
    path='/training/stop', 
    tags=['training'], 
    status_code=status.HTTP_200_OK,
    # response_model=IntentSchema,
    dependencies=[Depends(AdminRoleBearer())]
  )
async def stop_rasa():
  try:
    rasa_container = client.containers.get("rasa_app")
    rasa_container.stop()
    return {"message": "El servicio de Rasa termino de forma exitosa"}
  except Exception as e:
    return {"error": str(e)}

############################################################################
# Iniciar rasa
############################################################################
@training_router.post(
    path='/training/start', 
    tags=['training'], 
    status_code=status.HTTP_200_OK,
    # response_model=IntentSchema,
    dependencies=[Depends(AdminRoleBearer())]
  )
async def start_rasa():
  try:
    rasa_container = client.containers.get("rasa_app")
    rasa_container.start()
    return {"message": "El servicio de Rasa inicio de forma exitosa"}
  except Exception as e:
    return {"error": str(e)}