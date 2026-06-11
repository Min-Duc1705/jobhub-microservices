using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace NotificationService.Models.Response;

public class AssistantMessageDto
{
    [JsonPropertyName("role")]
    public string Role { get; set; } = string.Empty; // "user" | "model"

    [JsonPropertyName("content")]
    public string Content { get; set; } = string.Empty;
}

public class AssistantChatRequest
{
    [JsonPropertyName("message")]
    public string Message { get; set; } = string.Empty;

    [JsonPropertyName("image_base64")]
    public string? ImageBase64 { get; set; }

    [JsonPropertyName("file_content")]
    public string? FileContent { get; set; }

    [JsonPropertyName("conversation_history")]
    public List<AssistantMessageDto> ConversationHistory { get; set; } = new();
}

public class ActionItemDto
{
    [JsonPropertyName("action_type")]
    public string ActionType { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("data")]
    public object? Data { get; set; }

    [JsonPropertyName("requires_confirmation")]
    public bool RequiresConfirmation { get; set; }

    [JsonPropertyName("tool_name")]
    public string? ToolName { get; set; }
}

public class AssistantChatResponse
{
    [JsonPropertyName("reply")]
    public string Reply { get; set; } = string.Empty;

    [JsonPropertyName("actions_taken")]
    public List<ActionItemDto> ActionsTaken { get; set; } = new();

    [JsonPropertyName("pending_action")]
    public ActionItemDto? PendingAction { get; set; }

    [JsonPropertyName("suggestions")]
    public List<string> Suggestions { get; set; } = new();

    [JsonPropertyName("error")]
    public string? Error { get; set; }
}
