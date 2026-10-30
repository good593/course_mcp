from fastmcp import FastMCP
from fastmcp.server.dependencies import get_context

mcp = FastMCP("Course — Prompts only")

@mcp.prompt
def get_prompt() -> str:
    return ("당신은 친절한 초등학교 선생님입니다.\n"
"사용자의 요청에 맞게 적절한 답변을 해주세요.")

@mcp.tool 
async def get_teacher_prompt() -> str:
    """
    사용 예시: get_teacher_prompt()를 사용해서 LLM 설명해줘.
    => 결과: 초등학교 선생님 말투로 LLM 설명하는 결과를 얻을 수 있음
    """
    ctx = get_context()
    response = await ctx.fastmcp.render_prompt("get_prompt")
    return "\n".join(
        msg.content.text for msg in response.messages if msg.content.type == "text"
    )

@mcp.prompt
async def explain_term_with_glossary(term: str) -> str:
    """같은 서버의 lookup_glossary 도구를 호출해 정의를 넣은 뒤, 설명을 요청하는 사용자 메시지."""
    ctx = get_context()
    tool_result = await ctx.fastmcp.call_tool(
        "lookup_glossary",
        {"term": term.strip()},
    )
    sc = tool_result.structured_content or {}
    definition = sc.get("result", "")
    if not definition and tool_result.content:
        block = tool_result.content[0]
        definition = getattr(block, "text", str(block))
    return (
        f"아래는 용어 '{term}'에 대한 glossary 정의입니다.\n\n{definition}\n\n"
        "이 정의를 바탕으로 맥락을 보태 초보자도 이해할 수 있게 짧게 설명해 줘."
    )


@mcp.resource("course://glossary/{term}")
def get_glossary_entry(term: str) -> str:
    """간단한 용어 설명(데모). 실제로는 DB·파일에서 조회할 수 있다."""
    entries = {
        "mcp": "Model Context Protocol — LLM 클라이언트와 외부 기능을 연결하는 표준.",
        "resource": "URI로 읽는 읽기 전용 데이터.",
        "tool": "스키마가 있는 실행 가능한 함수.",
    }
    key = term.strip().lower()
    return entries.get(key, f"'{term}' 항목은 아직 glossary에 없습니다.")

@mcp.tool()
async def lookup_glossary(term: str) -> str:
    """`course://glossary/{term}` 리소스를 읽어 용어 설명 문자열을 반환한다."""
    ctx = get_context()
    uri = f"course://glossary/{term.strip()}"
    result = await ctx.read_resource(uri)
    if not result.contents:
        return ""
    body = result.contents[0].content
    return body if isinstance(body, str) else body.decode("utf-8", errors="replace")



if __name__ == "__main__":
    mcp.run()
