import json
import networkx as nx
from typing import Optional, Union, Dict, Any, List, Set, Generic, TypeVar, Iterable, Tuple
import datetime
from enum import Enum
from dataclasses import dataclass, field
from itertools import chain
import os
import networkx as nx

def compare_graphs(graph1: nx.DiGraph, graph2: nx.DiGraph) -> Dict[str, Any]:
    """Compare two NetworkX graphs and return the differences."""
    
    # Node differences
    nodes_g1 = set(graph1.nodes())
    nodes_g2 = set(graph2.nodes())
    
    # Edge differences
    edges_g1 = set(graph1.edges())
    edges_g2 = set(graph2.edges())
    
    # Node attribute differences for common nodes
    common_nodes = nodes_g1 & nodes_g2
    node_attr_diffs = {}
    
    for node in common_nodes:
        attrs_g1 = graph1.nodes[node]
        attrs_g2 = graph2.nodes[node]
        
        if attrs_g1 != attrs_g2:
            node_attr_diffs[node] = {
                'graph1': attrs_g1,
                'graph2': attrs_g2
            }
    
    # Edge attribute differences for common edges
    common_edges = edges_g1 & edges_g2
    edge_attr_diffs = {}
    
    for edge in common_edges:
        attrs_g1 = graph1.edges[edge]
        attrs_g2 = graph2.edges[edge]
        
        if attrs_g1 != attrs_g2:
            edge_attr_diffs[edge] = {
                'graph1': attrs_g1,
                'graph2': attrs_g2
            }
    
    return {
        'nodes': {
            'only_in_graph1': nodes_g1 - nodes_g2,
            'only_in_graph2': nodes_g2 - nodes_g1,
            'common': common_nodes,
            'attribute_differences': node_attr_diffs
        },
        'edges': {
            'only_in_graph1': edges_g1 - edges_g2,
            'only_in_graph2': edges_g2 - edges_g1,
            'common': common_edges,
            'attribute_differences': edge_attr_diffs
        }
    }

def print_graph_diff(diff: Dict[str, Any]):
    """Pretty print graph differences."""
    print("=== GRAPH COMPARISON ===")
    
    # Node differences
    if diff['nodes']['only_in_graph1']:
        print(f"\nNodes only in Graph 1: {diff['nodes']['only_in_graph1']}")
    
    if diff['nodes']['only_in_graph2']:
        print(f"\nNodes only in Graph 2: {diff['nodes']['only_in_graph2']}")
    
    if diff['nodes']['attribute_differences']:
        print(f"\nNodes with different attributes:")
        for node, attrs in diff['nodes']['attribute_differences'].items():
            print(f"  {node}:")
            print(f"    Graph 1: {attrs['graph1']}")
            print(f"    Graph 2: {attrs['graph2']}")
    
    # Edge differences
    if diff['edges']['only_in_graph1']:
        print(f"\nEdges only in Graph 1: {diff['edges']['only_in_graph1']}")
    
    if diff['edges']['only_in_graph2']:
        print(f"\nEdges only in Graph 2: {diff['edges']['only_in_graph2']}")
    
    if diff['edges']['attribute_differences']:
        print(f"\nEdges with different attributes:")
        for edge, attrs in diff['edges']['attribute_differences'].items():
            print(f"  {edge}:")
            print(f"    Graph 1: {attrs['graph1']}")
            print(f"    Graph 2: {attrs['graph2']}")
    
    if (not diff['nodes']['only_in_graph1'] and 
        not diff['nodes']['only_in_graph2'] and 
        not diff['edges']['only_in_graph1'] and 
        not diff['edges']['only_in_graph2'] and
        not diff['nodes']['attribute_differences'] and
        not diff['edges']['attribute_differences']):
        print("\nGraphs are identical!")



# String helper method to convert forms of strings between each other
import re
def normalize_string(s: str) -> str:
    # 1. split apart camelCase
    s = re.sub(r'(?<!^)(?<!\s)(?=[A-Z])', '_', s)
    # 2. split apart snake_case and skewer-case
    s = re.sub(r'[-_]', ' ', s)
    # 3. select only alphanumeric characters and spaces
    s = re.sub(r'[^a-zA-Z0-9 ]', '', s)
    # 4. lowercase
    s = s.lower().strip()
    return s

def to_enum_name(name: str) -> str:
    """Convert a string to a valid Python enum name."""
    normalized = normalize_string(name)
    return re.sub(r'\s+', '_', normalized).upper()

def to_class_name(name: str) -> str:
    """Convert a string to a valid Python class name."""
    normalized = normalize_string(name).title()
    return re.sub(r'\s+', '', normalized)

def to_snake_case(name: str) -> str:
    """Convert a string to a snake_case."""
    normalized = normalize_string(name)
    return re.sub(r'\s+', '_', normalized)

