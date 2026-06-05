# app/services/ai_assistant_service/tools/gemini_builder.py
"""
Xây dựng Gemini FunctionDeclaration objects từ tool definitions.
"""
import google.generativeai as genai


def _build_gemini_tools(available_tool_defs: list[dict]) -> list:
    """Build Gemini FunctionDeclaration objects from tool definitions."""
    function_declarations = []
    for td in available_tool_defs:
        # Build properties schema supporting string, integer, number, and array
        properties = {}
        for k, v in td["parameters"].get("properties", {}).items():
            param_type = v.get("type", "string")
            if param_type == "array":
                properties[k] = genai.protos.Schema(
                    type=genai.protos.Type.ARRAY,
                    description=v.get("description", ""),
                    items=genai.protos.Schema(type=genai.protos.Type.STRING)
                )
            else:
                properties[k] = genai.protos.Schema(
                    type=genai.protos.Type.STRING if param_type == "string" else
                         genai.protos.Type.INTEGER if param_type == "integer" else
                         genai.protos.Type.NUMBER if param_type == "number" else
                         genai.protos.Type.STRING,
                    description=v.get("description", "")
                )

        decl = genai.protos.FunctionDeclaration(
            name=td["name"],
            description=td["description"],
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties=properties,
                required=td["parameters"].get("required", [])
            )
        )
        function_declarations.append(decl)

    if not function_declarations:
        return []

    return [genai.protos.Tool(function_declarations=function_declarations)]
