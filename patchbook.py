"""
PATCHBOOK MARKUP LANGUAGE & PARSER
CREATED BY SPEKTRO AUDIO
http://spektroaudio.com/
"""

import sys
import re
import os
import argparse
import json
import tempfile
import subprocess

# Parser INFO
parserVersion = "b3"

# Reset main dictionary
mainDict = {
    "info": {"patchbook_version": parserVersion},
    "modules": {},
    "comments": []
}

# Available connection types
connectionTypes = {
    "->": "audio",
    ">>": "cv",
    "p>": "pitch",
    "g>": "gate",
    "t>": "trigger",
    "c>": "clock"
}


# Reset global variables
lastModuleProcessed = ""
lastVoiceProcessed = ""

# Parse script arguments
parser = argparse.ArgumentParser()
parser.add_argument("-file", type=str, default="",
                    help="Name of the text file that will be parsed (including extension)")
parser.add_argument("-debug", type=int, default=0,
                    help="Enable Debugging Mode")
args = parser.parse_args()
filename = args.file
debugMode = args.debug
connectionID = 0

# Set up debugMode
if args.debug == 1:
    debugMode = True
else:
    debugMode = False


def initial_print():
    print()
    print("██████████████████████████████")
    print("       PATCHBOOK PARSER       ")
    print("   Created by Spektro Audio   ")
    print("██████████████████████████████")
    print()
    print("Version " + parserVersion)
    print()


def get_script_path():
    # Get path to python script
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def getFilePath(filename):
    try:
        # Append script path to the filename
        base_dir = get_script_path()
        filepath = os.path.join(base_dir, filename)
        if debugMode:
            print("File path: " + filepath)
        return filepath
    except IndexError:
        pass


def parseFile(filename):
    # This function reads the txt file and process each line.
    lines = []
    try:
        print("Loading file: " + filename)
        with open(filename, "r") as file:
            for l in file:
                lines.append(l)
                regexLine(l)
    except TypeError:
        print("ERROR. Please add text file path after the script.")
    except FileNotFoundError:
        print("ERROR. File not found.")
    print("File successfully processed.")
    print()


def regexLine(line):
    global lastModuleProcessed
    global lastVoiceProcessed

    if debugMode:
        print()
    if debugMode:
        print("Processing: " + line)

    # CHECK FOR COMMENTS
    if debugMode:
        print("Checking input for comments...")
    re_filter = re.compile(r"^\/\/\s?(.+)$")  # Regex for "// Comments"
    re_results = re_filter.search(line.strip())
    try:
        comment = re_results.group().replace("//", "").strip()
        if debugMode:
            print("New comment found: " + comment)
            addComment(comment)
        return
    except AttributeError:
        pass

    # CHECK FOR VOICES
    if debugMode:
        print("Cheking input for voices...")
    re_filter = re.compile(r"^(.+)\:$")  # Regex for "VOICE 1:"
    re_results = re_filter.search(line)
    try:
        # For some reason the Regex filter was still detecting parameter declarations as voices,
        # so I'm also running the results through an if statement.
        results = re_results.group().replace(":", "")
        if "*" not in results and "-" not in results and "|" not in results:
            if debugMode:
                print("New voice found: " + results.upper())
            lastVoiceProcessed = results.upper()
            return
    except AttributeError:
        pass

    # CHECK FOR CONNECTIONS
    if debugMode:
        print("Cheking input for connections...")
    re_filter = re.compile(
        r"\-\s(.+)[(](.+)[)]\s+(\>\>|\-\>|[a-z]\>)\s(.+)[(](.+)[)]\s(\[.+\])?$")
    re_results = re_filter.search(line)
    try:
        results = re_results.groups()
        voice = lastVoiceProcessed
        if len(results) == 6:
            if debugMode:
                print("New connection found, parsing info...")
            # args = parseArguments(results[5])
            # results = results[:5]
            addConnection(results, voice)
            return
    except AttributeError:
        pass

    # CHECK PARAMETERS
    if debugMode:
        print("Checking for parameters...")
    # If single-line parameter declaration:
    re_filter = re.compile(r"^\*\s(.+)\:\s?(.+)?$")
    re_results = re_filter.search(line.strip())
    try:
        # Get module name
        results = re_results.groups()
        module = results[0].strip().lower()
        if debugMode:
            print("New module found: " + module)
        if results[1] != None:
            # If parameters are also declared
            parameters = results[1].split(" | ")
            for p in parameters:
                p = p.split(" = ")
                addParameter(module, p[0].strip().lower(), p[1].strip())
            return
        elif results[1] == None:
            if debugMode:
                print("No parameters found. Storing module as global variable...")
            lastModuleProcessed = module
            return
    except AttributeError:
        pass

    # If multi-line parameter declaration:
    if "|" in line and "=" in line and "*" not in line:
        module = lastModuleProcessed.lower()
        if debugMode:
            print("Using global variable: " + module)
        parameter = line.split(" = ")[0].replace("|", "").strip().lower()
        value = line.split(" = ")[1].strip()
        addParameter(module, parameter, value)
        return


