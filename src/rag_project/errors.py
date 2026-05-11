class RagProjectError(Exception):
    """Base exception for user-facing project errors."""


class ExternalServiceError(RagProjectError):
    """Raised when an upstream model service is unavailable or misconfigured."""


def ensure_dashscope_api_key(api_key: str | None) -> None:
    if api_key:
        return
    raise ExternalServiceError("请先设置 DASHSCOPE_API_KEY 环境变量。")


def wrap_external_error(exc: Exception, action: str) -> ExternalServiceError:
    message = str(exc)

    if "Arrearage" in message:
        return ExternalServiceError(
            f"DashScope 账户当前处于欠费或不可用状态，暂时无法{action}。"
            "请先登录阿里云百炼 / Model Studio 检查账单、余额或服务状态后重试。"
        )

    if "DASHSCOPE_API_KEY" in message or "api key" in message.lower():
        return ExternalServiceError("DashScope API Key 无效或未配置，请检查 DASHSCOPE_API_KEY。")

    return ExternalServiceError(f"调用 DashScope 服务时无法{action}：{message}")