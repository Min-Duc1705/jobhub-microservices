# app/services/ai_assistant_service/tools/vertex_builder.py
"""
Xây dựng Vertex AI Tool và FunctionDeclaration objects từ tool definitions.
"""

def _build_vertex_tools(available_tool_defs: list[dict]) -> list:
    """Build Vertex AI Tool objects from tool definitions."""
    from vertexai.generative_models import Tool, FunctionDeclaration
    function_declarations = []
    
    for td in available_tool_defs:
        parameters_dict = dict(td["parameters"])
        
        # Standardize parameter type names from lowercase to uppercase for Vertex AI compatibility
        if "properties" in parameters_dict:
            properties = {}
            for k, v in parameters_dict["properties"].items():
                prop = dict(v)
                if "type" in prop:
                    prop["type"] = prop["type"].upper()
                    if prop["type"] == "ARRAY" and "items" in prop:
                        items = dict(prop["items"])
                        if "type" in items:
                            items["type"] = items["type"].upper()
                        prop["items"] = items
                properties[k] = prop
            parameters_dict["properties"] = properties
            
        if "type" in parameters_dict:
            parameters_dict["type"] = parameters_dict["type"].upper()
            
        decl = FunctionDeclaration(
            name=td["name"],
            description=td["description"],
            parameters=parameters_dict
        )
        function_declarations.append(decl)
        
    if not function_declarations:
        return []
        
    return [Tool(function_declarations=function_declarations)]