def parseArguments(args):
    # This method takes an arguments string like "[color = blue]" and converts it to a dictionary
    args_string = args.replace("[", "").replace("]", "")
    args_array = args_string.split(",")
    args_dict = {}

    if debugMode:
        print("Parsing arguments: " + args)

    for item in args_array:
        item = item.split("=")
        name = item[0].strip()
        value = item[1].strip()
        args_dict[name] = value
        if debugMode:
            print(name + " = " + value)

    if debugMode:
        print("All arguments processes.")

    return args_dict


def addConnection(list, voice="none"):
    global mainDict
    global connectionTypes
    global connectionID

    connectionID += 1

    if debugMode:
        print("Adding new connection...")
    if debugMode:
        print("-----")

    output_module = list[0].lower().strip()
    output_port = list[1].lower().strip()

    if debugMode:
        print("Output module: " + output_module)
    if debugMode:
        print("Output port: " + output_port)

    try:
        connection_type = connectionTypes[list[2].lower()]
        if debugMode:
            print("Matched connection type: " + connection_type)
    except KeyError:
        print("Invalid connection: " + list[2])
        connection_type = "cv"

    input_module = list[3].lower().strip()
    input_port = list[4].lower().strip()

    if list[5] is not None:
        arguments = parseArguments(list[5])
    else:
        arguments = {}

    if debugMode:
        print("Input module: " + input_module)
    if debugMode:
        print("Input port: " + output_port)

    checkModuleExistance(output_module, output_port, "out")
    checkModuleExistance(input_module, input_port, "in")

    if debugMode:
        print("Appending output and input connections to mainDict...")

    output_dict = {
        "input_module": input_module,
        "input_port": input_port,
        "connection_type": connection_type,
        "voice": voice,
        "id": connectionID}

    input_dict = {
        "output_module": output_module,
        "output_port": output_port,
        "connection_type": connection_type,
        "voice": voice,
        "id": connectionID}

    for key in arguments:
        output_dict[key] = arguments[key]
        input_dict[key] = arguments[key]

    mainDict["modules"][output_module]["connections"]["out"][output_port].append(
        output_dict)
    mainDict["modules"][input_module]["connections"]["in"][input_port] = input_dict
    if debugMode:
        print("-----")


def checkModuleExistance(module, port="port", direction=""):
    global mainDict

    if debugMode:
        print("Checking if module already existing in main dictionary: " + module)

    # Check if module exists in main dictionary
    if module not in mainDict["modules"]:
        mainDict["modules"][module] = {
            "parameters": {},
            "connections": {"out": {}, "in": {}}
        }

    # If it exists, check if the port exists
    if direction == "in":
        if port not in mainDict["modules"][module]["connections"]["in"]:
            mainDict["modules"][module]["connections"]["in"][port] = []

    if direction == "out":
        if port not in mainDict["modules"][module]["connections"]["out"]:
            mainDict["modules"][module]["connections"]["out"][port] = []


def addParameter(module, name, value):
    checkModuleExistance(module)
    # Add parameter to mainDict
    if debugMode:
        print("Adding parameter: " + module + " - " + name + " - " + value)
    mainDict["modules"][module]["parameters"][name] = value


def addComment(value):
    mainDict["comments"].append(value)


