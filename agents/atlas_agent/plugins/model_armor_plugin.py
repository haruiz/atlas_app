
import logging
import os
from typing import Any


from google.adk import runners
from google.adk.agents import invocation_context, llm_agent
from google.adk.events import event
from google.adk.models import llm_request, llm_response
from google.adk.plugins import base_plugin
from google.adk.tools import base_tool, tool_context
from google.api_core.client_options import ClientOptions
from google.cloud import modelarmor_v1
from google.cloud.modelarmor_v1 import RaiFilterResult
from google.genai import types




# Util function defined here to avoid extra dependency files
def parse_model_armor_response(
        response: (
                modelarmor_v1.SanitizeUserPromptResponse
                | modelarmor_v1.SanitizeModelResponseResponse
        ),
) -> list[tuple[str, Any]]:
    """Parses the Model Armor response."""
    # TODO: Make the filter match more robust.
    matched_filters = []

    if response is None:
        return matched_filters

    # Navigate to filter_results
    try:
        filter_results = dict(response.sanitization_result.filter_results)
    except (AttributeError, TypeError):
        return matched_filters

    # Mapping of filter names to their corresponding result attribute names
    filter_attr_mapping = {
        'csam': 'csam_filter_filter_result',
        'malicious_uris': 'malicious_uri_filter_result',
        'pi_and_jailbreak': 'pi_and_jailbreak_filter_result',
        'rai': 'rai_filter_result',
        'sdp': 'sdp_filter_result',
        'virus_scan': 'virus_scan_filter_result'
    }

    for filter_name, filter_obj in filter_results.items():
        # Get the appropriate attribute name for this filter
        attr_name = filter_attr_mapping.get(filter_name)

        if not attr_name:
            # Try to construct the attribute name if not in mapping
            if filter_name == 'malicious_uris':
                attr_name = 'malicious_uri_filter_result'
            else:
                attr_name = f'{filter_name}_filter_result'

        # Get the actual filter result
        if hasattr(filter_obj, attr_name):
            filter_result = getattr(filter_obj, attr_name)

            # Special handling for SDP (has inspect_result wrapper)
            if filter_name == 'sdp' and hasattr(filter_result, 'inspect_result'):
                if hasattr(filter_result.inspect_result, 'match_state'):
                    if filter_result.inspect_result.match_state.name == 'MATCH_FOUND':
                        matched_filters.append(('sdp', filter_result.inspect_result))

            # Special handling for RAI (has subcategories)
            elif filter_name == 'rai':
                # Check main RAI match state
                if hasattr(filter_result, 'match_state'):
                    if filter_result.match_state.name == 'MATCH_FOUND':
                        # Check RAI subcategories
                        filter_types = dict(filter_result.rai_filter_type_results)
                        for ftype, fsettings in filter_types.items():
                            if hasattr(fsettings, 'match_state') and fsettings.match_state.name == 'MATCH_FOUND':
                                matched_filters.append((f"rai_{ftype}", fsettings.confidence_level.name))
            else:
                if hasattr(filter_result, 'match_state'):
                    if filter_result.match_state.name == 'MATCH_FOUND':
                        matched_filters.append((filter_name, filter_result.confidence_level.name))

    return matched_filters


Event = event.Event
InMemoryRunner = runners.InMemoryRunner
InvocationContext = invocation_context.InvocationContext
CallbackContext = base_plugin.CallbackContext
ToolContext = tool_context.ToolContext
LlmAgent = llm_agent.LlmAgent
BasePlugin = base_plugin.BasePlugin
BaseTool = base_tool.BaseTool
LlmRequest = llm_request.LlmRequest
LlmResponse = llm_response.LlmResponse

_USER_PROMPT_REMOVED_MESSAGE = (
    "FAILED: Unsafe prompt detected."
)
_UNSAFE_TOOL_OUTPUT_MESSAGE = (
    "Unable to emit tool result due to unsafe outputs."
)
_MODEL_RESPONSE_REMOVED_MESSAGE = (
    "FAILED: Unsafe model response detected."
)