def to_var_name(name: str) -> str:
    """Convert a string to a valid Python variable name."""
    snake_case = to_snake_case(name)

    # Replace reserved words with intelligible alternatives
    reserved_words = {
        'from': 'from_value',
        'to': 'to_value',
        'class': 'class_value',
        'def': 'def_value',
        'import': 'import_value',
        'as': 'as_value',
    }

    return reserved_words.get(snake_case, snake_case)

@dataclass(frozen=False)
class CompilerNode:
    """Base class for compiler nodes. Created by Swagger schemas, used to create Python classes."""
    description: Optional[str] = None
    example: Optional[str] = None

    @property
    def type_name(self) -> str:
        """Get the name of the type represented by this node. Must be usable as a Python class name."""
        pass

    @property
    def annotation_name(self) -> str:
        """Get the name of the annotation for this node. Used for type hints. Rarely different from type_name."""
        return self.type_name
    
    def compile(self) -> str:
        """Compiles the node into a Python class definition, if needed."""
        pass

    def get_to_api_method(self, instance_reference) -> str:
        """Snippet for converting this node to an API-compatible format."""
        return f"{instance_reference}.to_api()"

    def get_from_api_method(self, args) -> str:
        """Snippet for converting this node from an API-compatible format."""
        return f"{self.type_name}.from_api({args})"

@dataclass(frozen=False)
class DtypeNode(CompilerNode):
    """Represents a simple python dtype node in the compiler (bool, str, int, float, etc.)."""
    dtype: type = None

    def __post_init__(self):
        if self.dtype is None:
            raise ValueError("dtype must be specified for DtypeNode")

    @property
    def type_name(self) -> str:
        return self.dtype.__name__

    def compile(self) -> str:
        """Note: dtypes represented already exist in Python, most likely just imported"""
        return str()

    def get_to_api_method(self, instance_reference) -> str:
        return f"{instance_reference}"

    def get_from_api_method(self, args) -> str:
        return f"{self.type_name}({args})"

@dataclass(frozen=False)
class DateTimeNode(CompilerNode):
    """Represents a datetime data type in the compiler."""
    
    @property
    def type_name(self) -> str:
        return "datetime.datetime"
    
    def compile(self) -> str:
        """Note: must be imported later."""
        return str()
    
    def get_to_api_method(self, instance_reference) -> str:
        return f"{instance_reference}.isoformat()"

    def get_from_api_method(self, args) -> str:
        return f"datetime.datetime.fromisoformat({args})"

@dataclass(frozen=False)
class EnumNode(CompilerNode):
    """Represents a string enum in the compiler."""
    name: str = None
    values: Set[str] = None

    def __post_init__(self):
        if self.name is None:
            raise ValueError("name must be specified for EnumNode")
        if self.values is None:
            raise ValueError("values must be specified for EnumNode")

    @property
    def type_name(self) -> str:
        return to_class_name(self.name)

    def compile(self) -> str:
        enum_class = f"class {self.type_name}(Enum, SupportsAPI):\n"
        
        # Description Docstring
        if self.description:
            enum_class += f"    \"\"\"{self.description}\"\"\"\n"
        
        # Add enum values
        for value in self.values:
            enum_class += f"    {to_enum_name(value)} = {repr(value)}\n"
        if self.values:
            enum_class += "\n"
        
        # make to_api and from_api methods
        enum_class += f"    def to_api(self) -> str:\n"
        enum_class += f"        return self.value\n"
        enum_class += "\n"
        enum_class += f"    @classmethod\n"
        enum_class += f"    def from_api(cls, value: str) -> {self.annotation_name}:\n"
        enum_class += f"        return cls(value)\n"

        return enum_class
    
    def get_to_api_method(self, instance_reference) -> str:
        return f"{instance_reference}.to_api()"
    
    def get_from_api_method(self, args) -> str:
        return f"{self.type_name}.from_api({args})"
    
