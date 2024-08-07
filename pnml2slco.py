import xml.etree.ElementTree as ET
import sys

def validate_pnml(pnml_tree):
    root = pnml_tree.getroot()
    # Validate if it's a PNML file
    if root.tag != '{http://www.pnml.org/version-2009/grammar/pnml}pnml':
        raise Exception('Not a PNML file')
    print('PNML file is valid')


def check_petri_net_type(pnml_tree):
    root = pnml_tree.getroot()   
     
    # Find the <net> element

    net = root.find("{http://www.pnml.org/version-2009/grammar/pnml}net")
    if net is None:
        raise Exception('No net found in PNML file')
    
    # Get the type attribute of the <net> element
    net_type = net.get('type')
    if net_type is None:
        raise Exception('No type attribute found in net element')
    
    # Check if the type is 'http://www.pnml.org/version-2009/grammar/ptnet'
    if net_type != 'http://www.pnml.org/version-2009/grammar/ptnet':
        raise Exception(f'Unsupported Petri net type: {net_type}')
    print('Petri net type is supported (PTNet)')

def parse_pnml(pnml_file):
    tree = ET.parse(pnml_file)
    validate_pnml(tree)
    check_petri_net_type(tree)
    root = tree.getroot()
    namespace = {'pnml': 'http://www.pnml.org/version-2009/grammar/pnml'}

    # parse the transitions
    transtion_data = []
    for transition in root.findall('.//pnml:transition', namespaces=namespace):
        transition_id = transition.get('id')
        # deal with no ID transition errors
        if transition_id is None:
            print('Warning: Transition without ID found, skipping.')
            continue
        
        # find transition name if not found set to empty string
        name_element = transition.find('pnml:name/pnml:text', namespaces=namespace)
        name_text = name_element.text if name_element is not None else ""


        data = {
            'transition_id': transition_id,
            'transition_name': name_text
        }
        transtion_data.append(data)
    print(transtion_data)

    # parse the places
    place_data = []
    for place in root.findall('.//pnml:place', namespaces=namespace):
        place_id = place.get('id')
        # deal with no ID place errors
        if place_id is None:
            print('Warning: Place without ID found, skipping.')
            continue
        
        # find place name if not found set to empty string
        name_element = place.find('pnml:name/pnml:text', namespaces=namespace)
        name_text = name_element.text if name_element is not None else ""

        # find the initial marking
        initial_marking = place.find('pnml:initialMarking/pnml:text', namespaces=namespace)
        initial_marking_text = initial_marking.text if initial_marking is not None else "0"

        data = {
            'place_id': place_id,
            'place_name': name_text,
            'place_initial_marking': initial_marking_text
        }
        place_data.append(data)
    print(place_data)
    # parse the arcs
    arc_data = []  
    for arc in root.findall('.//pnml:arc', namespaces=namespace):
        arc_id = arc.get('id')
        # deal with no ID arc errors
        if arc_id is None:
            print('Warning: Arc without ID found, skipping.')
            continue
        
        # find source and target
        source = arc.get('source')
        target = arc.get('target')
        if source is None or target is None:
            print('Warning: Arc without source or target found, skipping.')
            continue

        # find arc inscription (weight)
        inscription = arc.find('pnml:inscription/pnml:text', namespaces=namespace)
        inscription_text = inscription.text if inscription is not None else "1"

        data = {
            'arc_id': arc_id,
            'arc_source': source,
            'arc_target': target,
            'arc_inscription': inscription_text
        }
        arc_data.append(data)
    print(arc_data)

    return transtion_data, place_data, arc_data

# Generate the code for the SLCO variables using the place data parsed from the PNML file
def generate_slco_variables(place_data):
    variable_statements = []
    for place in place_data:
        variable_name = place['place_id']
        initial_marking = place['place_initial_marking']
        variable_statement = f"Integer {variable_name} := {initial_marking}"
        variable_statements.append(variable_statement)
    return ", ".join(variable_statements)

# Generate the code for the SLCO state machines using the transition and arc data parsed from the PNML file
def generate_slco_state_machines(transition_data, arc_data):
    pass

# Generate the code for the SLCO model
def generate_slco_model(model_name, place_data, state_machines):
    slco_template = """model %s {
  classes
    GlobalClass {
      variables
        %s
	  
      state machines
        SM { 
            initial fire states 
            transitions
                %s
	}

  objects
    globalObject : GlobalClass()
}
"""
    variables_statement = generate_slco_variables(place_data)
    return slco_template % (model_name, variables_statement, state_machines)



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <pnml_file>")
        sys.exit(1)
    pnml_file = sys.argv[1]
    _, data,_ = parse_pnml(pnml_file)
    print(generate_slco_model("PetriNetModel", data, []))