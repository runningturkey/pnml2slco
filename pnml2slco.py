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
    # print(transtion_data)

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
    # print(place_data)

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
    # print(arc_data)

    return transtion_data, place_data, arc_data

# Generate the sum-up information for each transition using the parsed transition and arc data from the pnml file
# This fnction can organize the transition data for further use in the step of generating the SLCO code
def generate_transition_inf(transition_data, place_data, arc_data):
    transition_analysis = {}

    # Initialize transition information
    for transition in transition_data:
        transition_id = transition['transition_id']
        transition_analysis[transition_id] = {
            'transition_name': transition['transition_name'],
            'input_arcs': [],
            'output_arcs': []
        }

    # Initialize place information
    place_info = {}
    for place in place_data:
        place_id = place['place_id']
        place_info[place_id] = {
            'place_name': place['place_name'],
            'place_initial_marking': place['place_initial_marking']
        }

    # start finding corresponding information in the arc data
    for arc in arc_data:
        arc_id = arc['arc_id']
        arc_source = arc['arc_source']
        arc_target = arc['arc_target']
        arc_inscription = arc['arc_inscription']
        
        # find input arcs and input places for transition
        if arc_target in transition_analysis:
            transition_analysis[arc_target]['input_arcs'].append({
                'input_arc_id': arc_id,
                'input_place_id': arc_source,
                #'input_place_name': place_info[arc_source]['place_name'], # may not used
                #'input_place_initial_marking': place_info[arc_source]['place_initial_marking'], #may not used
                'input_arc_inscription': arc_inscription
            })
        
        # find output arcs and output place for transition
        if arc_source in transition_analysis:
            transition_analysis[arc_source]['output_arcs'].append({
                'output_arc_id': arc_id,
                'output_place_id': arc_target,
                #'output_place_name': place_info[arc_target]['place_name'],
                #'output_place_initial_marking': place_info[arc_target]['place_initial_marking'],
                'output_arc_inscription': arc_inscription
            })
    
    
    return transition_analysis

# Generate the code for the SLCO variables using the place data parsed from the PNML file
def generate_slco_variables(place_data):
    variable_statements = []
    for place in place_data:
        variable_name = place['place_id']
        initial_marking = place['place_initial_marking']
        variable_statement = f"Integer {variable_name} := {initial_marking}"
        variable_statements.append(variable_statement)
    return ", ".join(variable_statements)

# Generate the code for the SLCO state machines using the organized transition information using function 'generate_transition_inf'
def generate_slco_tansitions(transition_data, place_data, arc_data):

    transition_analysis = generate_transition_inf(transition_data, place_data, arc_data)

    result_codes = []

    for _, details in transition_analysis.items():
        input_conditions = []
        input_updates = []
        output_updates = []

        for input_arc in details['input_arcs']:
            input_place_id = input_arc['input_place_id']
            input_inscription = input_arc['input_arc_inscription']
            input_conditions.append(f"{input_place_id} > 0")
            input_updates.append(f"{input_place_id} := {input_place_id} - {input_inscription}")

        for output_arc in details['output_arcs']:
            output_place_id = output_arc['output_place_id']
            output_inscription = output_arc['output_arc_inscription']
            output_updates.append(f"{output_place_id} := {output_place_id} + {output_inscription}")

        condition_str = " and ".join(input_conditions)
        update_str = "; ".join(input_updates + output_updates)

        update_code = f"update -> update {{[{condition_str}; {update_str}]}}"
        result_codes.append(update_code)

    return "\n                ".join(result_codes)

# Generate the code for the SLCO model
def generate_slco_model(model_name, transition_data, place_data, arc_data):
    slco_template = """model %s {
  classes
    GlobalClass {
      variables
        %s
	  
      state machines
        SM { 
            initial update states 
            transitions
                %s
        }
	}

  objects
    globalObject : GlobalClass()
}
"""
    variables_statements = generate_slco_variables(place_data)
    state_machine_statements = generate_slco_tansitions(transition_data, place_data, arc_data)
    return slco_template % (model_name, variables_statements, state_machine_statements)



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <pnml_file>")
        sys.exit(1)
    pnml_file = sys.argv[1]
    transtion_data, place_data, arc_data = parse_pnml(pnml_file)
    print(generate_slco_model("PetriNetModel", transtion_data, place_data, arc_data))