def askCommand():
    command = input("> ").lower().strip()
    if command == "module":
        detailModule()
    elif command == "print":
        printDict()
    elif command == "export":
        exportJSON()
    elif command == "connections":
        printConnections()
    elif command == "graph":
        graphviz()
    else:
        print("Invalid command, please try again.")
    askCommand()


def detailModule():
    global mainDict
    module = input("Enter module name: ").lower()
    if module in mainDict["modules"]:
        print("-------")
        print("Showing information for module: " + module.upper())
        print()
        print("Inputs:")
        for c in mainDict["modules"][module]["connections"]["in"]:
            keyvalue = mainDict["modules"][module]["connections"]["in"][c]
            print(keyvalue["output_module"].title() + " (" + keyvalue["output_port"].title(
            ) + ") > " + c.title() + " - " + keyvalue["connection_type"].title())
        print()

        print("Outputs:")
        for x in mainDict["modules"][module]["connections"]["out"]:
            port = mainDict["modules"][module]["connections"]["out"][x]
            for c in port:
                keyvalue = c
                print(x.title() + " > " + keyvalue["input_module"].title() + " (" + keyvalue["input_port"].title(
                ) + ") " + " - " + keyvalue["connection_type"].title() + " - " + keyvalue["voice"])
        print()

        print("Parameters:")
        for p in mainDict["modules"][module]["parameters"]:
            value = mainDict["modules"][module]["parameters"][p]
            print(p.title() + " = " + value)
        print()

        print("-------")


def printConnections():
    print()
    print("Printing all connections by type...")
    print()

    for ctype in connectionTypes:
        ctype_name = connectionTypes[ctype]
        print("Connection type: " + ctype_name)
        # For each module
        for module in mainDict["modules"]:
            # Get all outgoing connections:
            connections = mainDict["modules"][module]["connections"]["out"]
            for c in connections:
                connection = connections[c]
                for subc in connection:
                    # print(connection)
                    if subc["connection_type"] == ctype_name:
                        print(module.title(
                        ) + " > " + subc["input_module"].title() + " (" + subc["input_port"].title() + ") ")
        print()


def exportJSON():
    # Exports mainDict as json file
    name = filename.split(".")[0]
    filepath = getFilePath(name + '.json')
    print("Exporting dictionary as file: " + filepath)
    with open(filepath, 'w') as fp:
        json.dump(mainDict, fp)