class ModelArmorSafetyFilterPlugin(BasePlugin):
    """Guardian plugin to run Model Armor on user prompts and model responses in ADK."""

    def __init__(
            self,
            project_id: str = os.environ.get("GOOGLE_CLOUD_PROJECT", ""),
            location_id: str = os.environ.get("GOOGLE_CLOUD_LOCATION", ""),
            template_id: str = os.environ.get("TEMPLATE_NAME", None),
    ) -> None:
        """Initializes the ModelArmorPlugin."""
        super().__init__(name="ModelArmorPlugin")
        self._project_id = project_id
        self._location_id = location_id
        if not self._location_id:
            self._location_id = "us-central1"

        assert template_id, "TEMPLATE_NAME environment variable must be set to the Model Armor template ID"

        self._template_id = template_id
        # The template_id provided is the full resource name, so use it directly if it starts with projects/
        if self._template_id.startswith("projects/"):
            self._model_armor_url = self._template_id
        else:
            self._model_armor_url = f"projects/{self._project_id}/locations/{self._location_id}/templates/{self._template_id}"

        self._client = modelarmor_v1.ModelArmorClient(
            client_options=ClientOptions(
                api_endpoint=f"modelarmor.{self._location_id}.rep.googleapis.com"
            ),
        )
        print(f"DEBUG: Initialized ModelArmorPlugin with template: {self._model_armor_url}")
        logging.info(f"Initialized ModelArmorPlugin with template: {self._model_armor_url}")

    def _sanitize_user_prompt(
            self, user_prompt: str
    ) -> modelarmor_v1.SanitizeUserPromptResponse:
        logging.info(f"Attempting to sanitize user message: {user_prompt}")
        user_prompt_data = modelarmor_v1.DataItem(text=user_prompt)

        request = modelarmor_v1.SanitizeUserPromptRequest(
            name=self._model_armor_url,
            user_prompt_data=user_prompt_data,
        )

        return self._client.sanitize_user_prompt(request=request)

    def _sanitize_model_response(
            self, model_response: str
    ) -> modelarmor_v1.SanitizeModelResponseResponse:
        logging.info(f"Attempting to sanitize model response: {model_response}")
        model_response_data = modelarmor_v1.DataItem(text=model_response)

        request = modelarmor_v1.SanitizeModelResponseRequest(
            name=self._model_armor_url,
            model_response_data=model_response_data,
        )

        return self._client.sanitize_model_response(request=request)

    def _get_model_armor_response(
            self,
            method: str,
            text: str,
    ) -> list[tuple[str, Any]]:
        """Gets the Model Armor response for the given text and method."""
        try:
            if method == "sanitizeUserPrompt":
                response = self._sanitize_user_prompt(text)
            elif method == "sanitizeModelResponse":
                response = self._sanitize_model_response(text)
            else:
                raise ValueError(f"Unsupported method: {method}")
            parsed_result = parse_model_armor_response(response)
            return parsed_result
        except Exception as e:
            logging.error(f"Error calling Model Armor: {e}")
            # Fail open or closed? For safety, typically fail closed, but for dev maybe log and proceed?
            # Let's return empty list to "fail open" if service is unreachable to avoid breaking everything
            return []

    async def on_user_message_callback(
            self,
            invocation_context: InvocationContext,
            user_message: types.Content,
    ) -> types.Content | None:
        if not user_message.parts or not user_message.parts[0].text:
            return None

        if response := self._get_model_armor_response(
                "sanitizeUserPrompt", user_message.parts[0].text
        ):
            # Set the state to false if the user prompt is unsafe and return a
            # modified user prompt. This will be consumed by the before_run_callback
            # to halt the runner and end the invocation before the user prompt is
            # sent to the model.
            invocation_context.session.state["is_user_prompt_safe"] = False
            invocation_context.session.state["user_prompt_unsafe_reason"] = str(response)

            # We return the "FAIL" message here as the user prompt modification
            # But the real short-circuit happens in before_run_callback
            return types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text=(
                            f"{_USER_PROMPT_REMOVED_MESSAGE} Reason: {response}"
                        ),
                    )
                ],
            )
        else:
            invocation_context.session.state["is_user_prompt_safe"] = True

    async def before_run_callback(
            self,
            invocation_context: InvocationContext,
    ) -> types.Content | None:
        # Consume the state set in the on_user_message_callback to determine if the
        # user prompt is safe. If not, return a modified user prompt.
        if not invocation_context.session.state.get(
                "is_user_prompt_safe", True
        ):
            reason = invocation_context.session.state.get("user_prompt_unsafe_reason", "Unknown")
            # Reset session state to true to allow the runner to proceed normally for NEXT turn
            invocation_context.session.state["is_user_prompt_safe"] = True

            # This return value triggers the "Fail Fast" - it replaces the model's response
            return types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text=f"{_USER_PROMPT_REMOVED_MESSAGE} Reason: {reason}",
                    )
                ],
            )
        return None

    async def after_model_callback(
            self,
            callback_context: CallbackContext,
            llm_response: LlmResponse,
    ) -> LlmResponse | None:
        llm_content = llm_response.content
        if not llm_content or not llm_content.parts:
            return None
        # Support for multiple parts and different types of LLM responses
        # (e.g. function calls etc.).
        model_output = "\n".join(
            [part.text or "" for part in llm_content.parts]
        ).strip()
        if not model_output:
            return None
        if response := self._get_model_armor_response(
                "sanitizeModelResponse", model_output
        ):
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part.from_text(
                            text=f"{_MODEL_RESPONSE_REMOVED_MESSAGE} Reason: {response}",
                        )
                    ],
                )
            )

    async def after_tool_callback(
            self,
            tool: BaseTool,
            tool_args: dict[str, Any],
            tool_context: ToolContext,
            result: dict[str, Any],
    ) -> dict[str, Any] | None:
        if response := self._get_model_armor_response(
                "sanitizeUserPrompt", str(result)
        ):
            return {
                "error": (
                    f"{_UNSAFE_TOOL_OUTPUT_MESSAGE}. Reason: {response}"
                )
            }