import json
import uuid
import pytz
import pandas as pd
import re
from stix2 import Bundle
from datetime import datetime
from mitreattack.stix20 import MitreAttackData


IDENTITY_ID = "f685eafd-6ae2-4685-a0e6-4dcc3ca3b7e5"  # af12 unique identifier
EXTENSION_DEFINITION = {  # describe the attackflow extension
    "type": "extension-definition",
    "id": "extension-definition--fb9c968a-745b-4ade-9b25-c324172197f4",
    "spec_version": "2.1",
    "created": "2022-08-02T19:34:35.143Z",
    "modified": "2022-08-02T19:34:35.143Z",
    "name": "Attack Flow",
    "description": "Extends STIX 2.1 with features to create Attack Flows.",
    "created_by_ref": "identity--fb9c968a-745b-4ade-9b25-c324172197f4",
    "schema": "https://center-for-threat-informed-defense.github.io/attack-flow/stix/attack-flow-schema-2.0.0.json",
    "version": "2.0.0",
    "extension_types": [
        "new-sdo"
    ],
    "external_references": [
        {
        "source_name": "Documentation",
        "description": "Documentation for Attack Flow",
        "url": "https://center-for-threat-informed-defense.github.io/attack-flow"
        },
        {
        "source_name": "GitHub",
        "description": "Source code repository for Attack Flow",
        "url": "https://github.com/center-for-threat-informed-defense/attack-flow"
        }
    ]
}
IDENTITY = {  # describe the af12 group
    "type": "identity",
    "id": "identity--" + IDENTITY_ID,
    "spec_version": "2.1",
    "created": "2023-08-01T19:34:35.143Z",
    "modified": "2023-08-01T19:34:35.143Z",
    "created_by_ref": "identity--" + IDENTITY_ID,
    "name": "University of Adelaide Comp Sci Project attackflow_12",
    "identity_class": "group"
}
# unique to this code run instance
TIME_CREATED = str(datetime.now().replace(tzinfo=pytz.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))


def generate(name: str, description: str):   # main collection of objects
    """
    Returns a tuple of bundle and the unique attackflow object.
    Note that the attackflow must STILL be manually added with batch_add. 
    Required: name (The name of the Attack Flow) and description.
    """
    bundle = dict(Bundle())
    bundle["spec_version"] = "2.1"
    bundle["created"] = TIME_CREATED
    bundle["modified"] = TIME_CREATED
    bundle["objects"] = []

    attackflow_id = str(uuid.uuid4())  # unique to each attackflow
    attackflow = {
        "type": "attack-flow",
        "id": "attack-flow--" + attackflow_id,
        "spec_version": "2.1",
        "created": TIME_CREATED,
        "modified": TIME_CREATED,
        "extensions": {
            "extension-definition--fb9c968a-745b-4ade-9b25-c324172197f4": {
            "extension_type": "new-sdo"
            }
        },
        "created_by_ref": IDENTITY["id"],
        "name": name,
        "description": description,
        "scope": "incident"  # probably always incidents
    }

    bundle["objects"].append(EXTENSION_DEFINITION)
    bundle["objects"].append(IDENTITY)

    return (bundle, attackflow)


def new_sdo(sdo_type: str, attributes: dict) -> dict:
    '''
    STIX Domain Objects. Most common sdo_types are "threat-actor", "infrastructure", "vulnerability", "malware". 
    Attackflow has made custom sdo_types which are "attack-action", "attack-asset", "attack-condition", "attack-operator". 
    Info on which attributes to use can be found at 
    https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html#_nrhq5e9nylke and 
    https://center-for-threat-informed-defense.github.io/attack-flow/language/#attack-flow-sdos 
    for custom SDOs.
    '''
    sdo = {
        "type": sdo_type,
        "id": sdo_type + "--" + str(uuid.uuid4()),
        "spec_version": "2.1",
        "created": TIME_CREATED,
        "modified": TIME_CREATED
    }

    if sdo_type in ("attack-action", "attack-asset", "attack-condition", "attack-operator"):
        sdo["extensions"] = {"extension-definition--fb9c968a-745b-4ade-9b25-c324172197f4" : {"extension_type":"new-sdo"}}

    for key, value in attributes.items():
        sdo[key] = value
    return sdo


def batch_add(bundle: dict, objects: list) -> dict:
    '''Add objects to main bundle.'''
    for obj in objects:
        bundle["objects"].append(obj)
    return bundle


def link(key: str, parent: dict, children: list, replace=False) -> dict:
    ''' Connects an object to another and returns the parent. 
    key is one of the sdo properties defined at 
    https://center-for-threat-informed-defense.github.io/attack-flow/language/#attack-flow-sdos, 
    for example 'effect_refs' and 'asset_refs'.
    children can be 1 or many objects. 
    Set replace to True for replacement of property values, default False means appending.
    '''
    if children == []:
        return parent
    if not key.endswith('s'):
        parent[key] = children[0]["id"]
        return parent
    if replace or key not in parent:
        parent[key] = []
    for child in children:
        parent[key].append(child["id"])
    return parent