def graphviz():
    linetypes = {
        "audio": {"style": "bold"},
        "cv": {"color": "gray"},
        "gate": {"color": "red", "style": "dashed"},
        "trigger": {"color": "orange", "style": "dashed"},
        "pitch": {"color": "blue"},
        "clock": {"color": "purple", "style": "dashed"}
    }
    print("Generating signal flow code for GraphViz.")
    print("Copy the code between the line break and paste it into https://dreampuf.github.io/GraphvizOnline/ to download a SVG / PNG chart.")
    conn = []
    total_string = ""
    print("-------------------------")
    print("digraph G{\nrankdir = LR;\nsplines = spline;\nordering=out;")
    total_string += "digraph G{\nrankdir = LR;\nsplines = polyline;\nordering=out;\n"
    for module in sorted(mainDict["modules"]):
        # Get all outgoing connections:
        outputs = mainDict["modules"][module]["connections"]["out"]
        for out in sorted(outputs):
            out_formatted = "_" + re.sub('[^A-Za-z0-9]+', '', out)
            connections = outputs[out]
            for c in connections:
                line_style_array = []
                graphviz_parameters = [
                    "color", "weight", "style", "arrowtail", "dir"]
                for param in graphviz_parameters:
                    if param in c:
                        line_style_array.append(param + "=" + c[param])
                    elif param in linetypes[c["connection_type"]]:
                        line_style_array.append(
                            param + "=" + linetypes[c["connection_type"]][param])
                if len(line_style_array) > 0:
                    line_style = "[" + ', '.join(line_style_array) + "]"
                else:
                    line_style = ""
                in_formatted = "_" + \
                    re.sub('[^A-Za-z0-9]+', '', c["input_port"])
                connection_line = module.replace(" ", "") + ":" + out_formatted + ":e  -> " + \
                    c["input_module"].replace(
                        " ", "") + ":" + in_formatted + ":w " + line_style
                conn.append([c["input_port"], connection_line])

        # If there is a template for the module, use it to render the module
        # Also validate the connections and parameters
        templates_dir = os.path.dirname(os.path.realpath(__file__)) + "/Modules"
        template_file = templates_dir + "/" + re.sub(r" .+$", "", module).upper()
        if os.path.isfile(template_file):
            lines = (line.rstrip('\n') for line in open(template_file))
            line = next(lines)
            line_nr = 1
            if line != "ports:":
                print("ERROR parsing template " + template_file + " (line " + str(line_nr) + ")"
                      + ": expected 'ports:'")
                sys.exit(1)
            line = next(lines)
            line_nr += 1
            ports = []
            supported_params = {}
            lambdas = {}
            port_re = re.compile(r"^ *- *([^ ]+) *$")
            while line != "---":
                m = port_re.search(line)
                if m:
                    ports.append(m.group(1))
                elif line == "params:":
                    line = next(lines)
                    line_nr += 1
                    break
                else:
                    print("ERROR parsing template " + template_file + " (line " + str(line_nr) + ")"
                          + ": expected a port definition or 'params:' or '---'")
                    sys.exit(1)
                line = next(lines)
                line_nr += 1
            param_re = re.compile(r"^ *([^ :]+) *: */([^/]+)/ *$")
            while line != "---":
                m = param_re.search(line)
                if m:
                    supported_params[m.group(1)] = re.compile(m.group(2))
                elif line == "lambdas:":
                    line = next(lines)
                    line_nr += 1
                    break
                else:
                    print("ERROR parsing template " + template_file + " (line " + str(line_nr) + ")"
                          + ": expected a parameter definition or 'lambdas:' or '---'")
                    sys.exit(1)
                line = next(lines)
                line_nr += 1
            lambda_re = re.compile(r"^ *([^ :]+) *: *(.+)$")
            while line != "---":
                m = lambda_re.search(line)
                if m:
                    if m.group(2) == '|':
                        lambda_def = ''
                        line = next(lines)
                        line_nr += 1
                        indent = re.sub('^( +)[^ ].*$', '\\1', line)
                        while line.startswith(indent):
                            lambda_def += (line[len(indent):] + '\n')
                            line = next(lines)
                            line_nr += 1
                    else:
                        lambda_def = m.group(2)
                        line = next(lines)
                        line_nr += 1
                    lambdas[m.group(1)] = (lambda d: lambda *argv: re.sub(template_re, replace_in_template({'argv': argv}), d))(lambda_def)
                else:
                    print("ERROR parsing template " + template_file + " (line " + str(line_nr) + ")"
                          + ": expected a lambda definition or '---'")
                    sys.exit(1)
            inputs = mainDict["modules"][module]["connections"]["in"]
            for inp in inputs:
                inp = re.sub('[^A-Za-z0-9]+', '', inp)
                if not inp in ports:
                    print("ERROR: port '" + inp + "' is not defined in template " + template_file)
                    sys.exit(1)
            for out in outputs:
                out = re.sub('[^A-Za-z0-9]+', '', out)
                if not out in ports:
                    print("ERROR: port '" + out + "' is not defined in template " + template_file)
                    sys.exit(1)
            params = mainDict["modules"][module]["parameters"]
            for param in params:
                if not param in supported_params:
                    print("ERROR: parameter '" + param + "' is not defined in template " + template_file)
                    sys.exit(1)
                param_value = params[param]
                if not re.match(supported_params[param], param_value):
                    print("ERROR: invalid parameter '" + param + " = " + param_value
                          + "' (parameter '" + param + "' defined in " + template_file + ")")
                    sys.exit(1)
            for param in supported_params:
                if not param in params:
                    params[param] = None
            template = "\n".join(lines)
            template_re = re.compile(r"{{([^ /#}]+)}}|{{#([^ #}]+)}}(.+?){{/\2}}|{%(.+?)%}", re.DOTALL)
            def replace_in_template(ctxt=None):
                ctxt = ctxt or {}
                ctxt = ctxt.copy()
                ctxt.update(params)
                ctxt.update(lambdas)
                def fn(match):
                    tag = match.group(1) or match.group(2)
                    if match.group(1):
                        if tag == "curdir":
                            return templates_dir
                        elif tag in params:
                            return params[tag]
                        elif tag in supported_params:
                            return ""
                        else:
                            print("ERROR parsing template " + template_file + ": can not render {{" + tag + "}}: "
                                  + "parameter '" + tag + "' not defined")
                            sys.exit(1)
                    elif match.group(3):
                        content = match.group(3)
                        content = re.sub(template_re, replace_in_template(), content)
                        if tag == "render_svg":
                            tmp_file = tempfile.NamedTemporaryFile('w', suffix='.svg', delete=False)
                            tmp_file.write(content)
                            tmp_file.close()
                            # Convert SVG to PNG
                            png_file_name = re.sub('svg$', 'png', tmp_file.name)
                            cmd = ['convert', tmp_file.name, png_file_name]
                            if debugMode:
                                print('Running ImageMagick: ' + str(cmd))
                            proc = subprocess.Popen(cmd, cwd=templates_dir)
                            proc.wait()
                            if proc.returncode == 0:
                                return png_file_name
                            else:
                                print("ERROR rendering template " + template_file + ": SVG could not be rendered:\n\n" + content)
                                sys.exit(1)
                        elif tag in lambdas:
                            return lambdas[tag](content)
                        else:
                            print("ERROR parsing template " + template_file + ": can not render {{#" + tag + "}}: "
                                  + "function '" + tag + "' not defined")
                            sys.exit(1)
                    else:
                        return eval(match.group(4), ctxt)
                return fn
            final_box = module.replace(" ", "") + "[" + re.sub(template_re, replace_in_template(), template) + "]"

        else:
            # Get all outgoing connections:
            module_outputs = ""
            out_count = 0
            for out in sorted(outputs):
                out_count += 1
                out_formatted = "_" + re.sub('[^A-Za-z0-9]+', '', out)
                module_outputs += "<" + out_formatted + "> " + out.upper()
                if out_count < len(outputs.keys()):
                    module_outputs += " | "

            # Get all incoming connections:
            inputs = mainDict["modules"][module]["connections"]["in"]
            module_inputs = ""
            in_count = 0
            for inp in sorted(inputs):
                inp_formatted = "_" + re.sub('[^A-Za-z0-9]+', '', inp)
                in_count += 1
                module_inputs += "<" + inp_formatted + "> " + inp.upper()
                if in_count < len(inputs.keys()):
                    module_inputs += " | "

            # Get all parameters:
            params = mainDict["modules"][module]["parameters"]
            module_params = ""
            param_count = 0
            for par in sorted(params):
                param_count += 1
                module_params += par.title() + " = " + params[par]
                if param_count < len(params.keys()):
                    module_params += r'\n'

            # If module contains parameters
            if module_params != "":
                # Add them below module name
                middle = "{{" + module.upper() + "}|{" + module_params + "}}"
            else:
                # Otherwise just display module name
                middle = module.upper()

            final_box = module.replace(
                " ", "") + "[label=\"{ {" + module_inputs + "}|" + middle + "| {" + module_outputs + "}}\"  shape=Mrecord]"

        print(final_box)
        total_string += final_box + "; "

    # Print Connections
    for c in sorted(conn):
        print(c[1])
        total_string += c[1] + "; "

    if len(mainDict["comments"]) != 0:
        format_comments = ""
        comments_count = 0
        for comment in mainDict["comments"]:
            comments_count += 1
            format_comments += "{" + comment + "}"
            if comments_count < len(mainDict["comments"]):
                format_comments += "|"
        format_comments = "comments[label=<{{{<b>PATCH COMMENTS</b>}|" + format_comments + "}}>  shape=Mrecord]"
        print(format_comments)

    print("}")
    total_string += "}"

    print("-------------------------")
    print()
    return total_string


def printDict():
    global mainDict
    for key in mainDict["modules"]:
        print(key.title() + ": " + str(mainDict["modules"][key]))


if __name__ == "__main__":
    initial_print()
    parseFile(filename)
    askCommand()