@dataclass(frozen=False)
class ObjectNode(CompilerNode):
    name: str = None
    properties: Dict[str, CompilerNode] = None

    def __post_init__(self):
        if self.name is None:
            raise ValueError("name must be specified for ObjectNode")
        if self.properties is None:
            raise ValueError("properties must be specified for ObjectNode")

    @property
    def type_name(self) -> str:
        return to_class_name(self.name)

    @property
    def is_useful(self) -> bool:
        return len(self.properties) > 0

    def compile(self) -> str:
        obj_class  = f"@dataclass(frozen=True)\n"
        obj_class += f"class {self.type_name}(SupportsAPI):\n"

        # Docstring
        obj_class += f"    \"\"\""
        if self.description:
            obj_class += f"{self.description}\n\n"
        else:
            obj_class += "\n"
        
        if self.properties:
            obj_class += f"    Attributes:\n"
            for name, prop in self.properties.items():
                obj_class += f"        {to_var_name(name)}: {prop.description or prop.annotation_name}\n"
        
        obj_class += f"    \"\"\"\n\n"

        # Add properties
        for name, prop in self.properties.items():
            obj_class += f"    {to_var_name(name)}: {prop.annotation_name}\n"
        obj_class += "\n"

        # Add to_api method
        obj_class += f"    def to_api(self) -> Dict[str, Any]:\n"
        obj_class += f"        api_dict = dict()\n"
        for name, prop in self.properties.items():
            obj_class += f"        api_dict['{name}'] = {prop.get_to_api_method(f'self.{to_var_name(name)}')}\n"
        obj_class += f"        return api_dict\n"
        obj_class += "\n"

        # Add from_api method
        obj_class += f"    @classmethod\n"
        obj_class += f"    def from_api(cls, data: Dict[str, Any]) -> {self.annotation_name}:\n"
        obj_class += f"        return cls(\n"
        for name, prop in self.properties.items():
            obj_class += f"            {to_var_name(name)}={prop.get_from_api_method(f'data.get({chr(34)}{name}{chr(34)}, None)')},\n"
        obj_class += f"        )\n"

        return obj_class
    
    def get_to_api_method(self, instance_reference) -> str:
        return f"{instance_reference}.to_api()"
    
    def get_from_api_method(self, args) -> str:
        return f"{self.type_name}.from_api({args})"

@dataclass(frozen=False)
class ArrayNode(CompilerNode):
    """Represents a typed array in the compiler."""
    item_type: CompilerNode = None

    def __post_init__(self):
        if self.item_type is None:
            raise ValueError("item_type must be specified for ArrayNode")

    @property
    def type_name(self) -> str:
        return f"list"
    
    @property
    def annotation_name(self) -> str:
        return f"List[{self.item_type.annotation_name}]"
    
    def compile(self) -> str:
        """Noop"""
        return str()
    
    def get_to_api_method(self, instance_reference) -> str:
        # To convert an array to API format, we need to convert each item to its API format
        return f"[{self.item_type.get_to_api_method(f'item')} for item in {instance_reference}]"
    
    def get_from_api_method(self, args):
        # Create a list comprehension of the from api methods
        # Assumes that args is a list of items
        return f"[{self.item_type.get_from_api_method(f'item')} for item in {args}]"
    
@dataclass(frozen=False)
class OptionalNode(CompilerNode):
    """Represents an optional type in the compiler."""
    item_type: CompilerNode = None

    def __post_init__(self):
        if self.item_type is None:
            raise ValueError("item_type must be specified for OptionalNode")

    @property
    def type_name(self) -> str:
        return self.item_type.type_name
    
    @property
    def annotation_name(self) -> str:
        return f"Optional[{self.item_type.annotation_name}]"
    
    def compile(self) -> str:
        """Noop"""
        return str()
    
    def get_to_api_method(self, instance_reference) -> str:
        return f"{self.item_type.get_to_api_method(instance_reference)} if {instance_reference} is not None else None"
    
    def get_from_api_method(self, args):
        return f"{self.item_type.get_from_api_method(args)} if {args} is not None else None"