def run_test():
    bundle, attackflow = generate('Pizza Theft', 'A pizza theft performed by Sly')
    threat_actor = new_sdo("threat-actor", { 'name' : 'Sly' })
    action0 = new_sdo("attack-action", { 'name' : 'Lurk' })
    attackflow = link("start_refs", attackflow, [action0])

    asset0 = new_sdo("attack-asset", { 'name' : 'Pizzarina' })
    action1 = new_sdo("attack-action", { 'name' : 'Snatch' })
    action0 = link("effect_refs", action0, [action1])
    action1 = link("asset_refs", action1, [asset0])

    condition0 = new_sdo("attack-condition", { 'description' : 'Pizza is compromised?' })
    action1 = link("effect_refs", action1, [condition0])

    action2 = new_sdo("attack-action", { 'name' : 'Run' })
    condition0 = link("on_true_refs", condition0, [action2])
    action3 = new_sdo("attack-action", { 'name' : 'Still Run' })
    condition0 = link("on_false_refs", condition0, [action3])

    operator0 = new_sdo("attack-operator", { 'operator' : 'OR' })
    action2 = link("effect_refs", action2, [operator0])
    action3 = link("effect_refs", action3, [operator0])

    action4 = new_sdo("attack-action", { 'name' : 'Got out', 'description' : 'Got out nonetheless, SAJ' })
    operator0 = link("effect_refs", operator0, [action4])

    bundle = batch_add(bundle, 
        [attackflow, threat_actor,
        action0, action1, action2, action3, action4,
        asset0, condition0, operator0])
    
    with open("test.json", "w") as f:
        json.dump(bundle, f, indent=2)

def tactic_name_to_id() -> dict:
    '''Return a dictionary of tactic name and id as key and value. 
    Saves the hassle of checking tactic id on the website.'''
    tactics = {}
    tactic_list = MitreAttackData("enterprise-attack.json").get_tactics()
    for tactic in tactic_list:
        tactics[tactic["name"]] = tactic["external_references"][0]["external_id"]
    return tactics

def _process_affected(o_refs) -> list:
    '''output affected_ids as a list.'''
    o_refs = re.findall(r'\d+', o_refs)
    if o_refs == []:
        return o_refs
    if o_refs[-1] == '0':
        o_refs.pop()
    return o_refs

def _process_properties(o_props, o_name, o_desc) -> dict:
    '''process json properties of object which includes including name and description.'''
    if not o_props:
        o_props = {}
    elif o_props[0] == '{' and o_props[-1] == '}':
        o_props = json.loads(o_props)
    else:
        print(f'Error: properties must be a JSON object')
    if o_name:
        o_props['name'] = o_name
    if o_desc:
        o_props['description'] = o_desc
    return o_props

def _batch_link(affected, id_to_object, col) -> dict:
    for k, v in affected.items():
        parent_obj = id_to_object[k]
        children_objs = [id_to_object[c] for c in v]
        if parent_obj['type'] == 'attack-flow':
            attribute = 'start_refs'
        elif parent_obj['type'] == 'attack-action':
            if col == 1:
                attribute = 'effect_refs'
            elif col == 2:
                attribute = 'asset_refs'
        elif parent_obj['type'] == 'attack-condition':
            if col == 1:
                attribute = 'on_true_refs'
            elif col == 2:
                attribute = 'on_false_refs'
        elif parent_obj['type'] == 'attack-operator':
            attribute = 'effect_refs'
        parent_obj = link(attribute, parent_obj, children_objs)
        id_to_object[k] = parent_obj
    return id_to_object

def run_excel(file):
    '''Clarification for excel format: 
    As you can see in docs/sample_excel, I have 7 columns now. One change is affected_ids 
    separated into two cols for some object (attack-action has effect_refs as col 1 
    and asset_refs as col 2 for example, see _batch_link for more). The other change is 
    properties col for things like tactic_id and operator, which must be a valid json object.
    '''
    df = pd.read_excel(file)
    df = df.fillna('')  # replace all NaN as ''
    df = df.astype(str)  # make the entire df of type str, INCLUDING id
    # print(df)
    
    tactics = tactic_name_to_id()
    print(tactics) # feel free to use this
    affected1, affected2 = {}, {}  # maps parent id to children ids
    id_to_object = {}  # maps object id to object

    for index, row in df.iterrows():
        # the reason for separating affected_ids is because attack-action and attack-condition
        # has two kind of children (asset or others | true refs or false refs).
        id, o_type, o_name, o_desc, o_refs1, o_refs2, o_props = [c.strip() for c in row]
        # print(id, o_type, o_name, o_desc, o_refs1, o_refs2, o_props, sep='|')
        if not o_type or not id:
            print(f'Error: row {id} - object type or id cannot be empty')
            return
        if ' ' in o_refs1 or ' ' in o_refs2:
            print(f'Error: row {id} - no whitespace allowed in affected ids')
            return
        o_refs1 = _process_affected(o_refs1)
        o_refs2 = _process_affected(o_refs2)
        o_props = _process_properties(o_props, o_name, o_desc)
        
        # print(id, o_type, o_name, o_desc, o_refs1, o_refs2, o_props, sep='|')
        if o_type == 'attack-flow':
            if id != '0':
                print(f'Error: row {id} - attack-flow must have id 0')
            bundle, attackflow = generate(o_name, o_desc)
            id_to_object[id] = attackflow
        else:
            new_object = new_sdo(o_type, o_props)
            id_to_object[id] = new_object
        affected1[id] = o_refs1
        affected2[id] = o_refs2
    id_to_object = _batch_link(affected1, id_to_object, 1)
    id_to_object = _batch_link(affected2, id_to_object, 2)

    bundle = batch_add(bundle, list(id_to_object.values()))
    with open("docs/sample_excel.json", "w") as f:
        json.dump(bundle, f, indent=2)

if __name__ == "__main__":
    # run_test()
    run_excel('docs/sample_excel.xlsx')
    # then try to run af validate excel.json at terminal and visualise with vizgraph
