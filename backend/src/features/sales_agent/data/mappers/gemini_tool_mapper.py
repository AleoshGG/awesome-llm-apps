from google.genai import types

from src.features.sales_agent.domain.entities.tool_definition_entity import ToolDefinition


def to_gemini_tools(definitions: list[ToolDefinition]) -> list[types.Tool]:
    if not definitions:
        return []
    return [types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name=definition.name,
            description=definition.description,
            parameters_json_schema=definition.parameters,
            behavior=types.Behavior.NON_BLOCKING,
        )
        for definition in definitions
    ])]