def create_dependency_graph(swagger_schema: dict, patterns_to_ignore=[r"^Link$", r"^PaginatedData\."]) -> nx.DiGraph:
    """Creates a graph representation of swagger schema nodes, with edges based on $ref links
    Nodes are either base nodes, with no properties, or object nodes with named properties.

    Object nodes are represented as basic nodes with named edges to their properties.

    Basic nodes are simple dictionaries.

    To resolve $ref links, we need to look up the referenced schema in the swagger document and create a new node for it if it doesn't already exist.
    However, we (luckily) note that schemas are not nested
    """

    graph = nx.DiGraph()

    # Idea: as we go through the properties, if there is an unresolved $ref, we can blindly make a link to the referenced node
    # and later the node will be populated

    def parse_schema(name: str, schema: dict) -> Tuple[str, CompilerNode]:
        # adds any parsed node to the graph, creating necessary links
        # objects must know their name for compilation, unused otherwise
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            print(f"Found $ref in schema {name}: {schema['$ref']} -> {ref_name}")
            if ref_name in graph:
                node = graph.nodes[ref_name]["node"]
            else:
                node = ObjectNode(name=ref_name, description=schema.get("description", None), example=schema.get("example", None), properties={})
                graph.add_node(ref_name, node=node, properties={})
            return ref_name, node

        # Basic nodes
        if schema["type"] == "integer":
            node = DtypeNode(dtype=int, description=schema.get("description", None), example=schema.get("example", None))
            graph.add_node(name, node=node)
        elif schema["type"] == "number":
            node = DtypeNode(dtype=float, description=schema.get("description", None), example=schema.get("example", None))
            graph.add_node(name, node=node)
        elif schema["type"] == "boolean":
            node = DtypeNode(dtype=bool, description=schema.get("description", None), example=schema.get("example", None))
            graph.add_node(name, node=node)
        elif schema["type"] == "array":
            pname, predecessor = parse_schema(f"{name}_arrayitem", schema.get("items", {}))
            node = ArrayNode(item_type=predecessor)
            graph.add_node(name, node=node)
            graph.add_edge(pname, name)
        elif schema["type"] == "string":
            if "enum" in schema:
                node = EnumNode(name=name, values=schema["enum"])
                graph.add_node(name, node=node)
            elif schema.get("format", '') == 'date-time':
                node = DateTimeNode(description=schema.get("description", None), example=schema.get("example", None))
                graph.add_node(name, node=node)
            else:
                node = DtypeNode(dtype=str, description=schema.get("description", None), example=schema.get("example", None))
                graph.add_node(name, node=node)
        elif schema["type"] == "object":
            # Object nodes - we cannot fully resolve properties, so use the graph to store WIP properties
            node = ObjectNode(name=name, description=schema.get("description", None), example=schema.get("example", None), properties={})
            graph.add_node(name, node=node, properties={})

            for prop_name, prop_schema in schema.get("properties", {}).items():
                prop_node_name, prop_node = parse_schema(f"{name}_{to_var_name(prop_name)}", prop_schema)
                print(f"Prop {prop_name} ({prop_node_name}): {type(prop_node)}")
                graph.nodes[name]["properties"][to_var_name(prop_name)] = prop_node_name
                graph.add_edge(prop_node_name, name, name=prop_name)

        return name, node

    
    # Populate basic nodes
    for name, schema in swagger_schema.items():
        parse_schema(name, schema)

    # Remove unwanted nodes
    for node_name, node_data in list(graph.nodes(data=True)):
        node = node_data["node"]
        matches = any(re.match(pattern, node_name) for pattern in patterns_to_ignore)

        if not matches: continue

        # First, remove all nodes that reference this node
        for neighbor_name in list(graph.neighbors(node_name)):
            neighbor_data = graph.nodes[neighbor_name]
            if isinstance(neighbor_data["node"], ObjectNode):
                neighbor_node = neighbor_data["node"]

                # Prop
                for prop_name, prop_node_name in neighbor_data["properties"].items():
                    if prop_node_name == node_name:
                        del neighbor_data["properties"][prop_name]
                        break

                # Edge
                graph.remove_edge(node_name, neighbor_name)
        graph.remove_node(node_name)

    # Remove "useless" nodes, topo order
    # An object node is useless if it has no predecessors (i.e. no properties)
    # Enums are useless if the have no values
    for node_name in list(nx.topological_sort(graph)):
        node = graph.nodes[node_name]["node"]
        is_useful = True
        if isinstance(node, ObjectNode):
            is_useful = len(list(graph.predecessors(node_name))) > 0
        elif isinstance(node, EnumNode):
            is_useful = len(node.values) > 0
        if not is_useful:
            graph.remove_node(node_name)
        
    # Finalize properties, topo order
    for node_name in nx.topological_sort(graph):
        node = graph.nodes[node_name]["node"]
        
        #  Incoming edges
        if isinstance(node, ObjectNode):
            for prop_node in graph.predecessors(node_name):
                prop_name = graph.get_edge_data(prop_node, node_name)['name']
                prop_cnode = graph.nodes[prop_node]["node"]
                print(f"Adding property {prop_name} to {node_name} (type: {prop_cnode})")

                node.properties[prop_name] = prop_cnode

        
    
    return graph

if __name__ == "__main__":
    import json
    with open("swagger.json", "r") as f:
        swagger = json.load(f)


    raw_graph = create_dependency_graph(swagger.get("components", {}).get("schemas", {}))

    compile_list = []
    for node_name in nx.topological_sort(raw_graph):
        node_data = raw_graph.nodes[node_name]
        node = node_data["node"]
        if isinstance(node, CompilerNode):
            compile_list.append(node)
    
    # Compile all nodes into Python classes
    os.makedirs("./textverified/generated/", exist_ok=True)
    with open("./textverified/generated/generated_enums.py", "w") as f:
        f.write("""
\"\"\"
Generated enums and dataclasses from Swagger schema
This file is auto-generated. Do not edit manually.
\"\"\"
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Optional, Dict, List, Any
import datetime

class SupportsAPI(Protocol):
    def to_api(self) -> Any:
        \"\"\"Convert this object to an API-compatible format.\"\"\"
        ...
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'SupportsAPI':
        \"\"\"Create an instance from API data.\"\"\"
        ...

        """.strip())
        f.write("\n\n")
        for node in compile_list:
            compiled_code = node.compile()
            if compiled_code.strip():
                f.write(compiled_code)
                f.write("\n\n")
    
